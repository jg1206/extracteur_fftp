'''
Created on 27 févr. 2018

@author: jerome.guillaume
'''
import os
import json

from django.shortcuts import render, redirect
from django.http import HttpResponse

from .extracteurclass import Extracteur, lister_codes_communes, test_pg_dump, test_schema_a_creer
from ff_extract_idcom.settings import BASE_DIR
from .gestion_erreur_parametre import test_formulaire, tentative_connexion, error_schema_a_creer, error_perimetre

def connexion(request):
    
    pass

def accueil(request):
    errors = []
    MILLESIMES = ['2017', '2016', '2015', '2014', '2013', '2012', '2011', '2009']
    chemin = os.path.join(BASE_DIR, 'sortie_donnees') 
    fichier_csv = os.path.join(BASE_DIR,'entree_csv','liste_idcom_test.csv')
    
#test présence de pg_dump dans le path
    if not test_pg_dump():
        msg = "Attention, la commande pg_dump n'est pas détectée ou présente dans le PATH Windows"
        return render(request, 'erreur.html', locals())
    
    if request.method == "POST":        
        # champs de formulaire à remplir pour faire l'extraction'
        host = request.POST['host']
        utilisateur = request.POST['utilisateur']
        base = request.POST['base']
        password = request.POST['password']
        perimetre = request.POST['perimetre']
        chemin = request.POST['chemin']
        millesime = request.POST['annee']
        fichier_csv = request.POST['csvfile']
        
        # Recupération des idcom et renvoi d'erreur eventuel
        liste_idcom, erreur = lister_codes_communes(fichier_csv, 'idcom')
        if erreur:
            errors.append(erreur)
        
        errors += test_formulaire(host, base, utilisateur, password, perimetre, liste_idcom, millesime, chemin)
        # test des champs du formulaire et affichage des erreurs potentielles 
        # concernant la forme de l'hôte, la base, l'utilisateur, le périmètre          
        if  len(errors) > 0 :
            return render(request, 'accueil.html', locals())
        else :
            request.session['host'] = host
            request.session['user'] = utilisateur
            request.session['base'] = base
            request.session['password'] = password
            request.session['perimetre'] = perimetre
            request.session['chemin'] = chemin
            request.session['millesime'] = millesime
            request.session['liste_idcom'] = liste_idcom            
            return render(request, 'traitement.html', locals())            
    return render(request, 'accueil.html', locals())

def traitement(request, etape):
    params = parametres(request.session)
    extracteur = Extracteur(**params)
    data = {}
    print(etape)
    if etape == '9999':
        data = {}
        #return render(request, 'fin_traitement.html', locals())
    elif etape == '1' :
        success, msg = extracteur.creation_schema_extraction()
        if success:
            print('Etape 1 réussie')
            print(msg)
            data = {'etape_suivante' : 2, 'progression' : 5, 'description': 'Creation tables vides FFTP'}
        else:
            print(msg)
            request.session['erreur'] = msg
            data = {'erreur': True}
    elif etape == '2':
        success, msg = extracteur.creation_tables_vides()
        if success:
            print('Etape 2 réussie')
            print(msg)
            data = {'etape_suivante' : 3, 'progression' : 15, 'description' : 'Insertion des données communales'}
        else:
            print(msg)
            request.session['erreur'] = msg
            data = {'erreur': True}        
    elif etape == '3':
        success, msg = extracteur.insertion_donnees()
        if success:
            print('Etape 3 réussie')
            print(msg)
            data = {'etape_suivante' : 4, 'progression' : 30, 'description' : 'Creation tables vides FFTP'}
        else:
            print(msg)
            request.session['erreur'] = msg
            data = {'erreur': True}
    elif etape == '4':
        success, msg = extracteur.dumper()
        if success:
            print('Etape 4 réussie')
            print(msg)
            data = {'etape_suivante' : 9999, 'progression' : 100, 'description' : 'Travail terminé'}
        else:
            print(msg)
            request.session['erreur'] = msg
            data = {'erreur': True}

    return HttpResponse(json.dumps(data), content_type='application/json')


def fin_traitement(request):
    params = parametres(request.session)
    return render(request, 'fin_traitement.html', locals())

def erreur(request):
    msg = "Aucun message d'erreur recupéré."
    if 'erreur' in request.session:
        msg = request.session['erreur']
    return render(request, 'erreur.html', locals())

def parametres(session):
    params = {'hote': session['host'], 
              'base': session['base'], 
              'port':'5432',
              'utilisateur': session['user'],
              'mdp': session['password'],
              'millesime': session['millesime'],
              'perimetre': session['perimetre'],
              'liste_idcom': session['liste_idcom'],
              'chemin': session['chemin']}
    return params

