from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('inscription/', views.inscription_etudiant, name='inscription_etudiant'),
    path('changer-mot-de-passe/', views.changer_mot_de_passe_obligatoire, name='changer_mot_de_passe_obligatoire'),
    path('dashboard/tuteur/', views.dashboard_tuteur, name='dashboard_tuteur'),
    path('dashboard/etudiant/', views.dashboard_etudiant, name='dashboard_etudiant'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    
    # Profil
    path('profil/', views.mon_profil, name='mon_profil'),
    path('profil/modifier/', views.modifier_profil, name='modifier_profil'),
    path('profil/changer-mot-de-passe/', views.changer_mot_de_passe_profil, name='changer_mot_de_passe_profil'),
    
    # URLs Tuteur
    path('tuteur/mes-seances/', views.liste_seances_tuteur, name='liste_seances_tuteur'),
    path('tuteur/creer-seance/', views.creer_seance, name='creer_seance'),
    path('tuteur/modifier-seance/<int:pk>/', views.modifier_seance, name='modifier_seance'),
    path('tuteur/supprimer-seance/<int:pk>/', views.supprimer_seance, name='supprimer_seance'),
    path('tuteur/seance/<int:pk>/inscrits/', views.voir_inscrits, name='voir_inscrits'),
    path('tuteur/exclure-etudiant/<int:pk>/', views.exclure_etudiant, name='exclure_etudiant'),
    path('tuteur/bannis/', views.liste_bannis, name='liste_bannis'),
    path('tuteur/debannir/<int:pk>/', views.debannir_etudiant, name='debannir_etudiant'),
    path('tuteur/calendrier/', views.calendrier_tuteur, name='calendrier_tuteur'),
    path('tuteur/api/seances/', views.api_seances_tuteur, name='api_seances_tuteur'),
    
    # URLs Étudiant
    path('etudiant/seances-disponibles/', views.liste_seances_etudiant, name='liste_seances_etudiant'),
    path('etudiant/inscrire/<int:pk>/', views.inscrire_seance, name='inscrire_seance'),
    path('etudiant/mes-inscriptions/', views.mes_inscriptions, name='mes_inscriptions'),
    path('etudiant/desinscrire/<int:pk>/', views.desinscrire_seance, name='desinscrire_seance'),
    path('etudiant/calendrier/', views.calendrier_etudiant, name='calendrier_etudiant'),
    path('etudiant/api/seances/', views.api_seances_etudiant, name='api_seances_etudiant'),
    
    # URLs Forum
    path('forum/', views.forum_liste, name='forum_liste'),
    path('forum/sujet/<int:pk>/', views.forum_sujet, name='forum_sujet'),
    path('forum/nouveau/', views.forum_nouveau_sujet, name='forum_nouveau_sujet'),
    path('forum/supprimer-sujet/<int:pk>/', views.forum_supprimer_sujet, name='forum_supprimer_sujet'),
    path('forum/supprimer-reponse/<int:pk>/', views.forum_supprimer_reponse, name='forum_supprimer_reponse'),

    # Messagerie privée
    path('messages/', views.messagerie_liste, name='messagerie_liste'),
    path('messages/nouveau/', views.messagerie_nouvelle, name='messagerie_nouvelle'),
    path('messages/conversation/<int:pk>/', views.messagerie_conversation_detail, name='messagerie_conversation_detail'),  

    # URLs Admin
    path('admin-custom/bannissements/', views.gestion_bannissements_admin, name='gestion_bannissements_admin'),
    path('admin-custom/debannir/<int:pk>/', views.debannir_admin, name='debannir_admin'),
    path('admin-custom/seances/', views.liste_seances_admin, name='liste_seances_admin'),
    path('admin-custom/moderation-forum/', views.moderation_forum_admin, name='moderation_forum_admin'),
]