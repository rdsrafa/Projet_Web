from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from .models import Seance, Inscription, Matiere, Sujet, Reponse, BannissementTuteur, Conversation, Message, User
from .forms import SeanceForm, InscriptionEtudiantForm, ChangementMotDePasseForm, SujetForm, ReponseForm, ProfilForm, ChangerMotDePasseProfilForm
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.db.models import Count
from django.db import models

# ========== VUES GÉNÉRALES ==========

def home(request):
    """Page d'accueil"""
    if request.user.is_authenticated:
        if request.user.is_admin():
            return redirect('dashboard_admin')  # ← Changez cette ligne
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
            return reverse_lazy('dashboard_admin')
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
    """
    Dashboard tuteur avec statistiques
    """
    if not request.user.is_tuteur():
        messages.error(request, "Accès réservé aux tuteurs.")
        return redirect('home')
    
    # Rediriger si le tuteur doit changer son mot de passe
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    # Statistique 1 : Séances planifiées (à venir)
    seances_planifiees_count = Seance.objects.filter(
        tuteur=request.user,
        statut='planifiee',
        date__gte=timezone.now().date()
    ).count()
    
    # Statistique 2 : Total d'inscrits (toutes séances à venir)
    total_inscrits_count = Inscription.objects.filter(
        seance__tuteur=request.user,
        seance__date__gte=timezone.now().date(),
        statut='confirmee'
    ).count()
    
    # Statistique 3 : Séances terminées
    seances_terminees_count = Seance.objects.filter(
        tuteur=request.user,
        date__lt=timezone.now().date()
    ).count()
    
    # Statistique 4 : Étudiants bannis
    etudiants_bannis_count = BannissementTuteur.objects.filter(
        tuteur=request.user
    ).count()
    
    # Prochaines séances (5 prochaines séances à venir)
    prochaines_seances = Seance.objects.filter(
        tuteur=request.user,
        statut='planifiee',
        date__gte=timezone.now().date()
    ).select_related('matiere').order_by('date', 'heure_debut')[:5]
    
    # Ajouter le nombre d'inscrits pour chaque séance
    for seance in prochaines_seances:
        seance.inscrits_count = Inscription.objects.filter(
            seance=seance,
            statut='confirmee'
        ).count()
    
    context = {
        'seances_planifiees_count': seances_planifiees_count,
        'total_inscrits_count': total_inscrits_count,
        'seances_terminees_count': seances_terminees_count,
        'etudiants_bannis_count': etudiants_bannis_count,
        'prochaines_seances': prochaines_seances,
    }
    
    return render(request, 'tutorat/dashboard_tuteur.html', context)


@login_required
@never_cache
def dashboard_etudiant(request):
    """
    Dashboard étudiant avec statistiques
    """
    if not request.user.is_etudiant():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('home')
    
    # Statistique 1 : Inscriptions actives (séances à venir)
    mes_inscriptions_count = Inscription.objects.filter(
        etudiant=request.user,
        statut='confirmee',
        seance__date__gte=timezone.now().date()
    ).count()
    
    # Statistique 2 : Séances disponibles
    # Exclure les tuteurs qui ont banni l'étudiant
    tuteurs_bannis = BannissementTuteur.objects.filter(
        etudiant=request.user
    ).values_list('tuteur_id', flat=True)
    
    # Exclure les séances où l'étudiant est déjà inscrit
    seances_inscrites = Inscription.objects.filter(
        etudiant=request.user,
        statut='confirmee'
    ).values_list('seance_id', flat=True)
    
    seances_disponibles_count = Seance.objects.filter(
        statut='planifiee',
        date__gte=timezone.now().date()
    ).exclude(
        id__in=seances_inscrites
    ).exclude(
        tuteur_id__in=tuteurs_bannis
    ).count()
    
    # Statistique 3 : Séances terminées
    seances_terminees_count = Inscription.objects.filter(
        etudiant=request.user,
        statut='confirmee',
        seance__date__lt=timezone.now().date()
    ).count()
    
    # Statistique 4 : Mes sujets forum
    mes_sujets_forum_count = Sujet.objects.filter(auteur=request.user).count()
    
    context = {
        'mes_inscriptions_count': mes_inscriptions_count,
        'seances_disponibles_count': seances_disponibles_count,
        'seances_terminees_count': seances_terminees_count,
        'mes_sujets_forum_count': mes_sujets_forum_count,
    }
    
    return render(request, 'tutorat/dashboard_etudiant.html', context)

# ========== VUES TUTEUR ==========

@login_required
@never_cache
def liste_seances_tuteur(request):
    if not request.user.is_tuteur() and not request.user.is_admin():
        messages.error(request, "Accès réservé aux tuteurs et administrateurs.")
        return redirect('home')
    
    # Si admin, afficher toutes les séances, sinon uniquement celles du tuteur
    if request.user.is_admin():
        seances = Seance.objects.all().order_by('-date')
    else:
        seances = Seance.objects.filter(tuteur=request.user).order_by('-date')
    
    # Rediriger si tuteur doit changer mot de passe
    if request.user.is_tuteur() and request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    for seance in seances:
        seance.actualiser_statut()
    
    # Compter les étudiants bannis (seulement pour les tuteurs)
    nb_bannis = 0
    if request.user.is_tuteur():
        nb_bannis = BannissementTuteur.objects.filter(tuteur=request.user).count()
    
    context = {
        'seances': seances,
        'nb_bannis': nb_bannis,
    }
    
    return render(request, 'tutorat/tuteur_liste_seances.html', context)

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
        form = SeanceForm(request.POST, tuteur=request.user)
        if form.is_valid():
            seance = form.save(commit=False)
            seance.tuteur = request.user
            seance.save()
            messages.success(request, f'La séance "{seance.titre}" a été créée avec succès !')
            return redirect('liste_seances_tuteur')
    else:
        form = SeanceForm(tuteur=request.user)
    
    return render(request, 'tutorat/creer_seance.html', {'form': form})

@login_required
@never_cache
def modifier_seance(request, pk):
    seance = get_object_or_404(Seance, pk=pk, tuteur=request.user)
    
    # Rediriger si doit changer mot de passe
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    if request.method == 'POST':
        form = SeanceForm(request.POST, instance=seance, tuteur=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'La séance "{seance.titre}" a été modifiée avec succès !')
            return redirect('liste_seances_tuteur')
    else:
        form = SeanceForm(instance=seance, tuteur=request.user)
    
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
def voir_inscrits(request, pk):
    """
    Voir la liste des étudiants inscrits à une séance (tuteur uniquement)
    """
    if not request.user.is_tuteur():
        messages.error(request, "Accès réservé aux tuteurs.")
        return redirect('home')
    
    # Rediriger si doit changer mot de passe
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    seance = get_object_or_404(Seance, pk=pk, tuteur=request.user)
    inscriptions = Inscription.objects.filter(
        seance=seance,
        statut='confirmee'
    ).select_related('etudiant').order_by('etudiant__last_name', 'etudiant__first_name')
    
    context = {
        'seance': seance,
        'inscriptions': inscriptions,
    }
    
    return render(request, 'tutorat/voir_inscrits.html', context)


@login_required
def exclure_etudiant(request, pk):
    """
    Exclure un étudiant d'une séance avec option de bannissement (tuteur uniquement)
    """
    if not request.user.is_tuteur():
        messages.error(request, "Accès réservé aux tuteurs.")
        return redirect('home')
    
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    inscription = get_object_or_404(Inscription, pk=pk, seance__tuteur=request.user)
    seance_id = inscription.seance.pk
    etudiant = inscription.etudiant
    
    if request.method == 'POST':
        raison = request.POST.get('raison', '')
        bannir = request.POST.get('bannir') == 'on'
        
        etudiant_nom = etudiant.get_full_name() or etudiant.username
        
        # Si bannissement demandé
        if bannir:
            # 1. Créer le bannissement
            BannissementTuteur.objects.get_or_create(
                tuteur=request.user,
                etudiant=etudiant,
                defaults={'raison': raison}
            )
            
            # 2. Supprimer TOUTES les inscriptions de cet étudiant aux séances de ce tuteur
            inscriptions_a_supprimer = Inscription.objects.filter(
                etudiant=etudiant,
                seance__tuteur=request.user,
                statut='confirmee'
            )
            nb_inscriptions_supprimees = inscriptions_a_supprimer.count()
            inscriptions_a_supprimer.delete()
            
            messages.warning(
                request, 
                f"{etudiant_nom} a été exclu de {nb_inscriptions_supprimees} séance(s) "
                f"et banni de toutes vos séances futures."
            )
        else:
            # Exclure seulement de cette séance
            inscription.delete()
            messages.success(request, f"{etudiant_nom} a été exclu de cette séance.")
        
        return redirect('voir_inscrits', pk=seance_id)
    
    return render(request, 'tutorat/exclure_etudiant.html', {'inscription': inscription})

@login_required
@never_cache
def liste_bannis(request):
    """
    Liste des étudiants bannis par le tuteur
    """
    if not request.user.is_tuteur():
        messages.error(request, "Accès réservé aux tuteurs.")
        return redirect('home')
    
    # Rediriger si doit changer mot de passe
    if request.user.doit_changer_mdp:
        return redirect('changer_mot_de_passe_obligatoire')
    
    from .models import BannissementTuteur
    bannis = BannissementTuteur.objects.filter(tuteur=request.user).select_related('etudiant').order_by('-date_bannissement')
    
    return render(request, 'tutorat/liste_bannis.html', {'bannis': bannis})


@login_required
def debannir_etudiant(request, pk):
    """
    Débannir un étudiant (tuteur uniquement)
    """
    if not request.user.is_tuteur():
        messages.error(request, "Accès réservé aux tuteurs.")
        return redirect('home')
    
    from .models import BannissementTuteur
    bannissement = get_object_or_404(BannissementTuteur, pk=pk, tuteur=request.user)
    
    if request.method == 'POST':
        etudiant_nom = bannissement.etudiant.get_full_name() or bannissement.etudiant.username
        bannissement.delete()
        messages.success(request, f"{etudiant_nom} a été débanni. Il peut maintenant s'inscrire à vos séances.")
        return redirect('liste_bannis')
    
    return render(request, 'tutorat/debannir_etudiant.html', {'bannissement': bannissement})

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
    
    # Récupérer les tuteurs qui ont banni cet étudiant
    tuteurs_bannis = BannissementTuteur.objects.filter(
        etudiant=request.user
    ).values_list('tuteur_id', flat=True)
    
    # Récupérer les IDs des séances auxquelles l'étudiant est déjà inscrit
    seances_inscrites = Inscription.objects.filter(
        etudiant=request.user,
        statut='confirmee'
    ).values_list('seance_id', flat=True)
    
    # Afficher uniquement les séances disponibles (non inscrites et tuteurs non bannis)
    seances = Seance.objects.filter(
        statut='planifiee',
        date__gte=timezone.now().date()
    ).exclude(
        id__in=seances_inscrites
    ).exclude(
        tuteur_id__in=tuteurs_bannis
    ).order_by('date', 'heure_debut')
    
    return render(request, 'tutorat/etudiant_liste_seances.html', {'seances': seances})

@login_required
def inscrire_seance(request, pk):
    if not request.user.is_etudiant():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('home')
    
    seance = get_object_or_404(Seance, pk=pk)
    
    # Vérifier si l'étudiant est banni par ce tuteur
    if BannissementTuteur.objects.filter(tuteur=seance.tuteur, etudiant=request.user).exists():
        messages.error(request, "Vous ne pouvez pas vous inscrire aux séances de ce tuteur.")
        return redirect('liste_seances_etudiant')
    
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
    
    # Ajouter le nombre de nouvelles réponses pour chaque sujet
    for sujet in sujets:
        # Compter les nouvelles réponses sur MES sujets depuis la dernière visite
        if request.user.derniere_visite_forum and sujet.auteur == request.user:
            nb_nouvelles = sujet.reponses.filter(
                date_creation__gt=request.user.derniere_visite_forum
            ).exclude(auteur=request.user).count()
            sujet.nb_nouvelles_reponses = nb_nouvelles
        else:
            sujet.nb_nouvelles_reponses = 0
    
    matieres = Matiere.objects.all()
    
    # Mettre à jour la dernière visite du forum
    request.user.derniere_visite_forum = timezone.now()
    request.user.save(update_fields=['derniere_visite_forum'])
    
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
        form = SujetForm(request.POST, user=request.user)
        if form.is_valid():
            sujet = form.save(commit=False)
            sujet.auteur = request.user
            sujet.save()
            messages.success(request, f'Votre sujet "{sujet.titre}" a été créé !')
            return redirect('forum_sujet', pk=sujet.pk)
    else:
        form = SujetForm(user=request.user)
    
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


# ========== VUE DASHBOARD ADMIN ==========

@login_required
@never_cache
def dashboard_admin(request):
    """
    Dashboard administrateur avec statistiques
    """
    if not request.user.is_admin():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('home')
    
    # Statistiques utilisateurs
    total_users = User.objects.count()
    total_tuteurs = User.objects.filter(role='tuteur').count()
    total_etudiants = User.objects.filter(role='etudiant').count()
    
    # Statistiques séances et inscriptions
    total_seances = Seance.objects.count()
    total_inscriptions = Inscription.objects.filter(statut='confirmee').count()
    
    # Statistiques forum
    total_sujets_forum = Sujet.objects.count()
    
    # Statistiques matières
    total_matieres = Matiere.objects.count()

    # Statistiques bannissements
    total_bannissements = BannissementTuteur.objects.count()
    
    # Séances récentes (5 dernières)
    seances_recentes = Seance.objects.select_related('tuteur', 'matiere').order_by('-date_creation')[:5]
    
    # Statistiques du mois en cours
    from django.utils import timezone
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    seances_ce_mois = Seance.objects.filter(date__gte=debut_mois).count()
    tuteurs_actifs = Seance.objects.filter(date__gte=debut_mois).values('tuteur').distinct().count()
    etudiants_inscrits_mois = Inscription.objects.filter(
        date_inscription__gte=debut_mois,
        statut='confirmee'
    ).values('etudiant').distinct().count()
    
    context = {
        'total_users': total_users,
        'total_tuteurs': total_tuteurs,
        'total_etudiants': total_etudiants,
        'total_seances': total_seances,
        'total_inscriptions': total_inscriptions,
        'total_sujets_forum': total_sujets_forum,
        'total_matieres': total_matieres,
        'seances_recentes': seances_recentes,
        'tuteurs_actifs': tuteurs_actifs,
        'etudiants_inscrits_mois': etudiants_inscrits_mois,
        'seances_ce_mois': seances_ce_mois,
        'total_bannissements': total_bannissements,
    }
    
    return render(request, 'tutorat/dashboard_admin.html', context)

@login_required
@never_cache
def gestion_bannissements_admin(request):
    """
    Gestion globale des bannissements pour l'admin
    """
    if not request.user.is_admin():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('home')
    
    # Récupérer tous les bannissements
    bannissements = BannissementTuteur.objects.select_related('tuteur', 'etudiant').order_by('-date_bannissement')
    
    # Statistiques
    total_bannissements = bannissements.count()
    tuteurs_avec_bannis = bannissements.values('tuteur').distinct().count()
    etudiants_bannis = bannissements.values('etudiant').distinct().count()
    
    context = {
        'bannissements': bannissements,
        'total_bannissements': total_bannissements,
        'tuteurs_avec_bannis': tuteurs_avec_bannis,
        'etudiants_bannis': etudiants_bannis,
    }
    
    return render(request, 'tutorat/admin_bannissements.html', context)


@login_required
def debannir_admin(request, pk):
    """
    Débannir un étudiant (admin uniquement)
    """
    if not request.user.is_admin():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('home')
    
    bannissement = get_object_or_404(BannissementTuteur, pk=pk)
    
    if request.method == 'POST':
        etudiant_nom = bannissement.etudiant.get_full_name() or bannissement.etudiant.username
        tuteur_nom = bannissement.tuteur.get_full_name() or bannissement.tuteur.username
        bannissement.delete()
        messages.success(request, f"{etudiant_nom} a été débanni par l'administrateur (banni par {tuteur_nom}).")
        return redirect('gestion_bannissements_admin')
    
    return render(request, 'tutorat/admin_debannir.html', {'bannissement': bannissement})


@login_required
@never_cache
def moderation_forum_admin(request):
    """
    Page de modération du forum pour l'admin
    """
    if not request.user.is_admin():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('home')
    
    # Récupérer tous les sujets avec statistiques
    sujets = Sujet.objects.select_related('auteur', 'matiere').prefetch_related('reponses').order_by('-date_creation')
    
    # Statistiques
    total_sujets = sujets.count()
    total_reponses = Reponse.objects.count()
    sujets_sans_reponse = sujets.filter(reponses__isnull=True).count()
    
    # Sujets par matière (exclure les annonces générales sans matière)
    sujets_par_matiere = sujets.filter(matiere__isnull=False).values('matiere__nom').annotate(
    count=models.Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'sujets': sujets,
        'total_sujets': total_sujets,
        'total_reponses': total_reponses,
        'sujets_sans_reponse': sujets_sans_reponse,
        'sujets_par_matiere': sujets_par_matiere,
    }
    
    return render(request, 'tutorat/admin_moderation_forum.html', context)


@login_required
@never_cache
def liste_seances_admin(request):
    """
    Liste de toutes les séances pour l'admin (lecture seule)
    """
    if not request.user.is_admin():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('home')
    
    seances = Seance.objects.all().select_related('tuteur', 'matiere').order_by('-date', '-heure_debut')
    
    for seance in seances:
        seance.actualiser_statut()
    
    return render(request, 'tutorat/admin_liste_seances.html', {'seances': seances})

# ===== MESSAGERIE PRIVÉE =====

@login_required
@never_cache
def messagerie_liste(request):
    """
    Liste toutes les conversations de l'utilisateur
    """
    conversations_queryset = request.user.conversations.all().order_by('-created_at')
    
    # Enrichir chaque conversation avec des infos utiles
    conversations = []
    for conv in conversations_queryset:
        autre_user = conv.other_participant(request.user)
        dernier_msg = conv.last_message()
        
        # Compter messages non lus dans cette conversation
        nb_non_lus = conv.messages.filter(is_read=False).exclude(sender=request.user).count()
        
        conversations.append({
            'pk': conv.pk,
            'other': autre_user,
            'last_message': dernier_msg.content if dernier_msg else None,
            'last_message_time': dernier_msg.created_at if dernier_msg else conv.created_at,
            'nb_non_lus': nb_non_lus
        })
    
    # Trier par date du dernier message
    conversations.sort(key=lambda x: x['last_message_time'], reverse=True)
    
    # Total messages non lus
    total_non_lus = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    
    context = {
        'conversations': conversations,
        'total_non_lus': total_non_lus
    }
    
    return render(request, 'tutorat/messagerie_conversation.html', context)


@login_required
@never_cache
def messagerie_conversation_detail(request, pk):
    """
    Affiche une conversation spécifique avec tous ses messages
    """
    conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)
    autre_user = conversation.other_participant(request.user)
    
    # Récupérer tous les messages
    messages_list = conversation.messages.all().order_by('created_at')
    
    # Marquer comme lus les messages reçus
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    # Envoyer un nouveau message
    if request.method == 'POST':
        contenu = request.POST.get('content')
        if contenu:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=contenu
            )
            messages.success(request, 'Message envoyé !')
            return redirect('messagerie_conversation_detail', pk=pk)
    
    context = {
        'conversation': conversation,
        'autre_user': autre_user,
        'messages_list': messages_list
    }
    
    return render(request, 'tutorat/messagerie_conversation_detail.html', context)


@login_required
@never_cache
def messagerie_nouvelle(request):
    """
    Créer une nouvelle conversation
    """
    if request.method == 'POST':
        destinataire_id = request.POST.get('destinataire')
        contenu = request.POST.get('content')
        
        if destinataire_id and contenu:
            destinataire = get_object_or_404(User, pk=destinataire_id)
            
            # Vérifier si une conversation existe déjà entre ces 2 utilisateurs
            conversation_existante = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=destinataire
            ).first()
            
            if conversation_existante:
                # Utiliser la conversation existante
                Message.objects.create(
                    conversation=conversation_existante,
                    sender=request.user,
                    content=contenu
                )
                messages.success(request, 'Message envoyé !')
                return redirect('messagerie_conversation_detail', pk=conversation_existante.pk)
            else:
                # Créer une nouvelle conversation
                nouvelle_conv = Conversation.objects.create()
                nouvelle_conv.participants.add(request.user, destinataire)
                
                # Créer le premier message
                Message.objects.create(
                    conversation=nouvelle_conv,
                    sender=request.user,
                    content=contenu
                )
                
                messages.success(request, 'Conversation créée et message envoyé !')
                return redirect('messagerie_conversation_detail', pk=nouvelle_conv.pk)
    
    # Filtrer les utilisateurs selon le rôle
    if request.user.is_etudiant():
        # Les étudiants ne peuvent contacter que les tuteurs
        utilisateurs = User.objects.filter(role='tuteur').order_by('first_name', 'last_name', 'username')
    else:
        # Admin et tuteurs peuvent contacter tout le monde (sauf eux-mêmes)
        utilisateurs = User.objects.exclude(pk=request.user.pk).order_by('first_name', 'last_name', 'username')
    
    # Destinataire pré-sélectionné ?
    destinataire_preselectionne = None
    if 'destinataire' in request.GET:
        destinataire_id = request.GET.get('destinataire')
        destinataire_preselectionne = User.objects.filter(pk=destinataire_id).first()
    
    context = {
        'utilisateurs': utilisateurs,
        'destinataire_preselectionne': destinataire_preselectionne
    }
    
    return render(request, 'tutorat/messagerie_nouvelle.html', context)