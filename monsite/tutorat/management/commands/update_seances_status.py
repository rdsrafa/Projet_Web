"""
Commande Django pour mettre à jour automatiquement le statut des séances
À exécuter régulièrement avec un cron job ou task scheduler

Usage: python manage.py update_seances_status
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from tutorat.models import Seance


class Command(BaseCommand):
    help = 'Met à jour automatiquement le statut des séances (PREVUE, EN_COURS, TERMINEE)'

    def handle(self, *args, **options):
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        updated_count = 0
        
        # Récupérer toutes les séances prévues ou en cours
        seances = Seance.objects.filter(statut__in=['PREVUE', 'EN_COURS'])
        
        for seance in seances:
            old_statut = seance.statut
            
            # Séance passée → TERMINEE
            if seance.date < today:
                seance.statut = 'TERMINEE'
            
            # Séance d'aujourd'hui
            elif seance.date == today:
                # Séance terminée (heure de fin dépassée)
                if current_time > seance.heure_fin:
                    seance.statut = 'TERMINEE'
                
                # Séance en cours
                elif seance.heure_debut <= current_time <= seance.heure_fin:
                    seance.statut = 'EN_COURS'
                
                # Séance à venir aujourd'hui
                else:
                    seance.statut = 'PREVUE'
            
            # Séance future → PREVUE
            else:
                seance.statut = 'PREVUE'
            
            # Sauvegarder si le statut a changé
            if old_statut != seance.statut:
                seance.save(update_fields=['statut', 'updated_at'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Séance "{seance.titre}" ({seance.date}) : {old_statut} → {seance.statut}'
                    )
                )
        
        if updated_count == 0:
            self.stdout.write(self.style.WARNING('Aucune séance à mettre à jour.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✓ {updated_count} séance(s) mise(s) à jour avec succès!')
            )