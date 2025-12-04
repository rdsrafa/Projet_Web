from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from .models import User, Seance, Matiere, Inscription, Sujet, Reponse
from .forms import SeanceForm, InscriptionEtudiantForm, ChangementMotDePasseForm, SujetForm, ReponseForm, ProfilForm, ChangerMotDePasseProfilForm
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

# ========== VUES GÉNÉRALES ==========

def home(request):
    """Page d'accueil"""
    if request.user.is_authenticated:
        if request.user.is_admin():
            return redirect('admin:index')
        elif request.user.is_tuteur():
            return redirect('dashboard_tuteur')
        else:
            return redirect('dashboard_etudiant')
    else:
        return render(request, 'tutorat/home.html')

# ========== AUTHENTIFICATION ==========

@method_decorator(never_cache, name='dispatch')
class CustomLoginView(LoginView):
    template_name = 'tutorat/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
    
        # Si le tuteur doit changer son mot de passe
        if user.is_tuteur() and user.doit_changer_mdp:
            return reverse_lazy('changer_mot_de_passe_obligatoire')
    
        if user.is_admin():
            return reverse_lazy('admin:index')
        elif user.is_tuteur():
            return reverse_lazy('dashboard_tuteur')
        else:
            return reverse_lazy('dashboard_etudiant')
    
    def form_valid(self, form):
        messages.success(self.request, f'Bienvenue {form.get_user().get_full_name() or form.get_user().username} !')
        return super().form_valid(form)

def custom_logout(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')

def inscription_etudiant(request):
    """
    Inscription publique pour les étudiants
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = InscriptionEtudiantForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Bienvenue {user.get_full_name()} ! Votre compte étudiant a été créé avec succès.')
            return redirect('login')
    else:
        form = InscriptionEtudiantForm()
    
    return render(request, 'tutorat/inscription_etudiant.html', {'form': form})

@login_required
@never_cache
def changer_mot_de_passe_obligatoire(request):
    """
    Forcer le changement de mot de passe pour les tuteurs
    """
    if not request.user.doit_changer_mdp:
        return redirect('home')
    
    if request.method == 'POST':
        form = ChangementMotDePasseForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.doit_changer_mdp = False
            user.save()
            messages.success(request, 'Votre mot de passe a été changé avec succès !')
            return redirect('dashboard_tuteur')
    else:
        form = ChangementMotDePasseForm(request.user)
    
    return render(request, 'tutorat/changer_mot_de_passe.html', {'form': form})

@login_required
@never_cache
def dashboard_tuteur(request):
    # Rediriger si le tuteur doit changer son mot de passe
    if request.user.is_tuteur() and request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    return render(request, 'tutorat/dashboard_tuteur.html')

@login_required
@never_cache
def dashboard_etudiant(request):
    return render(request, 'tutorat/dashboard_etudiant.html')

# ========== VUES TUTEUR ==========

@login_required
@never_cache
def liste_seances_tuteur(request):
    if not request.user.is_tuteur():
        messages.error(request, "Accès réservé aux tuteurs.")
        return redirect('home')
    
    # Rediriger si doit changer mot de passe
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    seances = Seance.objects.filter(tuteur=request.user).order_by('-date')
    for seance in seances:
        seance.actualiser_statut()
    
    return render(request, 'tutorat/tuteur_liste_seances.html', {'seances': seances})

@login_required
@never_cache
def creer_seance(request):
    if not request.user.is_tuteur():
        messages.error(request, "Accès réservé aux tuteurs.")
        return redirect('home')
    
    # Rediriger si doit changer mot de passe
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    if request.method == 'POST':
        form = SeanceForm(request.POST)
        if form.is_valid():
            seance = form.save(commit=False)
            seance.tuteur = request.user
            seance.save()
            messages.success(request, f'La séance "{seance.titre}" a été créée avec succès !')
            return redirect('liste_seances_tuteur')
    else:
        form = SeanceForm()
    
    return render(request, 'tutorat/creer_seance.html', {'form': form})

@login_required
@never_cache
def modifier_seance(request, pk):
    seance = get_object_or_404(Seance, pk=pk, tuteur=request.user)
    
    # Rediriger si doit changer mot de passe
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    if request.method == 'POST':
        form = SeanceForm(request.POST, instance=seance)
        if form.is_valid():
            form.save()
            messages.success(request, f'La séance "{seance.titre}" a été modifiée avec succès !')
            return redirect('liste_seances_tuteur')
    else:
        form = SeanceForm(instance=seance)
    
    return render(request, 'tutorat/modifier_seance.html', {'form': form, 'seance': seance})

@login_required
def supprimer_seance(request, pk):
    seance = get_object_or_404(Seance, pk=pk, tuteur=request.user)
    
    # Rediriger si doit changer mot de passe
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    if request.method == 'POST':
        titre = seance.titre
        seance.delete()
        messages.success(request, f'La séance "{titre}" a été supprimée.')
        return redirect('liste_seances_tuteur')
    
    return render(request, 'tutorat/supprimer_seance.html', {'seance': seance})

@login_required
@never_cache
def calendrier_tuteur(request):
    if not request.user.is_tuteur():
        messages.error(request, "Accès réservé aux tuteurs.")
        return redirect('home')
    
    # Rediriger si doit changer mot de passe
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    return render(request, 'tutorat/calendrier_tuteur.html')

@login_required
def api_seances_tuteur(request):
    if not request.user.is_tuteur():
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    seances = Seance.objects.filter(tuteur=request.user)
    for seance in seances:
        seance.actualiser_statut()
    
    events = []
    for seance in seances:
        if seance.statut == 'planifiee':
            color = '#0d6efd'
        elif seance.statut == 'en_cours':
            color = '#198754'
        elif seance.statut == 'terminee':
            color = '#6c757d'
        else:
            color = '#dc3545'
        
        events.append({
            'id': seance.id,
            'title': f"{seance.titre} ({seance.places_restantes}/{seance.places_max})",
            'start': f"{seance.date}T{seance.heure_debut}",
            'end': f"{seance.date}T{seance.heure_fin}",
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'matiere': str(seance.matiere),
                'lieu': seance.lieu,
                'description': seance.description,
                'statut': seance.get_statut_display(),
                'inscrits': seance.inscriptions.filter(statut='confirmee').count(),
            }
        })
    
    return JsonResponse(events, safe=False)

# ========== VUES ÉTUDIANT ==========

@login_required
@never_cache
def liste_seances_etudiant(request):
    if not request.user.is_etudiant():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('home')
    
    # Récupérer les IDs des séances auxquelles l'étudiant est déjà inscrit
    seances_inscrites = Inscription.objects.filter(
        etudiant=request.user,
        statut='confirmee'
    ).values_list('seance_id', flat=True)
    
    # Afficher uniquement les séances disponibles (non inscrites)
    seances = Seance.objects.filter(
        statut='planifiee',
        date__gte=timezone.now().date()
    ).exclude(
        id__in=seances_inscrites
    ).order_by('date', 'heure_debut')
    
    return render(request, 'tutorat/etudiant_liste_seances.html', {'seances': seances})

@login_required
def inscrire_seance(request, pk):
    if not request.user.is_etudiant():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('home')
    
    seance = get_object_or_404(Seance, pk=pk)
    
    if Inscription.objects.filter(etudiant=request.user, seance=seance).exists():
        messages.warning(request, "Vous êtes déjà inscrit à cette séance.")
        return redirect('liste_seances_etudiant')
    
    if seance.est_complet:
        messages.error(request, "Cette séance est complète.")
        return redirect('liste_seances_etudiant')
    
    Inscription.objects.create(etudiant=request.user, seance=seance, statut='confirmee')
    messages.success(request, f'Vous êtes inscrit à la séance "{seance.titre}" !')
    return redirect('mes_inscriptions')

@login_required
@never_cache
def mes_inscriptions(request):
    if not request.user.is_etudiant():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('home')
    
    inscriptions = Inscription.objects.filter(
        etudiant=request.user
    ).select_related('seance', 'seance__matiere', 'seance__tuteur').order_by('seance__date', 'seance__heure_debut')
    
    # Actualiser tous les statuts et séparer les inscriptions
    inscriptions_actives = []
    inscriptions_historique = []
    
    for inscription in inscriptions:
        inscription.seance.actualiser_statut()
        inscription.actualiser_statut_selon_seance()
        
        # Séparer selon le statut affiché
        if inscription.statut_affichage == 'confirmee':
            inscriptions_actives.append(inscription)
        else:
            inscriptions_historique.append(inscription)
    
    context = {
        'inscriptions_actives': inscriptions_actives,
        'inscriptions_historique': inscriptions_historique,
    }
    
    return render(request, 'tutorat/mes_inscriptions.html', context)

@login_required
def desinscrire_seance(request, pk):
    inscription = get_object_or_404(Inscription, pk=pk, etudiant=request.user)
    
    if request.method == 'POST':
        seance_titre = inscription.seance.titre
        inscription.delete()
        messages.success(request, f'Vous vous êtes désinscrit de la séance "{seance_titre}".')
        return redirect('mes_inscriptions')
    
    return render(request, 'tutorat/desinscrire_seance.html', {'inscription': inscription})

@login_required
@never_cache
def calendrier_etudiant(request):
    if not request.user.is_etudiant():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('home')
    return render(request, 'tutorat/calendrier_etudiant.html')

@login_required
def api_seances_etudiant(request):
    if not request.user.is_etudiant():
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    # Récupérer TOUTES les inscriptions de l'étudiant
    inscriptions = Inscription.objects.filter(
        etudiant=request.user
    ).select_related('seance', 'seance__matiere', 'seance__tuteur')
    
    events = []
    for inscription in inscriptions:
        seance = inscription.seance
        seance.actualiser_statut()
        
        # Afficher uniquement si l'inscription est active (confirmée)
        if inscription.statut != 'confirmee':
            continue
        
        # Couleur selon le statut de la séance
        if seance.statut == 'planifiee':
            color = '#0d6efd'  # Bleu
        elif seance.statut == 'en_cours':
            color = '#198754'  # Vert
        elif seance.statut == 'terminee':
            color = '#6c757d'  # Gris
        else:  # annulee
            color = '#dc3545'  # Rouge
        
        events.append({
            'id': seance.id,
            'title': seance.titre,
            'start': f"{seance.date}T{seance.heure_debut}",
            'end': f"{seance.date}T{seance.heure_fin}",
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'matiere': str(seance.matiere),
                'tuteur': seance.tuteur.get_full_name() or seance.tuteur.username,
                'lieu': seance.lieu,
                'description': seance.description,
                'statut': seance.get_statut_display(),
            }
        })
    
    return JsonResponse(events, safe=False)

# ========== VUES FORUM ==========

@login_required
@never_cache
def forum_liste(request):
    """
    Liste des sujets du forum avec filtre par matière
    """
    matiere_id = request.GET.get('matiere')
    
    if matiere_id:
        sujets = Sujet.objects.filter(matiere_id=matiere_id).select_related('auteur', 'matiere')
    else:
        sujets = Sujet.objects.all().select_related('auteur', 'matiere')
    
    matieres = Matiere.objects.all()
    
    context = {
        'sujets': sujets,
        'matieres': matieres,
        'matiere_selectionnee': matiere_id,
    }
    return render(request, 'tutorat/forum_liste.html', context)

@login_required
@never_cache
def forum_sujet(request, pk):
    """
    Détail d'un sujet avec ses réponses
    """
    sujet = get_object_or_404(Sujet, pk=pk)
    reponses = sujet.reponses.select_related('auteur').all()
    
    if request.method == 'POST':
        form = ReponseForm(request.POST)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.sujet = sujet
            reponse.auteur = request.user
            reponse.save()
            messages.success(request, 'Votre réponse a été ajoutée !')
            return redirect('forum_sujet', pk=pk)
    else:
        form = ReponseForm()
    
    context = {
        'sujet': sujet,
        'reponses': reponses,
        'form': form,
    }
    return render(request, 'tutorat/forum_sujet.html', context)

@login_required
@never_cache
def forum_nouveau_sujet(request):
    """
    Créer un nouveau sujet
    """
    if request.method == 'POST':
        form = SujetForm(request.POST)
        if form.is_valid():
            sujet = form.save(commit=False)
            sujet.auteur = request.user
            sujet.save()
            messages.success(request, f'Votre sujet "{sujet.titre}" a été créé !')
            return redirect('forum_sujet', pk=sujet.pk)
    else:
        form = SujetForm()
    
    return render(request, 'tutorat/forum_nouveau_sujet.html', {'form': form})

@login_required
def forum_supprimer_sujet(request, pk):
    """
    Supprimer un sujet (auteur ou admin uniquement)
    """
    sujet = get_object_or_404(Sujet, pk=pk)
    
    # Vérifier que l'utilisateur est l'auteur ou admin
    if request.user != sujet.auteur and not request.user.is_admin():
        messages.error(request, "Vous ne pouvez pas supprimer ce sujet.")
        return redirect('forum_liste')
    
    if request.method == 'POST':
        titre = sujet.titre
        sujet.delete()
        messages.success(request, f'Le sujet "{titre}" a été supprimé.')
        return redirect('forum_liste')
    
    return render(request, 'tutorat/forum_supprimer_sujet.html', {'sujet': sujet})

@login_required
def forum_supprimer_reponse(request, pk):
    """
    Supprimer une réponse (auteur ou admin uniquement)
    """
    reponse = get_object_or_404(Reponse, pk=pk)
    sujet_pk = reponse.sujet.pk
    
    # Vérifier que l'utilisateur est l'auteur ou admin
    if request.user != reponse.auteur and not request.user.is_admin():
        messages.error(request, "Vous ne pouvez pas supprimer cette réponse.")
        return redirect('forum_sujet', pk=sujet_pk)
    
    if request.method == 'POST':
        reponse.delete()
        messages.success(request, 'La réponse a été supprimée.')
        return redirect('forum_sujet', pk=sujet_pk)
    
    return render(request, 'tutorat/forum_supprimer_reponse.html', {'reponse': reponse})

# ========== VUES PROFIL ==========

@login_required
@never_cache
def mon_profil(request):
    """
    Afficher et modifier le profil utilisateur
    """
    return render(request, 'tutorat/mon_profil.html')

@login_required
@never_cache
def modifier_profil(request):
    """
    Modifier les informations du profil
    """
    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('mon_profil')
    else:
        form = ProfilForm(instance=request.user)
    
    return render(request, 'tutorat/modifier_profil.html', {'form': form})

@login_required
@never_cache
def changer_mot_de_passe_profil(request):
    """
    Changer le mot de passe depuis le profil
    """
    if request.method == 'POST':
        form = ChangerMotDePasseProfilForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Garder l'utilisateur connecté après changement de mot de passe
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Votre mot de passe a été changé avec succès !')
            return redirect('mon_profil')
    else:
        form = ChangerMotDePasseProfilForm(request.user)
    
    return render(request, 'tutorat/changer_mot_de_passe_profil.html', {'form': form})