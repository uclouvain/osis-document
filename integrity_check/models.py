from django.db import models


class MaintenanceRun(models.Model):
    """
    Classe abstraite de base pour les tâches de maintenance
    """
    class TaskState(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        PROCESSING = 'PROCESSING', 'En cours'
        DONE = 'DONE', 'Terminé'
        ERROR = 'ERROR', 'En erreur'

    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=20,
        choices=TaskState.choices,
        default=TaskState.PENDING.name
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Progression
    current_step = models.CharField(max_length=100, blank=True)
    progress_percentage = models.IntegerField(default=0)
    progress_info = models.JSONField(default=dict)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return f"Tâche {self.id} - {self.get_status_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ReclaimSpaceCheckRun(MaintenanceRun):
    """
    Modèle pour les vérifications de récupération d'espace disque
    """
    # Paramètres de la tâche
    upload_dir = models.CharField(max_length=500)
    safety_margin_minutes = models.IntegerField(default=60)

    # Résultats
    total_db_files = models.IntegerField(null=True, blank=True)
    total_disk_files = models.IntegerField(null=True, blank=True)
    total_orphan_files = models.IntegerField(null=True, blank=True)
    total_orphan_size_bytes = models.BigIntegerField(null=True, blank=True)
    detailed_report = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Vérification de récupération d'espace disque"
        verbose_name_plural = "Vérifications de récupération d'espace disque"

    @property
    def total_orphan_size_mb(self):
        if self.total_orphan_size_bytes:
            return round(self.total_orphan_size_bytes / (1024 * 1024), 2)
        return 0

    @property
    def total_orphan_size_gb(self):
        if self.total_orphan_size_bytes:
            return round(self.total_orphan_size_bytes / (1024 * 1024 * 1024), 2)
        return 0


class ChecksumValidatorRun(MaintenanceRun):
    """
    Modèle pour les vérifications des hashs de fichier
    """
    # Paramètres
    upload_dir = models.CharField(max_length=500)
    from_date = models.DateTimeField(null=True, blank=True)
    to_date = models.DateTimeField(null=True, blank=True)

    # Résultats
    total_db_files = models.IntegerField(null=True, blank=True)
    total_not_found_files = models.IntegerField(null=True, blank=True)
    total_hash_mismatch_files = models.IntegerField(null=True, blank=True)
    detailed_report = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Validation de hash"
        verbose_name_plural = "Validations de hash"

    @property
    def total_invalid_files(self):
        not_found = self.total_not_found_files or 0
        mismatch = self.total_hash_mismatch_files or 0
        return not_found + mismatch
