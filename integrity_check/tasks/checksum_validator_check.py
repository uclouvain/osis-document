from celery import shared_task


@shared_task(bind=True)
def run_checksum_validator_check(self, check_run_id: int):
    pass
