# from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^accueil/', views.accueil, name='accueil'),
    url(r'^step/(?P<etape>[0-9]+)/', views.traitement, name='traitement'),
    url(r'^fin_traitement/', views.fin_traitement, name='fin_traitement'),
    url(r'^erreur/', views.erreur, name='erreur'),
]