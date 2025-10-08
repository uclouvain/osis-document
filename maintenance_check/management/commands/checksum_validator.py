from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from maintenance_check.models import ChecksumValidatorRun
from maintenance_check.tasks.checksum_validator_check import run_checksum_validator_check


class Command(BaseCommand):
    help = "Contrôle l'intégrité (SHA256) et existance des fichiers"

    def add_arguments(self, parser):
        parser.add_argument("--uploaddir", required=True, help="Chemin du dossier d'upload")
        parser.add_argument("--fromdate", type=str, default=None,
                            help="Date de début au format ISO (YYYY-MM-DDTHH:MM, optionnel)")
        parser.add_argument("--todate", type=str, default=None,
                            help="Date de fin au format ISO (YYYY-MM-DDTHH:MM, optionnel)")

    def handle(self, *args, **options):
        fromdate = datetime.fromisoformat(options['fromdate']) if options['fromdate'] else None
        todate = datetime.fromisoformat(options['todate']) if options['todate'] else None

        check_run = ChecksumValidatorRun.objects.create(
            uploaddir=options['uploaddir'],
            fromdate=fromdate,
            todate=todate,
        )
        transaction.on_commit(
            lambda: run_checksum_validator_check.delay(check_run.id)
        )
        self.stdout.write(self.style.SUCCESS(f"Analyse de hash planifiée (id={check_run.id})"))
