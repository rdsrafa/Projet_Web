from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Matiere, Seance, Inscription, Sujet, Reponse, BannissementTuteur

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'date_inscription']
    list_filter = ['role', 'is_staff', 'is_active', 'date_inscription']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'telephone', 'doit_changer_mdp')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'telephone', 'email', 'first_name', 'last_name', 'doit_changer_mdp')
        }),
    )

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom']
    search_fields = ['nom', 'code']

@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    list_display = ['titre', 'matiere', 'tuteur', 'date', 'heure_debut', 'lieu', 'places_restantes', 'statut']
    list_filter = ['statut', 'matiere', 'date']
    search_fields = ['titre', 'tuteur__username', 'tuteur__first_name', 'tuteur__last_name']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('tuteur', 'matiere', 'titre', 'description')
        }),
        ('Horaires', {
            'fields': ('date', 'heure_debut', 'heure_fin', 'lieu')
        }),
        ('Paramètres', {
            'fields': ('places_max', 'statut')
        }),
    )

@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ['etudiant', 'seance', 'statut', 'date_inscription']
    list_filter = ['statut', 'date_inscription']
    search_fields = ['etudiant__username', 'etudiant__first_name', 'etudiant__last_name', 'seance__titre']
    date_hierarchy = 'date_inscription'


@admin.register(Sujet)
class SujetAdmin(admin.ModelAdmin):
    list_display = ['titre', 'matiere', 'auteur', 'nombre_reponses', 'est_resolu', 'date_creation']
    list_filter = ['matiere', 'est_resolu', 'date_creation']
    search_fields = ['titre', 'contenu', 'auteur__username']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'matiere', 'auteur', 'contenu')
        }),
        ('Statut', {
            'fields': ('est_resolu',)
        }),
    )

@admin.register(Reponse)
class ReponseAdmin(admin.ModelAdmin):
    list_display = ['sujet', 'auteur', 'date_creation']
    list_filter = ['date_creation']
    search_fields = ['contenu', 'auteur__username', 'sujet__titre']
    date_hierarchy = 'date_creation'


@admin.register(BannissementTuteur)
class BannissementTuteurAdmin(admin.ModelAdmin):
    list_display = ['etudiant', 'tuteur', 'raison', 'date_bannissement']
    list_filter = ['date_bannissement', 'tuteur']
    search_fields = ['etudiant__username', 'etudiant__first_name', 'etudiant__last_name', 'tuteur__username']
    date_hierarchy = 'date_bannissement'
    
    fieldsets = (
        ('Bannissement', {
            'fields': ('tuteur', 'etudiant', 'raison')
        }),
    )