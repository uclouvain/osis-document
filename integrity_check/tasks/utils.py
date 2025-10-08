import contextlib
from abc import ABC, abstractmethod
from typing import Type

from celery import Task
from django.db import models
from django.utils import timezone

from integrity_check.models import ReclaimSpaceCheckRun, ChecksumValidatorRun


class MaintenanceTask(Task, ABC):
    """
    Classe abstraite de base pour toutes les tâches de maintenance Celery
    Centralise la logique commune de gestion des états et du progrès
    """
    @property
    @abstractmethod
    def model_class(self) -> Type[models.Model]:
        pass

    def get_task_object(self, task_id: str) -> models.Model:
        return self.model_class.objects.get(task_id=task_id)

    def on_success(self, retval, task_id, args, kwargs):
        with contextlib.suppress(self.model_class.DoesNotExist):
            task_obj = self.get_task_object(task_id)
            task_obj.status = task_obj.TaskState.DONE.name
            task_obj.completed_at = timezone.now()
            task_obj.progress_percentage = 100
            task_obj.save(update_fields=['status', 'completed_at', 'progress_percentage'])

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        with contextlib.suppress(self.model_class.DoesNotExist):
            task_obj = self.get_task_object(task_id)
            task_obj.status = task_obj.TaskState.ERROR.name
            task_obj.completed_at = timezone.now()
            if hasattr(task_obj, 'error_message'):
                task_obj.error_message = str(exc)
                task_obj.save(update_fields=['status', 'completed_at', 'error_message'])
            else:
                task_obj.save(update_fields=['status', 'completed_at'])

    def update_progress(self, task_id: str, percentage: int, info: dict = None, step: str = None):
        task_obj = self.get_task_object(task_id)
        task_obj.progress_percentage = percentage

        if percentage >= 100:
            task_obj.status = task_obj.TaskState.DONE.name
            task_obj.completed_at = timezone.now()
        else:
            task_obj.status = task_obj.TaskState.PROCESSING.name

        if info:
            current_info = task_obj.progress_info or {}
            current_info.update(info)
            task_obj.progress_info = current_info

        if step:
            task_obj.current_step = step

        update_fields = ['progress_percentage', 'status', 'progress_info']
        if step:
            update_fields.append('current_step')
        if percentage >= 100:
            update_fields.append('completed_at')

        task_obj.save(update_fields=update_fields)

    def mark_as_processing(self, task_id: str, step: str = None):
        """Marque une tâche comme en cours de traitement"""
        task_obj = self.get_task_object(task_id)
        task_obj.status = task_obj.TaskState.PROCESSING.name
        update_fields = ['status']
        if step:
            task_obj.current_step = step
            update_fields.append('current_step')
        task_obj.save(update_fields=update_fields)


class ReclaimSpaceCheckTask(MaintenanceTask):
    """
    Tâche Celery pour les vérifications de récupération d'espace disque
    """

    @property
    def model_class(self) -> Type[ReclaimSpaceCheckRun]:
        return ReclaimSpaceCheckRun

    def update_space_info(self, task_id: str, db_files: int = None, disk_files: int = None,
                          orphan_files: int = None, orphan_size: int = None):
        """
        Met à jour les informations spécifiques à la récupération d'espace
        """
        with contextlib.suppress(self.model_class.DoesNotExist):
            task_obj = self.get_task_object(task_id)
            if task_obj:
                update_fields = []
                if db_files is not None:
                    task_obj.total_db_files = db_files
                    update_fields.append('total_db_files')
                if disk_files is not None:
                    task_obj.total_disk_files = disk_files
                    update_fields.append('total_disk_files')
                if orphan_files is not None:
                    task_obj.total_orphan_files = orphan_files
                    update_fields.append('total_orphan_files')
                if orphan_size is not None:
                    task_obj.total_orphan_size_bytes = orphan_size
                    update_fields.append('total_orphan_size_bytes')

                if update_fields:
                    task_obj.save(update_fields=update_fields)


class ChecksumValidatorCheckTask(MaintenanceTask):
    """
    Tâche Celery pour les vérifications de sommes de contrôle
    """

    @property
    def model_class(self) -> Type[ChecksumValidatorRun]:
        return ChecksumValidatorRun

    def update_validation_info(self, task_id: str, db_files: int = None,
                               not_found_files: int = None, hash_mismatch_files: int = None):
        """
        Met à jour les informations spécifiques à la validation des checksums
        """
        with contextlib.suppress(self.model_class.DoesNotExist):
            task_obj = self.get_task_object(task_id)
            if task_obj:
                update_fields = []
                if db_files is not None:
                    task_obj.total_db_files = db_files
                    update_fields.append('total_db_files')
                if not_found_files is not None:
                    task_obj.total_not_found_files = not_found_files
                    update_fields.append('total_not_found_files')
                if hash_mismatch_files is not None:
                    task_obj.total_hash_mismatch_files = hash_mismatch_files
                    update_fields.append('total_hash_mismatch_files')

                if update_fields:
                    task_obj.save(update_fields=update_fields)