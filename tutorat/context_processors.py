from django.utils import timezone
from datetime import timedelta
from .models import Message, Sujet, Reponse

def notifications(request):
    """
    Context processor pour afficher les notifications dans toute l'application
    """
    notifications_data = {
        'nb_messages_non_lus': 0,
        'nb_nouveaux_sujets': 0,
    }
    
    if request.user.is_authenticated:
        # Compter les messages non lus
        notifications_data['nb_messages_non_lus'] = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        
        # Compter les nouveaux sujets + nouvelles réponses sur MES sujets
        nb_nouveaux_sujets = 0
        nb_nouvelles_reponses = 0
        
        if request.user.derniere_visite_forum:
            # Nouveaux sujets depuis la dernière visite
            nb_nouveaux_sujets = Sujet.objects.filter(
                date_creation__gt=request.user.derniere_visite_forum
            ).exclude(auteur=request.user).count()
            
            # Nouvelles réponses sur MES sujets depuis la dernière visite
            nb_nouvelles_reponses = Reponse.objects.filter(
                sujet__auteur=request.user,  # Sur MES sujets
                date_creation__gt=request.user.derniere_visite_forum
            ).exclude(auteur=request.user).count()  # Pas mes propres réponses
        else:
            # Première visite, compter tous les sujets récents (24h)
            il_y_a_24h = timezone.now() - timedelta(days=1)
            nb_nouveaux_sujets = Sujet.objects.filter(
                date_creation__gte=il_y_a_24h
            ).exclude(auteur=request.user).count()
            
            # Réponses récentes sur mes sujets (24h)
            nb_nouvelles_reponses = Reponse.objects.filter(
                sujet__auteur=request.user,
                date_creation__gte=il_y_a_24h
            ).exclude(auteur=request.user).count()
        
        # Total des notifications forum = nouveaux sujets + nouvelles réponses sur mes sujets
        notifications_data['nb_nouveaux_sujets'] = nb_nouveaux_sujets + nb_nouvelles_reponses
    
    return notifications_data