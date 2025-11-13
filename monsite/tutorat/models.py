from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec trois types de profils
    """
    ROLE_CHOICES = (
        ('ETUDIANT', 'Étudiant'),
        ('TUTEUR', 'Tuteur'),
        ('ADMIN', 'Administrateur'),
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='ETUDIANT',
        verbose_name="Rôle"
    )
    
    telephone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Téléphone"
    )
    
    date_naissance = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de naissance"
    )
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_etudiant(self):
        return self.role == 'ETUDIANT'
    
    def is_tuteur(self):
        return self.role == 'TUTEUR'
    
    def is_admin_user(self):
        return self.role == 'ADMIN'


class Matiere(models.Model):
    """
    Modèle pour les matières du tutorat
    """
    nom = models.CharField(max_length=100, verbose_name="Nom de la matière")
    code = models.CharField(max_length=10, unique=True, verbose_name="Code")
    description = models.TextField(blank=True, verbose_name="Description")
    
    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.code} - {self.nom}"


class Seance(models.Model):
    """
    Modèle pour les séances de tutorat
    """
    STATUT_CHOICES = (
        ('PREVUE', 'Prévue'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('ANNULEE', 'Annulée'),
    )
    
    titre = models.CharField(max_length=200, verbose_name="Titre de la séance")
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='seances',
        verbose_name="Matière"
    )
    tuteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='seances_tuteur',
        limit_choices_to={'role': 'TUTEUR'},
        verbose_name="Tuteur"
    )
    date = models.DateField(verbose_name="Date")
    heure_debut = models.TimeField(verbose_name="Heure de début")
    heure_fin = models.TimeField(verbose_name="Heure de fin")
    lieu = models.CharField(max_length=200, verbose_name="Lieu")
    description = models.TextField(blank=True, verbose_name="Description")
    places_max = models.IntegerField(default=10, verbose_name="Places maximum")
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PREVUE',
        verbose_name="Statut"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Séance"
        verbose_name_plural = "Séances"
        ordering = ['-date', '-heure_debut']
    
    def __str__(self):
        return f"{self.titre} - {self.date} à {self.heure_debut}"
    
    def places_disponibles(self):
        """Retourne le nombre de places disponibles"""
        places_occupees = self.inscriptions.filter(statut='CONFIRMEE').count()
        return self.places_max - places_occupees
    
    def est_complete(self):
        """Vérifie si la séance est complète"""
        return self.places_disponibles() <= 0
    
    def peut_s_inscrire(self, etudiant):
        """Vérifie si un étudiant peut s'inscrire"""
        if self.est_complete():
            return False
        if self.inscriptions.filter(etudiant=etudiant, statut='CONFIRMEE').exists():
            return False
        return True
    


class Inscription(models.Model):
    """
    Modèle pour les inscriptions aux séances
    """
    STATUT_CHOICES = (
        ('EN_ATTENTE', 'En attente'),
        ('CONFIRMEE', 'Confirmée'),
        ('ANNULEE', 'Annulée'),
    )
    
    etudiant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        limit_choices_to={'role': 'ETUDIANT'},
        verbose_name="Étudiant"
    )
    seance = models.ForeignKey(
        Seance,
        on_delete=models.CASCADE,
        related_name='inscriptions',
        verbose_name="Séance"
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='CONFIRMEE',
        verbose_name="Statut"
    )
    date_inscription = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    commentaire = models.TextField(blank=True, verbose_name="Commentaire")
    
    class Meta:
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"
        unique_together = ['etudiant', 'seance']
        ordering = ['-date_inscription']
    
    def __str__(self):
        return f"{self.etudiant.username} - {self.seance.titre}"


class SujetForum(models.Model):
    """
    Modèle pour les sujets du forum
    """
    titre = models.CharField(max_length=200, verbose_name="Titre")
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='sujets_forum',
        verbose_name="Matière"
    )
    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sujets_crees',
        verbose_name="Auteur"
    )
    contenu = models.TextField(verbose_name="Contenu")
    epingle = models.BooleanField(default=False, verbose_name="Épinglé")
    resolu = models.BooleanField(default=False, verbose_name="Résolu")
    vues = models.IntegerField(default=0, verbose_name="Nombre de vues")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Sujet du forum"
        verbose_name_plural = "Sujets du forum"
        ordering = ['-epingle', '-updated_at']
    
    def __str__(self):
        return self.titre
    
    def nombre_reponses(self):
        return self.reponses.count()
    
    def derniere_reponse(self):
        return self.reponses.order_by('-created_at').first()


class ReponseForum(models.Model):
    """
    Modèle pour les réponses aux sujets du forum
    """
    sujet = models.ForeignKey(
        SujetForum,
        on_delete=models.CASCADE,
        related_name='reponses',
        verbose_name="Sujet"
    )
    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reponses_forum',
        verbose_name="Auteur"
    )
    contenu = models.TextField(verbose_name="Contenu")
    meilleure_reponse = models.BooleanField(default=False, verbose_name="Meilleure réponse")
    likes = models.ManyToManyField(
        User,
        related_name='reponses_likees',
        blank=True,
        verbose_name="J'aime"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Réponse du forum"
        verbose_name_plural = "Réponses du forum"
        ordering = ['-meilleure_reponse', 'created_at']
    
    def __str__(self):
        return f"Réponse de {self.auteur.username} sur {self.sujet.titre}"
    
    def nombre_likes(self):
        return self.likes.count()


class Conversation(models.Model):
    """
    Modèle pour les conversations privées
    """
    participants = models.ManyToManyField(
        User,
        related_name='conversations',
        verbose_name="Participants"
    )
    sujet = models.CharField(max_length=200, verbose_name="Sujet", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id}"
    
    def dernier_message(self):
        return self.messages.order_by('-created_at').first()
    
    def messages_non_lus(self, user):
        return self.messages.exclude(auteur=user).filter(lu=False).count()


class Message(models.Model):
    """
    Modèle pour les messages privés
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Conversation"
    )
    auteur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_envoyes',
        verbose_name="Auteur"
    )
    contenu = models.TextField(verbose_name="Contenu")
    lu = models.BooleanField(default=False, verbose_name="Lu")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message de {self.auteur.username}"


class Notification(models.Model):
    """
    Modèle pour les notifications
    """
    TYPE_CHOICES = (
        ('MESSAGE', 'Nouveau message'),
        ('REPONSE_FORUM', 'Réponse au forum'),
        ('INSCRIPTION', 'Nouvelle inscription'),
        ('SEANCE', 'Séance modifiée'),
    )
    
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Destinataire"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type")
    titre = models.CharField(max_length=200, verbose_name="Titre")
    message = models.TextField(verbose_name="Message")
    lien = models.CharField(max_length=200, blank=True, verbose_name="Lien")
    lue = models.BooleanField(default=False, verbose_name="Lue")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification pour {self.destinataire.username}"