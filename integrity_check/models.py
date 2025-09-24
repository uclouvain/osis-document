from django.db import models


class ReclaimSpaceCheckRun(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('running', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    ]

    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Paramètres d'exécution
    upload_dir = models.CharField(max_length=500)
    safety_margin_minutes = models.IntegerField(default=60)

    # Résultats
    total_db_files = models.IntegerField(null=True, blank=True)
    total_disk_files = models.IntegerField(null=True, blank=True)
    total_orphan_files = models.IntegerField(null=True, blank=True)
    total_orphan_size_bytes = models.BigIntegerField(null=True, blank=True)

    # Rapport détaillé (JSON)
    detailed_report = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Vérification de récupération d'espace disque"
        verbose_name_plural = "Vérifications de récupération d'espace disque"

    def __str__(self):
        return f"Contrôle {self.id} - {self.get_status_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

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
