'''
Created on 28 févr. 2018

@author: jerome.guillaume

fonctions python permettant de gérer les erreurs potentielles dans la saisie des paramètres de l'application extracteur_fftp
'''
import re, subprocess
from pg.pgbasics import PgOutils
import psycopg2
import os

def validate_ip(s):
    '''validation d'une adresse IP
    '''
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True

def error_host(host):
    '''validation d'un hote soit en localhost soit en adresse IPv4
    '''
    if host == 'localhost' or validate_ip(host):
        return True, 'IP Valide'
    else:
        return False, "l'adresse IP n'est pas valide"
    

def msg_error_host(host):
    '''affectation d'un message d'erreur si hote invalide
    '''
    if error_host(host) is False:
        msg_error_host = '''L'hôte entré n'est pas valide'''
        return msg_error_host
    return None

def error_user(user):
    if user != '':
        if re.match("^[a-z0-9_]*$",user):
            return True, "nom d'utilisateur ok"
    return False,"Le nom d'utilisateur contient des caractères non-autorisés"

def msg_error_user(user):
    if error_user(user) is False:
        msg_error_user = '''Le nom d'utilisateur n'est pas valide.'''
        return msg_error_user
    return None

def error_base(base):
    if base != '':
        if re.match("^[a-z0-9_]*$",base):
            return True, 'nom de base ok'
    return False, 'Le nom de base contient des caractères non-autorisés'

def msg_error_base(base):
    if error_user(base) is False:
        msg_error_base = "Le nom de la base de données n'est pas valide."
        return msg_error_base
    return None


def error_perimetre(perimetre):
    if perimetre != '':
        if re.match("^[a-z0-9_]*$",perimetre):
            return True, 'ok'
    return False, 'vous avez entré des caractères spéciaux dans votre périmètre....'
    

def error_schema_a_creer(host, base, user, password, perimetre, millesime):
    """
    permet de tester la présence du schema qui va être créé par l'application
    en fonction du nom de périmètre qui aura été entré dans le formulaire
    """
    params = {'hote':host, 'base':base, 'port':'5432','utilisateur':user,'motdepasse':password}
    pgoutils = PgOutils(**params)
    liste_schemas = pgoutils.lister_schemas()
    schema_ext = 'ff_{0}_{1}'.format(perimetre, millesime)
    if schema_ext not in liste_schemas:
        return True, 'Périmètre ok'
    return False, 'Le schéma d\'extraction ({0}) qui devrait être créé existe déjà, merci de le supprimer ou de changer le nom du périmètre...'.format(schema_ext)
    

def tentative_connexion(hote, bdd, utilisateur, mdp, port):
    '''
    Tente une connexion à la base PostgreSQL spécifiée
    '''
    try:
        conn = psycopg2.connect(host=hote, dbname=bdd, port=port, user=utilisateur, password=mdp)
        return True, 'connexion possible'
    except Exception as e:
        return False, 'La connexion a la base de donnée a échoué. Revoyez vos paramètres de connexion ou votre connexion réseau.'
    

def error_chemin(chemin):
    if not os.path.isdir(chemin):
        return False, 'Le chemin spécifié n\'est pas un répertoire valide'
    return True, 'Ok'   


# Fonction agrégeant tous les test sur le formulaire
def test_formulaire(host, base, user, password, perimetre, liste_idcom, millesime, chemin):
    errors = []
#   test forme hote
    success, msg = error_host(host)
    if not success:
        print(msg)
        errors.append(msg)
#   test forme user
    success, msg = error_user(user)
    if not success:
        print(msg)
        errors.append(msg)
#   test forme base
    success, msg = error_base(base)
    if not success:
        print(msg)
        errors.append(msg)
#   test forme perimetre
    success, msg = error_perimetre(perimetre)
    if not success:
        print(msg)
        errors.append(msg)
#    test connexion
    success, msg = tentative_connexion(host, base, user, password, 5432)
    if not success:
        print(msg)
        errors.append(msg)
    else:
    #    test schema de livraison uniquement si la tentative de connexion a fonctionné
        success, msg = error_schema_a_creer(host, base, user, password, perimetre, millesime)
        if not success:
            print(msg)
            errors.append(msg)
#    test chemin est bien un repertoire valide
    success, msg = error_chemin(chemin)
    if not success:
        print(msg)
        errors.append(msg)        
    return errors