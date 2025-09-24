import logging
import traceback

from celery import shared_task
from celery_progress.backend import ProgressRecorder
from django.utils import timezone

from .models import ReclaimSpaceCheckRun
from .orphan_finder import DjangoOrphanFilesFinder
from .scripts.orphan_finder import OrphanFilesFinder

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_reclaim_space_check(self, check_run_id):
    """
    Tâche Celery pour exécuter la vérification de récupération d'espace disque
    """
    progress_recorder = ProgressRecorder(self)

    try:
        # Récupération de l'instance ReclaimSpaceCheckRun
        check_run = ReclaimSpaceCheckRun.objects.get(id=check_run_id)
        check_run.status = 'running'
        check_run.task_id = self.request.id
        check_run.save()

        progress_recorder.set_progress(0, 100, description="Initialisation de l'analyse...")

        # Configuration de la base de données depuis Django
        from django.db import connection
        db_config = connection.get_connection_params()

        progress_recorder.set_progress(5, 100, description="Connexion à la base de données...")

        # Initialisation du finder adapté pour Django
        finder = OrphanFilesFinder(
            upload_dir=check_run.upload_dir,
            db_config=db_config,
            safety_margin_minutes=check_run.safety_margin_minutes,
            progress_callback=progress_recorder
        )

        progress_recorder.set_progress(10, 100, description="Récupération des fichiers de la base de données...")

        # Exécution de l'analyse complète
        results = finder.run_analysis_with_progress()

        progress_recorder.set_progress(95, 100, description="Finalisation du rapport...")

        # Mise à jour des résultats
        check_run.status = 'completed'
        check_run.completed_at = timezone.now()
        check_run.total_db_files = results['db_files_count']
        check_run.total_disk_files = results['disk_files_count']
        check_run.total_orphan_files = results['orphan_files_count']
        check_run.total_orphan_size_bytes = results['total_orphan_size_bytes']
        check_run.detailed_report = results['detailed_report']
        check_run.save()

        progress_recorder.set_progress(100, 100, description="Analyse terminée avec succès!")

        return {
            'status': 'success',
            'db_files': results['db_files_count'],
            'disk_files': results['disk_files_count'],
            'orphan_files': results['orphan_files_count'],
            'total_size_gb': results['total_orphan_size_bytes'] / (1024 ** 3) if results[
                'total_orphan_size_bytes'] else 0
        }

    except Exception as e:
        logger.error(f"Erreur lors de la vérification de récupération d'espace disque: {str(e)}")
        logger.error(traceback.format_exc())

        # Mise à jour du statut d'erreur
        try:
            check_run = ReclaimSpaceCheckRun.objects.get(id=check_run_id)
            check_run.status = 'failed'
            check_run.completed_at = timezone.now()
            check_run.error_message = str(e)
            check_run.save()
        except:
            pass

        progress_recorder.set_progress(100, 100, description=f"Erreur: {str(e)}")
        raise