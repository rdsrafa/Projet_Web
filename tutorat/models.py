from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import datetime


# ========== MODÈLE UTILISATEUR ==========

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec rôles
    """
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('tuteur', 'Tuteur'),
        ('etudiant', 'Étudiant'),
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='etudiant',
        verbose_name='Rôle'
    )
    
    telephone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name='Téléphone'
    )
    
    date_inscription = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date d\'inscription'
    )

    doit_changer_mdp = models.BooleanField(
        default=False,
        verbose_name='Doit changer le mot de passe'
    )
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_tuteur(self):
        return self.role == 'tuteur'
    
    def is_etudiant(self):
        return self.role == 'etudiant'


# ========== MODÈLE MATIÈRE ==========

class Matiere(models.Model):
    """
    Modèle représentant une matière enseignée
    """
    nom = models.CharField(max_length=100, verbose_name='Nom de la matière')
    code = models.CharField(max_length=20, unique=True, verbose_name='Code matière')
    description = models.TextField(blank=True, verbose_name='Description')
    
    class Meta:
        verbose_name = 'Matière'
        verbose_name_plural = 'Matières'
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"


# ========== MODÈLE SÉANCE ==========

class Seance(models.Model):
    """
    Modèle représentant une séance de tutorat
    """
    STATUT_CHOICES = (
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    )
    
    tuteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seances_tuteur',
        limit_choices_to={'role': 'tuteur'},
        verbose_name='Tuteur'
    )
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='seances',
        verbose_name='Matière'
    )
    
    titre = models.CharField(max_length=200, verbose_name='Titre de la séance')
    description = models.TextField(verbose_name='Description')
    
    date = models.DateField(verbose_name='Date')
    heure_debut = models.TimeField(verbose_name='Heure de début')
    heure_fin = models.TimeField(verbose_name='Heure de fin')
    
    lieu = models.CharField(max_length=100, verbose_name='Lieu')
    
    places_max = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=10,
        verbose_name='Nombre de places maximum'
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='planifiee',
        verbose_name='Statut'
    )
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Dernière modification')
    
    class Meta:
        verbose_name = 'Séance'
        verbose_name_plural = 'Séances'
        ordering = ['date', 'heure_debut']

    def actualiser_statut(self):
        """
        Met à jour automatiquement le statut selon la date/heure
        """
        if self.statut == 'annulee':
            return
        
        maintenant = timezone.now()
        date_aujourd_hui = maintenant.date()
        heure_actuelle = maintenant.time()
        
        datetime_debut = datetime.combine(self.date, self.heure_debut)
        datetime_fin = datetime.combine(self.date, self.heure_fin)
        datetime_actuel = datetime.combine(date_aujourd_hui, heure_actuelle)
        
        if datetime_actuel > datetime_fin:
            if self.statut != 'terminee':
                self.statut = 'terminee'
                self.save()
        elif datetime_debut <= datetime_actuel <= datetime_fin:
            if self.statut != 'en_cours':
                self.statut = 'en_cours'
                self.save()
        elif self.statut == 'en_cours' and datetime_actuel < datetime_debut:
            self.statut = 'planifiee'
            self.save()
    
    @property
    def statut_actuel(self):
        """
        Retourne le statut actualisé sans sauvegarder
        """
        if self.statut == 'annulee':
            return self.statut
        
        maintenant = timezone.now()
        date_aujourd_hui = maintenant.date()
        heure_actuelle = maintenant.time()
        
        datetime_debut = datetime.combine(self.date, self.heure_debut)
        datetime_fin = datetime.combine(self.date, self.heure_fin)
        datetime_actuel = datetime.combine(date_aujourd_hui, heure_actuelle)
        
        if datetime_actuel > datetime_fin:
            return 'terminee'
        elif datetime_debut <= datetime_actuel <= datetime_fin:
            return 'en_cours'
        else:
            return self.statut
    
    def __str__(self):
        return f"{self.titre} - {self.date} à {self.heure_debut}"
    
    @property
    def places_restantes(self):
        """
        Calcule le nombre de places restantes
        """
        return self.places_max - self.inscriptions.filter(statut='confirmee').count()
    
    @property
    def est_complet(self):
        """
        Vérifie si la séance est complète
        """
        return self.places_restantes <= 0


# ========== MODÈLE INSCRIPTION ==========

class Inscription(models.Model):
    """
    Modèle représentant l'inscription d'un étudiant à une séance
    """
    STATUT_CHOICES = (
        ('confirmee', 'Confirmée'),
        ('annulee', 'Annulée'),
    )
    
    etudiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        limit_choices_to={'role': 'etudiant'},
        verbose_name='Étudiant'
    )
    
    seance = models.ForeignKey(
        Seance,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name='Séance'
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='confirmee',
        verbose_name='Statut'
    )
    
    date_inscription = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'inscription')
    commentaire = models.TextField(blank=True, verbose_name='Commentaire')
    
    class Meta:
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        ordering = ['-date_inscription']
        unique_together = ['etudiant', 'seance']
    
    def actualiser_statut_selon_seance(self):
        """
        Met à jour le statut de l'inscription selon le statut de la séance
        """
        # Si la séance est annulée, annuler l'inscription
        if self.seance.statut == 'annulee' and self.statut != 'annulee':
           self.statut = 'annulee'
           self.save()
    
        # Si la séance redevient planifiée/en_cours et l'inscription était annulée automatiquement
        # (pas par l'étudiant), réactiver l'inscription
        elif self.seance.statut in ['planifiee', 'en_cours'] and self.statut == 'annulee':
            self.statut = 'confirmee'
            self.save()
    
    @property
    def statut_affichage(self):
        """
        Retourne le statut à afficher en tenant compte de la séance
        """
        # Utiliser statut_actuel au lieu de statut pour avoir le statut en temps réel
        statut_seance = self.seance.statut_actuel
    
        if statut_seance == 'annulee' or self.statut == 'annulee':
            return 'annulee'
        elif statut_seance == 'terminee':
            return 'terminee'
        else:
            return 'confirmee'

    def get_statut_affichage_display(self):
        """
        Retourne le libellé du statut à afficher
        """
        statut = self.statut_affichage
        if statut == 'confirmee':
            return 'Confirmée'
        elif statut == 'annulee':
            return 'Annulée'
        elif statut == 'terminee':
            return 'Terminée'
        return statut
    
    # ========== MODÈLE SUJET DE FORUM ==========

class Sujet(models.Model):
    """
    Modèle représentant un sujet de discussion dans le forum
    """
    titre = models.CharField(max_length=200, verbose_name='Titre du sujet')
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='sujets',
        verbose_name='Matière'
    )
    
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sujets',
        verbose_name='Auteur'
    )
    
    contenu = models.TextField(verbose_name='Contenu')
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Dernière modification')
    
    est_resolu = models.BooleanField(default=False, verbose_name='Résolu')
    
    class Meta:
        verbose_name = 'Sujet'
        verbose_name_plural = 'Sujets'
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.auteur.username}"
    
    @property
    def nombre_reponses(self):
        """Retourne le nombre de réponses au sujet"""
        return self.reponses.count()


# ========== MODÈLE RÉPONSE DE FORUM ==========

class Reponse(models.Model):
    """
    Modèle représentant une réponse à un sujet du forum
    """
    sujet = models.ForeignKey(
        Sujet,
        on_delete=models.CASCADE,
        related_name='reponses',
        verbose_name='Sujet'
    )
    
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reponses',
        verbose_name='Auteur'
    )
    
    contenu = models.TextField(verbose_name='Contenu')
    
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Dernière modification')
    
    class Meta:
        verbose_name = 'Réponse'
        verbose_name_plural = 'Réponses'
        ordering = ['date_creation']
    
    def __str__(self):
        return f"Réponse de {self.auteur.username} sur {self.sujet.titre}"