from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from .forms import InscriptionForm, ConnexionForm, SeanceForm, SujetForumForm, ReponseForumForm, MessageForm
from .models import Seance, Inscription, Matiere, User, SujetForum, ReponseForum, Conversation, Message as MessageModel, Notification
from datetime import datetime


def accueil(request):
    """
    Page d'accueil
    """
    return render(request, 'tutorat/accueil.html')


def inscription(request):
    """
    Vue pour l'inscription des utilisateurs
    """
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.')
            return redirect('connexion')
        else:
            messages.error(request, 'Erreur lors de l\'inscription. Vérifiez les informations.')
    else:
        form = InscriptionForm()
    
    return render(request, 'tutorat/inscription.html', {'form': form})


def connexion(request):
    """
    Vue pour la connexion des utilisateurs
    """
    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue {user.username} !')
                
                # Redirection selon le rôle
                if user.role == 'ADMIN':
                    return redirect('dashboard_admin')
                elif user.role == 'TUTEUR':
                    return redirect('dashboard_tuteur')
                else:  # ETUDIANT
                    return redirect('dashboard_etudiant')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    else:
        form = ConnexionForm()
    
    return render(request, 'tutorat/connexion.html', {'form': form})


@login_required
def deconnexion(request):
    """
    Vue pour la déconnexion
    """
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('accueil')


@login_required
def dashboard_etudiant(request):
    """
    Tableau de bord pour les étudiants
    """
    mes_inscriptions = Inscription.objects.filter(
        etudiant=request.user,
        statut='CONFIRMEE'
    ).select_related('seance', 'seance__matiere', 'seance__tuteur')
    
    seances_disponibles = Seance.objects.filter(
        statut='PREVUE',
        date__gte=datetime.now().date()
    ).exclude(
        inscriptions__etudiant=request.user,
        inscriptions__statut='CONFIRMEE'
    ).select_related('matiere', 'tuteur')[:5]
    
    context = {
        'mes_inscriptions': mes_inscriptions,
        'seances_disponibles': seances_disponibles,
        'total_inscriptions': mes_inscriptions.count(),
    }
    return render(request, 'tutorat/dashboard_etudiant.html', context)


@login_required
def dashboard_tuteur(request):
    """
    Tableau de bord pour les tuteurs
    """
    mes_seances = Seance.objects.filter(
        tuteur=request.user
    ).select_related('matiere').prefetch_related('inscriptions')
    
    seances_a_venir = mes_seances.filter(
        statut='PREVUE',
        date__gte=datetime.now().date()
    )
    
    total_etudiants = Inscription.objects.filter(
        seance__tuteur=request.user,
        statut='CONFIRMEE'
    ).values('etudiant').distinct().count()
    
    context = {
        'mes_seances': mes_seances,
        'seances_a_venir': seances_a_venir,
        'total_seances': mes_seances.count(),
        'total_etudiants': total_etudiants,
    }
    return render(request, 'tutorat/dashboard_tuteur.html', context)


@login_required
def dashboard_admin(request):
    """
    Tableau de bord pour les administrateurs
    """
    total_users = User.objects.count()
    total_seances = Seance.objects.count()
    total_inscriptions = Inscription.objects.filter(statut='CONFIRMEE').count()
    total_matieres = Matiere.objects.count()
    
    seances_recentes = Seance.objects.select_related('tuteur', 'matiere').order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_seances': total_seances,
        'total_inscriptions': total_inscriptions,
        'total_matieres': total_matieres,
        'seances_recentes': seances_recentes,
    }
    return render(request, 'tutorat/dashboard_admin.html', context)


# ========== GESTION DES SÉANCES ==========

@login_required
def seance_create(request):
    """
    Créer une nouvelle séance (Tuteur uniquement)
    """
    if request.user.role != 'TUTEUR':
        messages.error(request, "Seuls les tuteurs peuvent créer des séances.")
        return redirect('accueil')
    
    if request.method == 'POST':
        form = SeanceForm(request.POST)
        if form.is_valid():
            seance = form.save(commit=False)
            seance.tuteur = request.user
            seance.save()
            messages.success(request, 'Séance créée avec succès !')
            return redirect('seance_list')
        else:
            messages.error(request, 'Erreur lors de la création de la séance.')
    else:
        form = SeanceForm()
    
    return render(request, 'tutorat/seance_form.html', {'form': form, 'action': 'Créer'})


@login_required
def seance_list(request):
    """
    Liste des séances disponibles
    """
    if request.user.role == 'TUTEUR':
        seances = Seance.objects.filter(tuteur=request.user).select_related('matiere')
    else:
        seances = Seance.objects.filter(
            statut='PREVUE',
            date__gte=datetime.now().date()
        ).select_related('matiere', 'tuteur')
    
    return render(request, 'tutorat/seance_list.html', {'seances': seances})


@login_required
def seance_detail(request, pk):
    """
    Détails d'une séance
    """
    seance = get_object_or_404(Seance.objects.select_related('matiere', 'tuteur'), pk=pk)
    inscriptions = seance.inscriptions.filter(statut='CONFIRMEE').select_related('etudiant')
    
    est_inscrit = False
    if request.user.role == 'ETUDIANT':
        est_inscrit = seance.inscriptions.filter(
            etudiant=request.user,
            statut='CONFIRMEE'
        ).exists()
    
    context = {
        'seance': seance,
        'inscriptions': inscriptions,
        'est_inscrit': est_inscrit,
        'peut_modifier': request.user == seance.tuteur or request.user.role == 'ADMIN',
    }
    return render(request, 'tutorat/seance_detail.html', context)


@login_required
def seance_update(request, pk):
    """
    Modifier une séance (Tuteur propriétaire ou Admin)
    """
    seance = get_object_or_404(Seance, pk=pk)
    
    if request.user != seance.tuteur and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission de modifier cette séance.")
        return redirect('seance_detail', pk=pk)
    
    if request.method == 'POST':
        form = SeanceForm(request.POST, instance=seance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Séance modifiée avec succès !')
            return redirect('seance_detail', pk=pk)
    else:
        form = SeanceForm(instance=seance)
    
    return render(request, 'tutorat/seance_form.html', {'form': form, 'action': 'Modifier', 'seance': seance})


@login_required
def seance_delete(request, pk):
    """
    Supprimer une séance (Tuteur propriétaire ou Admin)
    """
    seance = get_object_or_404(Seance, pk=pk)
    
    if request.user != seance.tuteur and request.user.role != 'ADMIN':
        messages.error(request, "Vous n'avez pas la permission de supprimer cette séance.")
        return redirect('seance_detail', pk=pk)
    
    if request.method == 'POST':
        seance.delete()
        messages.success(request, 'Séance supprimée avec succès !')
        return redirect('seance_list')
    
    return render(request, 'tutorat/seance_confirm_delete.html', {'seance': seance})


# ========== GESTION DES INSCRIPTIONS ==========

@login_required
def inscription_create(request, seance_pk):
    """
    S'inscrire à une séance (Étudiant uniquement)
    """
    if request.user.role != 'ETUDIANT':
        messages.error(request, "Seuls les étudiants peuvent s'inscrire aux séances.")
        return redirect('seance_detail', pk=seance_pk)
    
    seance = get_object_or_404(Seance, pk=seance_pk)
    
    if not seance.peut_s_inscrire(request.user):
        messages.error(request, "Vous ne pouvez pas vous inscrire à cette séance (complète ou déjà inscrit).")
        return redirect('seance_detail', pk=seance_pk)
    
    Inscription.objects.create(
        etudiant=request.user,
        seance=seance,
        statut='CONFIRMEE'
    )
    
    messages.success(request, f'Vous êtes inscrit à la séance "{seance.titre}" !')
    return redirect('seance_detail', pk=seance_pk)


@login_required
def inscription_delete(request, pk):
    """
    Se désinscrire d'une séance
    """
    inscription = get_object_or_404(Inscription, pk=pk, etudiant=request.user)
    seance_pk = inscription.seance.pk
    
    inscription.delete()
    messages.success(request, 'Vous êtes désinscrit de cette séance.')
    return redirect('seance_detail', pk=seance_pk)


# ========== API POUR LE CALENDRIER ==========

@login_required
def seances_json(request):
    """
    Retourne les séances au format JSON pour le calendrier
    """
    if request.user.role == 'TUTEUR':
        seances = Seance.objects.filter(tuteur=request.user)
    elif request.user.role == 'ETUDIANT':
        seances = Seance.objects.filter(statut='PREVUE')
    else:
        seances = Seance.objects.all()
    
    events = []
    for seance in seances.select_related('matiere'):
        events.append({
            'id': seance.id,
            'title': f"{seance.titre} ({seance.matiere.code})",
            'start': f"{seance.date}T{seance.heure_debut}",
            'end': f"{seance.date}T{seance.heure_fin}",
            'url': f"/seance/{seance.id}/",
            'backgroundColor': '#0d6efd' if seance.statut == 'PREVUE' else '#6c757d',
        })
    
    return JsonResponse(events, safe=False)


@login_required
def calendrier(request):
    """
    Page du calendrier interactif
    """
    return render(request, 'tutorat/calendrier.html')


# ========== FORUM ==========

@login_required
def forum_accueil(request):
    """
    Page d'accueil du forum avec liste des sujets
    """
    matiere_id = request.GET.get('matiere')
    recherche = request.GET.get('q')
    
    sujets = SujetForum.objects.select_related('auteur', 'matiere').annotate(
        nb_reponses=Count('reponses')
    )
    
    if matiere_id:
        sujets = sujets.filter(matiere_id=matiere_id)
    
    if recherche:
        sujets = sujets.filter(
            Q(titre__icontains=recherche) | Q(contenu__icontains=recherche)
        )
    
    matieres = Matiere.objects.all()
    
    context = {
        'sujets': sujets,
        'matieres': matieres,
        'matiere_selectionnee': matiere_id,
        'recherche': recherche,
    }
    return render(request, 'tutorat/forum_accueil.html', context)


@login_required
def forum_sujet_create(request):
    """
    Créer un nouveau sujet sur le forum
    """
    if request.method == 'POST':
        form = SujetForumForm(request.POST)
        if form.is_valid():
            sujet = form.save(commit=False)
            sujet.auteur = request.user
            sujet.save()
            messages.success(request, 'Votre sujet a été créé avec succès !')
            return redirect('forum_sujet_detail', pk=sujet.pk)
    else:
        form = SujetForumForm()
    
    return render(request, 'tutorat/forum_sujet_form.html', {'form': form})


@login_required
def forum_sujet_detail(request, pk):
    """
    Afficher un sujet du forum avec ses réponses
    """
    sujet = get_object_or_404(SujetForum.objects.select_related('auteur', 'matiere'), pk=pk)
    
    # Incrémenter le nombre de vues
    sujet.vues += 1
    sujet.save(update_fields=['vues'])
    
    reponses = sujet.reponses.select_related('auteur').prefetch_related('likes')
    
    if request.method == 'POST':
        form = ReponseForumForm(request.POST)
        if form.is_valid():
            reponse = form.save(commit=False)
            reponse.sujet = sujet
            reponse.auteur = request.user
            reponse.save()
            
            # Créer une notification pour l'auteur du sujet
            if sujet.auteur != request.user:
                Notification.objects.create(
                    destinataire=sujet.auteur,
                    type='REPONSE_FORUM',
                    titre='Nouvelle réponse à votre sujet',
                    message=f'{request.user.first_name or request.user.username} a répondu à votre sujet "{sujet.titre}"',
                    lien=f'/forum/sujet/{sujet.pk}/'
                )
            
            messages.success(request, 'Votre réponse a été ajoutée !')
            return redirect('forum_sujet_detail', pk=pk)
    else:
        form = ReponseForumForm()
    
    context = {
        'sujet': sujet,
        'reponses': reponses,
        'form': form,
    }
    return render(request, 'tutorat/forum_sujet_detail.html', context)


@login_required
def forum_reponse_like(request, pk):
    """
    Liker/Unliker une réponse
    """
    reponse = get_object_or_404(ReponseForum, pk=pk)
    
    if request.user in reponse.likes.all():
        reponse.likes.remove(request.user)
        action = 'unliked'
    else:
        reponse.likes.add(request.user)
        action = 'liked'
    
    return JsonResponse({
        'action': action,
        'likes_count': reponse.nombre_likes()
    })


@login_required
def forum_reponse_meilleure(request, pk):
    """
    Marquer une réponse comme meilleure réponse (auteur du sujet uniquement)
    """
    reponse = get_object_or_404(ReponseForum, pk=pk)
    
    if request.user == reponse.sujet.auteur:
        # Retirer la meilleure réponse actuelle
        ReponseForum.objects.filter(sujet=reponse.sujet, meilleure_reponse=True).update(meilleure_reponse=False)
        
        # Marquer cette réponse comme meilleure
        reponse.meilleure_reponse = True
        reponse.save()
        
        # Marquer le sujet comme résolu
        reponse.sujet.resolu = True
        reponse.sujet.save()
        
        messages.success(request, 'Réponse marquée comme meilleure réponse !')
    else:
        messages.error(request, "Seul l'auteur du sujet peut choisir la meilleure réponse.")
    
    return redirect('forum_sujet_detail', pk=reponse.sujet.pk)


# ========== MESSAGERIE ==========

@login_required
def messagerie_liste(request):
    """
    Liste des conversations
    """
    conversations = request.user.conversations.prefetch_related('participants', 'messages').order_by('-updated_at')
    
    # Ajouter le nombre de messages non lus pour chaque conversation
    for conv in conversations:
        conv.non_lus = conv.messages_non_lus(request.user)
        conv.autre_participant = conv.participants.exclude(id=request.user.id).first()
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'tutorat/messagerie_liste.html', context)


@login_required
def messagerie_conversation(request, pk):
    """
    Afficher une conversation
    """
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('participants', 'messages__auteur'),
        pk=pk,
        participants=request.user
    )
    
    # Marquer les messages comme lus
    conversation.messages.exclude(auteur=request.user).update(lu=True)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.auteur = request.user
            message.save()
            
            # Mettre à jour la conversation
            conversation.updated_at = datetime.now()
            conversation.save()
            
            # Créer une notification pour les autres participants
            for participant in conversation.participants.exclude(id=request.user.id):
                Notification.objects.create(
                    destinataire=participant,
                    type='MESSAGE',
                    titre='Nouveau message',
                    message=f'{request.user.first_name or request.user.username} vous a envoyé un message',
                    lien=f'/messagerie/conversation/{conversation.pk}/'
                )
            
            return redirect('messagerie_conversation', pk=pk)
    else:
        form = MessageForm()
    
    autre_participant = conversation.participants.exclude(id=request.user.id).first()
    
    context = {
        'conversation': conversation,
        'messages': conversation.messages.all(),
        'form': form,
        'autre_participant': autre_participant,
    }
    return render(request, 'tutorat/messagerie_conversation.html', context)


@login_required
def messagerie_nouvelle(request, user_id):
    """
    Démarrer une nouvelle conversation avec un utilisateur
    """
    destinataire = get_object_or_404(User, pk=user_id)
    
    # Vérifier si une conversation existe déjà
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=destinataire
    ).first()
    
    if conversation:
        return redirect('messagerie_conversation', pk=conversation.pk)
    
    # Créer une nouvelle conversation
    conversation = Conversation.objects.create()
    conversation.participants.add(request.user, destinataire)
    
    return redirect('messagerie_conversation', pk=conversation.pk)


# ========== NOTIFICATIONS ==========

@login_required
def notifications_liste(request):
    """
    Liste des notifications
    """
    notifications = request.user.notifications.order_by('-created_at')[:20]
    
    # Marquer comme lues
    notifications.update(lue=True)
    
    return render(request, 'tutorat/notifications.html', {'notifications': notifications})


@login_required
def notifications_count(request):
    """
    Nombre de notifications non lues (API JSON)
    """
    count = request.user.notifications.filter(lue=False).count()
    return JsonResponse({'count': count})