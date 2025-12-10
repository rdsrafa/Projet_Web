from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Seance, Matiere, Sujet, Reponse, User
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from datetime import date, timedelta, time
from django import forms
from django.core.exceptions import ValidationError



# ========== FORMULAIRE SÉANCE ==========

class SeanceForm(forms.ModelForm):
    """
    Formulaire de création/modification de séance
    """
    
    def __init__(self, *args, **kwargs):
        self.tuteur = kwargs.pop('tuteur', None)
        super().__init__(*args, **kwargs)
        # Le reste du __init__ sera ajouté après
    
    class Meta:
        model = Seance
        fields = ['matiere', 'titre', 'description', 'date', 'heure_debut', 'heure_fin', 'lieu', 'places_max', 'statut']
        
        widgets = {
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Révision Algèbre'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Décrivez le contenu de la séance...'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}, format='%H:%M'),
            'lieu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Salle G103'}),
            'places_max': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '40'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'matiere': 'Matière',
            'titre': 'Titre de la séance',
            'description': 'Description',
            'date': 'Date',
            'heure_debut': 'Heure de début',
            'heure_fin': 'Heure de fin',
            'lieu': 'Lieu',
            'places_max': 'Nombre de places maximum',
            'statut': 'Statut',
        }
    
    def __init__(self, *args, **kwargs):
        self.tuteur = kwargs.pop('tuteur', None)
        super().__init__(*args, **kwargs)

        # Rendre la description optionnelle
        self.fields['description'].required = False
        
        # Définir les limites de date (aujourd'hui à 6 mois)
        today = date.today()
        max_date = today + timedelta(days=180)
        self.fields['date'].widget.attrs.update({
            'min': today.strftime('%Y-%m-%d'),
            'max': max_date.strftime('%Y-%m-%d')
        })
        
        # Limiter les choix de statut selon création ou modification
        if self.instance and self.instance.pk:
            # MODIFICATION : seulement Planifiée et Annulée
            self.fields['statut'].choices = [
                ('planifiee', 'Planifiée'),
                ('annulee', 'Annulée'),
            ]
            
            # Pré-remplir les dates/heures
            if self.instance.date:
                self.initial['date'] = self.instance.date.strftime('%Y-%m-%d')
            if self.instance.heure_debut:
                self.initial['heure_debut'] = self.instance.heure_debut.strftime('%H:%M')
            if self.instance.heure_fin:
                self.initial['heure_fin'] = self.instance.heure_fin.strftime('%H:%M')
        else:
            # CRÉATION : seulement Planifiée (par défaut)
            self.fields['statut'].choices = [
                ('planifiee', 'Planifiée'),
            ]
            self.fields['statut'].initial = 'planifiee'
    
    def clean_date(self):
        """
        Valider que la date est dans le futur, max 6 mois, et pas un dimanche
        """
        date_seance = self.cleaned_data.get('date')
        today = date.today()
        max_date = today + timedelta(days=180)  # 6 mois = environ 180 jours
    
        if date_seance < today:
            raise ValidationError("La date de la séance ne peut pas être dans le passé.")
    
        if date_seance > max_date:
            raise ValidationError("La date de la séance ne peut pas dépasser 6 mois dans le futur.")
    
        # Vérifier si c'est un dimanche (weekday() == 6)
        if date_seance.weekday() == 6:
            raise ValidationError("Les séances ne peuvent pas être planifiées le dimanche.")
    
        return date_seance
    
    def clean_heure_debut(self):
        """
        Valider que l'heure de début est entre 8h30 et 21h
        """
        heure_debut = self.cleaned_data.get('heure_debut')
        
        if heure_debut:
            heure_min = time(8, 30)  # 8h30
            heure_max = time(21, 0)  # 21h
            
            if heure_debut < heure_min:
                raise ValidationError("L'heure de début ne peut pas être avant 8h30.")
            
            if heure_debut >= heure_max:
                raise ValidationError("L'heure de début doit être avant 21h.")
        
        return heure_debut
    
    def clean_heure_fin(self):
        """
        Valider que l'heure de fin est entre 8h30 et 21h
        """
        heure_fin = self.cleaned_data.get('heure_fin')
        
        if heure_fin:
            heure_min = time(8, 30)  # 8h30
            heure_max = time(21, 0)   # 21h
            
            if heure_fin <= heure_min:
                raise ValidationError("L'heure de fin doit être après 8h30.")
            
            if heure_fin > heure_max:
                raise ValidationError("L'heure de fin ne peut pas être après 21h.")
        
        return heure_fin
    
    def clean_places_max(self):
        """
        Valider que le nombre de places est entre 1 et 40
        """
        places = self.cleaned_data.get('places_max')
        
        if places < 1:
            raise ValidationError("Le nombre de places doit être au minimum de 1.")
        
        if places > 40:
            raise ValidationError("Le nombre de places ne peut pas dépasser 40.")
        
        return places
    
    def clean(self):
        """
        Validation croisée pour vérifier :
        1. L'heure de fin est après l'heure de début
        2. Pas de chevauchement avec d'autres séances du tuteur
        """
        cleaned_data = super().clean()
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        date_seance = cleaned_data.get('date')
        
        # Validation 1 : heure de fin après heure de début
        if heure_debut and heure_fin:
            if heure_fin <= heure_debut:
                raise ValidationError("L'heure de fin doit être après l'heure de début.")
        
        # Validation 2 : pas de chevauchement avec d'autres séances
        if self.tuteur and date_seance and heure_debut and heure_fin:
            # Récupérer toutes les séances du tuteur pour cette date
            seances_meme_jour = Seance.objects.filter(
                tuteur=self.tuteur,
                date=date_seance,
                statut__in=['planifiee', 'en_cours']  # Exclure les annulées et terminées
            )
            
            # Si on modifie une séance existante, l'exclure de la vérification
            if self.instance and self.instance.pk:
                seances_meme_jour = seances_meme_jour.exclude(pk=self.instance.pk)
            
            # Vérifier les chevauchements
            for seance in seances_meme_jour:
                # Deux séances se chevauchent si :
                # - La nouvelle commence avant que l'ancienne ne finisse ET
                # - La nouvelle finit après que l'ancienne ne commence
                if (heure_debut < seance.heure_fin and heure_fin > seance.heure_debut):
                    raise ValidationError(
                        f"Cette séance chevauche une autre séance déjà planifiée : "
                        f"'{seance.titre}' de {seance.heure_debut.strftime('%H:%M')} "
                        f"à {seance.heure_fin.strftime('%H:%M')}."
                    )
        
        return cleaned_data


# ========== FORMULAIRES FORUM ==========

class SujetForm(forms.ModelForm):
    class Meta:
        model = Sujet
        fields = ['titre', 'matiere', 'contenu']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre du sujet'}),
            'matiere': forms.Select(attrs={'class': 'form-select'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Votre message...'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si l'utilisateur est admin, la matière devient optionnelle
        if user and user.is_admin():
            self.fields['matiere'].required = False
            self.fields['matiere'].help_text = "Laissez vide pour une annonce générale"
        else:
            self.fields['matiere'].required = True


class ReponseForm(forms.ModelForm):
    """
    Formulaire de réponse
    """
    class Meta:
        model = Reponse
        fields = ['contenu']
        
        widgets = {
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Écrivez votre réponse...'}),
        }
        
        labels = {
            'contenu': 'Votre réponse',
        }


# ========== FORMULAIRE INSCRIPTION ÉTUDIANT ==========

class InscriptionEtudiantForm(UserCreationForm):
    """
    Formulaire d'inscription pour les étudiants
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'votre.email@exemple.fr'})
    )
    first_name = forms.CharField(
        required=True,
        label='Prénom',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jean'})
    )
    last_name = forms.CharField(
        required=True,
        label='Nom',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dupont'})
    )
    telephone = forms.CharField(
        required=False,
        label='Téléphone',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0612345678'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'telephone', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'nom.prenom'}),
        }
        labels = {
            'username': "Nom d'utilisateur",
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les champs de mot de passe
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': '••••••••'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': '••••••••'})
        self.fields['password1'].label = 'Mot de passe'
        self.fields['password2'].label = 'Confirmer le mot de passe'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'etudiant'  # Forcer le rôle étudiant
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
    

# ========== FORMULAIRE CHANGEMENT MOT DE PASSE ==========

class ChangementMotDePasseForm(SetPasswordForm):
    """
    Formulaire pour le changement de mot de passe obligatoire
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmez le nouveau mot de passe'
        })
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmer le nouveau mot de passe'


# ========== FORMULAIRES PROFIL ==========

class ProfilForm(forms.ModelForm):
    """
    Formulaire de modification du profil
    """
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'telephone']
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'username': "Nom d'utilisateur",
            'email': 'Email',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'telephone': 'Téléphone',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Le username ne peut pas être modifié
        self.fields['username'].disabled = True


class ChangerMotDePasseProfilForm(PasswordChangeForm):
    """
    Formulaire de changement de mot de passe dans le profil
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe actuel'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmez le nouveau mot de passe'
        })
        self.fields['old_password'].label = 'Mot de passe actuel'
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmer le nouveau mot de passe'