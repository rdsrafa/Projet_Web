from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Matiere, Seance, Inscription, SujetForum, ReponseForum, Conversation, Message, Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuration de l'interface admin pour le modèle User personnalisé
    """
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'telephone', 'date_naissance'),
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'email', 'telephone', 'date_naissance'),
        }),
    )


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour les matières
    """
    list_display = ['code', 'nom', 'description']
    search_fields = ['nom', 'code']
    ordering = ['nom']
    
    fieldsets = (
        ('Informations de la matière', {
            'fields': ('nom', 'code', 'description'),
        }),
    )


@admin.register(Seance)
class SeanceAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour les séances
    """
    list_display = ['titre', 'matiere', 'tuteur', 'date', 'heure_debut', 'lieu', 'places_max', 'statut', 'places_restantes']
    list_filter = ['statut', 'matiere', 'date', 'tuteur']
    search_fields = ['titre', 'tuteur__username', 'matiere__nom']
    date_hierarchy = 'date'
    ordering = ['-date', '-heure_debut']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'matiere', 'tuteur', 'statut'),
        }),
        ('Date et horaires', {
            'fields': ('date', 'heure_debut', 'heure_fin', 'lieu'),
        }),
        ('Détails', {
            'fields': ('description', 'places_max'),
        }),
    )
    
    def places_restantes(self, obj):
        return obj.places_disponibles()
    places_restantes.short_description = 'Places disponibles'


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    """
    Configuration de l'interface admin pour les inscriptions
    """
    list_display = ['etudiant', 'seance', 'statut', 'date_inscription']
    list_filter = ['statut', 'date_inscription', 'seance__matiere']
    search_fields = ['etudiant__username', 'seance__titre']
    date_hierarchy = 'date_inscription'
    ordering = ['-date_inscription']
    
    fieldsets = (
        ('Inscription', {
            'fields': ('etudiant', 'seance', 'statut'),
        }),
        ('Informations complémentaires', {
            'fields': ('commentaire',),
        }),
    )