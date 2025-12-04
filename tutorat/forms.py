from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Seance, Matiere, Sujet, Reponse, User
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm



# ========== FORMULAIRE SÉANCE ==========

class SeanceForm(forms.ModelForm):
    """
    Formulaire de création/modification de séance
    """
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
            'places_max': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
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
        super().__init__(*args, **kwargs)
        
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
    
    def clean(self):
        """
        Validation personnalisée
        """
        cleaned_data = super().clean()
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        
        if heure_debut and heure_fin and heure_debut >= heure_fin:
            raise forms.ValidationError("L'heure de fin doit être après l'heure de début.")
        
        return cleaned_data


# ========== FORMULAIRES FORUM ==========

class SujetForm(forms.ModelForm):
    """
    Formulaire de création de sujet
    """
    class Meta:
        model = Sujet
        fields = ['titre', 'matiere', 'contenu']
        
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Comment résoudre une équation ?'}),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Décrivez votre question ou sujet de discussion...'}),
        }
        
        labels = {
            'titre': 'Titre du sujet',
            'matiere': 'Matière concernée',
            'contenu': 'Votre message',
        }


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