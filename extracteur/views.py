'''
Created on 27 févr. 2018

@author: jerome.guillaume
'''
import os
import json

from django.shortcuts import render, redirect
from django.http import HttpResponse

from .extracteur_ff import extract_fonction_unique, lister_codes_communes
from ff_extract_idcom.settings import BASE_DIR
from .gestion_erreur_parametre import test_formulaire, tentative_connexion


def accueil(request):
    errors = []
    MILLESIMES = ['2016', '2015', '2014', '2013', '2012', '2011', '2009']
    chemin = os.path.join(BASE_DIR, 'sortie_donnees') 
    fichier_csv = os.path.join(BASE_DIR,'entree_csv','liste_idcom_test.csv')
    
    if request.method == "POST":        
        # champs de formulaire à remplir pour faire l'extraction'
        host = request.POST['host']
        user = request.POST['utilisateur']
        base = request.POST['base']
        password = request.POST['password']
        perimetre = request.POST['perimetre']
        chemin = request.POST['chemin']
        millesime = request.POST['annee']
        fichier_csv = request.POST['csvfile']
        
        # Recupération des idcom et renvoie d'erreur eventuel
        liste_idcom, erreur = lister_codes_communes(fichier_csv, 'idcom')
        if erreur:
            errors.append(erreur)        
        # test des champs du formulaire
        errors += test_formulaire(host, user, base)
        # test de connexion à la base de données
        if not tentative_connexion(host, base, user, password, 5432):
            errors.append("La connexion a la base de donnée a échoué.")
        
        if  len(errors) > 0 :
            return render(request, 'accueil.html', locals())
        else :
            request.session['host'] = host
            request.session['user'] = user
            request.session['base'] = base
            request.session['password'] = password
            request.session['perimetre'] = perimetre
            request.session['chemin'] = chemin
            request.session['millesime'] = millesime
            request.session['liste_idcom'] = liste_idcom            
            return render(request, 'traitement.html', locals())            
    return render(request, 'accueil.html', locals())

def traitement(request, etape):
    if etape == '9999':
        data = {}
    elif etape == '1' :
        host = request.session['host']
        user = request.session['user'] 
        base = request.session['base']
        password = request.session['password']
        perimetre = request.session['perimetre']
        chemin = request.session['chemin']
        millesime = request.session['millesime']
        liste_idcom = request.session['liste_idcom']
        test = extract_fonction_unique(host, base, user, password, perimetre, liste_idcom, millesime, chemin)
        if test:
            print('extraction réussie!!')
            data = {'etape_suivante' : 9999}
        else:
            print('Echec connexion')
            data = {'erreur' : True}
    return HttpResponse(json.dumps(data), content_type='application/json')

def fin_traitement(request):
    return render(request, 'fin_traitement.html', locals())

def erreur(request):
    return render(request, 'erreur.html', locals())
