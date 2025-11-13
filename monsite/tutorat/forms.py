from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Seance, Matiere, SujetForum, ReponseForum, Message


class InscriptionForm(UserCreationForm):
    """
    Formulaire d'inscription avec choix du rôle
    """
    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        }),
        label="Prénom"
    )
    
    last_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom'
        }),
        label="Nom"
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    role = forms.ChoiceField(
        choices=[('ETUDIANT', 'Étudiant'), ('TUTEUR', 'Tuteur')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Je m'inscris en tant que"
    )
    
    telephone = forms.CharField(
        required=False,
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Téléphone (optionnel)'
        })
    )
    
    date_naissance = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Date de naissance (optionnel)"
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'role', 'telephone', 'date_naissance', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Nom d'utilisateur"
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })


class ConnexionForm(AuthenticationForm):
    """
    Formulaire de connexion personnalisé
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Nom d'utilisateur"
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )


class SeanceForm(forms.ModelForm):
    """
    Formulaire pour créer et modifier une séance de tutorat
    """
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Date"
    )
    
    heure_debut = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label="Heure de début"
    )
    
    heure_fin = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label="Heure de fin"
    )
    
    class Meta:
        model = Seance
        fields = ['titre', 'matiere', 'date', 'heure_debut', 'heure_fin', 'lieu', 'description', 'places_max']
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Révision Python'
            }),
            'matiere': forms.Select(attrs={'class': 'form-control'}),
            'lieu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Salle B201'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez le contenu de la séance...'
            }),
            'places_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 50
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si pas de matières disponibles, afficher un message
        if not Matiere.objects.exists():
            self.fields['matiere'].help_text = "⚠️ Aucune matière disponible. Contactez l'administrateur."


class SujetForumForm(forms.ModelForm):
    """
    Formulaire pour créer un sujet sur le forum
    """
    class Meta:
        model = SujetForum
        fields = ['titre', 'matiere', 'contenu']
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de votre question...'
            }),
            'matiere': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Décrivez votre question en détail...'
            }),
        }
        labels = {
            'titre': 'Titre de la question',
            'matiere': 'Matière concernée',
            'contenu': 'Votre question',
        }


class ReponseForumForm(forms.ModelForm):
    """
    Formulaire pour répondre à un sujet du forum
    """
    class Meta:
        model = ReponseForum
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Écrivez votre réponse...'
            }),
        }
        labels = {
            'contenu': 'Votre réponse',
        }


class MessageForm(forms.ModelForm):
    """
    Formulaire pour envoyer un message privé
    """
    class Meta:
        model = Message
        fields = ['contenu']
        widgets = {
            'contenu': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Écrivez votre message...'
            }),
        }
        labels = {
            'contenu': '',
        }