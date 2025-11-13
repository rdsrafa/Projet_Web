from django.urls import path
from . import views

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('dashboard/etudiant/', views.dashboard_etudiant, name='dashboard_etudiant'),
    path('dashboard/tuteur/', views.dashboard_tuteur, name='dashboard_tuteur'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    
    # Gestion des séances
    path('seances/', views.seance_list, name='seance_list'),
    path('seance/create/', views.seance_create, name='seance_create'),
    path('seance/<int:pk>/', views.seance_detail, name='seance_detail'),
    path('seance/<int:pk>/update/', views.seance_update, name='seance_update'),
    path('seance/<int:pk>/delete/', views.seance_delete, name='seance_delete'),
    
    # Gestion des inscriptions
    path('seance/<int:seance_pk>/inscription/', views.inscription_create, name='inscription_create'),
    path('inscription/<int:pk>/delete/', views.inscription_delete, name='inscription_delete'),
    
    # Calendrier
    path('calendrier/', views.calendrier, name='calendrier'),
    path('api/seances.json', views.seances_json, name='seances_json'),
    
    # Forum
    path('forum/', views.forum_accueil, name='forum_accueil'),
    path('forum/nouveau/', views.forum_sujet_create, name='forum_sujet_create'),
    path('forum/sujet/<int:pk>/', views.forum_sujet_detail, name='forum_sujet_detail'),
    path('forum/reponse/<int:pk>/like/', views.forum_reponse_like, name='forum_reponse_like'),
    path('forum/reponse/<int:pk>/meilleure/', views.forum_reponse_meilleure, name='forum_reponse_meilleure'),
    
    # Messagerie
    path('messagerie/', views.messagerie_liste, name='messagerie_liste'),
    path('messagerie/utilisateurs/', views.messagerie_utilisateurs, name='messagerie_utilisateurs'),
    path('messagerie/conversation/<int:pk>/', views.messagerie_conversation, name='messagerie_conversation'),
    path('messagerie/nouveau/<int:user_id>/', views.messagerie_nouvelle, name='messagerie_nouvelle'),
    
    # Notifications
    path('notifications/', views.notifications_liste, name='notifications_liste'),
    path('api/notifications/count/', views.notifications_count, name='notifications_count'),
    
    # Modération (Admin)
    path('admin/moderation/', views.admin_moderation, name='admin_moderation'),
    path('admin/sujet/<int:pk>/epingler/', views.admin_sujet_epingler, name='admin_sujet_epingler'),
    path('admin/sujet/<int:pk>/supprimer/', views.admin_sujet_supprimer, name='admin_sujet_supprimer'),
    path('admin/reponse/<int:pk>/supprimer/', views.admin_reponse_supprimer, name='admin_reponse_supprimer'),
    path('admin/utilisateur/<int:pk>/toggle/', views.admin_utilisateur_toggle, name='admin_utilisateur_toggle'),
]