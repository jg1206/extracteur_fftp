'''
Created on 27 févr. 2018

@author: jerome.guillaume
'''
from django.shortcuts import render
from .extracteur_ff import extract_fonction_unique, lister_codes_communes
from ff_extract_idcom.settings import BASE_DIR
from .gestion_erreur_parametre import test_formulaire
import os

def accueil(request):
    MILLESIMES = ['2016', '2015', '2014', '2013', '2012', '2011', '2009']
    CHEMIN_DEFAUT = os.path.join(BASE_DIR, 'sortie_donnees') 
    CHEMIN_CSV_TEST = os.path.join(BASE_DIR,'entree_csv','liste_idcom_test.csv')
    
    if request.method == "POST":
        print('Formulaire executé')
        print(request.POST)
        
#         champs de formulaire à remplir pour faire l'extraction'
        host = request.POST['host']
        user = request.POST['utilisateur']
        base = request.POST['base']
        password = request.POST['password']
        perimetre = request.POST['perimetre']
        chemin = request.POST['chemin']
        millesime = request.POST['annee']
        fichier_csv = request.POST['csvfile']
        liste_idcom = lister_codes_communes(fichier_csv,'idcom')
        
#         test des champs du formulaire
        errors = test_formulaire(host, user, base)
        if  len(errors) > 0 :
            return render(request, 'accueil.html', locals())
        else :
            test = extract_fonction_unique(host, base, user, password, perimetre, liste_idcom, millesime, chemin)
            if test:
                print('extraction réussie!!')
                return render(request, 'accueil.html', locals())
            else:
                print('Echec connexion')
#     return render(request, 'accueil.html', locals())
