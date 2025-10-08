import contextlib
import logging
import traceback
from functools import partialmethod

from celery import shared_task
from django.utils import timezone

from maintenance_check.models import ReclaimSpaceCheckRun
from maintenance_check.scripts.orphan_finder import OrphanFilesFinder
from maintenance_check.tasks.utils import ReclaimSpaceCheckTask

logger = logging.getLogger('maintenance')


@shared_task(bind=True, base=ReclaimSpaceCheckTask)
def run_reclaim_space_check(self, check_run_id: int):
    """
    Tâche Celery pour exécuter la vérification de récupération d'espace disque
    """
    try:
        check_run = ReclaimSpaceCheckRun.objects.get(id=check_run_id)
        check_run.status = ReclaimSpaceCheckRun.TaskState.PROCESSING.name
        check_run.task_id = self.request.id
        check_run.save()
        self.update_progress(
            task_id=check_run_id,
            percentage=0,
            info={
                'description' : "Initialisation de l'analyse..."
            }
        )

        from django.db import connection
        db_config = connection.get_connection_params()
        self.update_progress(
            task_id=check_run_id,
            percentage=5,
            info={
                'description': "Récupération des informations de connexion à la base de données..."
            }
        )

        self.update_progress(
            task_id=check_run_id,
            percentage=10,
            info={
                'description': "Initialisation de la recherche de fichier orphelins...",
                'orphan_files_finder_params' : {
                    'upload_dir': check_run.upload_dir,
                    'safety_margin_minutes': check_run.safety_margin_minutes
                }
            }
        )

        progress_callback = partialmethod(self.update_progress, task_id=check_run_id)
        finder = OrphanFilesFinder(
            upload_dir=check_run.upload_dir,
            db_config=db_config,
            safety_margin_minutes=check_run.safety_margin_minutes,
            progress_callback=progress_callback,
        )
        results = finder.run_analysis_with_progress()
        self.update_progress(
            task_id=check_run_id,
            percentage=95,
            info={
                'description': "Finalisation du rapport..."
            }
        )

        # Mise à jour des résultats
        check_run.status = ReclaimSpaceCheckRun.TaskState.DONE.name
        check_run.completed_at = timezone.now()
        check_run.total_db_files = results['db_files_count']
        check_run.total_disk_files = results['disk_files_count']
        check_run.total_orphan_files = results['orphan_files_count']
        check_run.total_orphan_size_bytes = results['total_orphan_size_bytes']
        check_run.detailed_report = results['detailed_report']
        check_run.save()

        self.update_progress(
            task_id=check_run_id,
            percentage=100,
            info={
                'description': "Analyse terminée avec succès !"
            }
        )
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
        with contextlib.suppress(Exception):
            check_run = ReclaimSpaceCheckRun.objects.get(id=check_run_id)
            check_run.status = ReclaimSpaceCheckRun.TaskState.ERROR.name
            check_run.completed_at = timezone.now()
            check_run.error_message = str(e)
            check_run.save()
        raise
