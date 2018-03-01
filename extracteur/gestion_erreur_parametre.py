'''
Created on 28 févr. 2018

@author: jerome.guillaume

fonctions python permettant de gérer les erreurs potentielles dans la saisie des paramètres de l'application extracteur_fftp
'''
import re, subprocess

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
        return True
    else:
        return False
    

def msg_error_host(host):
    '''affectation d'un message d'erreur si hote invalide
    '''
    if error_host(host) is False:
        msg_error_host = '''L'hôte entré n'est pas de la bonne forme'''
        return msg_error_host
    return None

def error_user(user):
    if user != '':
        if re.match("^[a-z0-9_]*$",user):
            return True
    return False

def msg_error_user(user):
    if error_user(user) is False:
        msg_error_user = '''veuillez rentrer un nom d'utilisateur valide'''
        return msg_error_user
    return None
        
def check_base(base,user,host,password):
    try subprocess.run(["psql", "-c","select postgis_version()", "-U", user, "-h", host, base], check = True):
        return True
    return False

def error_base(base):
    if base != '':
        if re.match("^[a-z0-9_]*$",base):
            return True
    return False

def msg_error_base(base):
    if error_user(base) is False:
        msg_error_base = 'veuillez rentrer un nom de base de données valide'
        return msg_error_base
    else:
        msg_error_base = ''
        return msg_error_base


def error_perimetre(perimetre):
    if re.match("^[a-z0-9_]*$", perimetre):
        return True
    else:
        msg_error_perimetre = 'vous avez entré des caractères spéciaux dans votre périmètre....'
        return msg_error_perimetre



# Fonction agrégeant tous les test sur le formulaire
def test_formulaire(host, user, base):
    errors = []
    error_host = msg_error_host(host)
    error_user = msg_error_user(user)
    error_base = msg_error_base(base)
    if error_host:
        print(error_host)
        errors.append(error_host)
    if error_user:
        print(error_user)
        errors.append(error_user)
    if error_base:
        print(error_base)
        errors.append(error_base)
    return errors

    
    

