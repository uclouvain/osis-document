from django.core.management.base import BaseCommand
from django.db import transaction

from maintenance_check.models import ReclaimSpaceCheckRun
from maintenance_check.tasks.reclaim_space_check import run_reclaim_space_check


class Command(BaseCommand):
    help = "Analyse du système de fichier/db afin de trouver des fichiers orphelins."

    def add_arguments(self, parser):
        parser.add_argument("--uploaddir", required=True, help="Chemin du dossier d'upload")
        parser.add_argument("--safetymargin", type=int, default=60, help="Marge de sécurité en minutes")

    def handle(self, *args, **options):
        check_run = ReclaimSpaceCheckRun.objects.create(
            uploaddir=options['uploaddir'],
            safetymargin=options['safetymargin']
        )
        transaction.on_commit(
            lambda : run_reclaim_space_check.delay(check_run .id)
        )
        self.stdout.write(self.style.SUCCESS(f"Analyse planifiée (id={check_run.id})"))
