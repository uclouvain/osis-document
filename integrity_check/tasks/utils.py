import contextlib

from celery import Task
from django.utils import timezone

from integrity_check.models import ReclaimSpaceCheckRun


class ReclaimSpaceCheckTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        with contextlib.suppress(ReclaimSpaceCheckRun.DoesNotExist):
            task_obj = ReclaimSpaceCheckRun.objects.get(task_id=task_id)
            task_obj.status = ReclaimSpaceCheckRun.TaskState.DONE.name
            task_obj.completed_at = timezone.now()
            task_obj.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        with contextlib.suppress(ReclaimSpaceCheckRun.DoesNotExist):
            task_obj = ReclaimSpaceCheckRun.objects.get(task_id=task_id)
            task_obj.status = ReclaimSpaceCheckRun.TaskState.ERROR.name
            task_obj.error_message = str(exc)
            task_obj.completed_at = timezone.now()
            task_obj.save()

    def update_progress(
        self,
        task_id: str,
        percentage: int,
        info: dict = None,
    ):
        with contextlib.suppress(ReclaimSpaceCheckRun.DoesNotExist):
            task_obj = ReclaimSpaceCheckRun.objects.get(task_id=task_id)
            task_obj.progress_percentage = percentage
            task_obj.status = ReclaimSpaceCheckRun.TaskState.PROCESSING.name if percentage < 100 else \
                ReclaimSpaceCheckRun.TaskState.DONE.name

            if info:
                current_info = task_obj.progress_info or {}
                current_info.update(info)
                task_obj.progress_info = current_info

            task_obj.save()
