from django.contrib import admin
from .models import ReclaimSpaceCheckRun, ChecksumValidatorRun
from .tasks.reclaim_space_check import run_reclaim_space_check
from .tasks.checksum_validator_check import run_checksum_validator_check

@admin.register(ReclaimSpaceCheckRun)
class ReclaimSpaceCheckRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaddir', 'safetymarginminutes', 'status', 'progresspercentage', 'createdat', 'completedat')
    list_filter = ('status',)
    search_fields = ('uploaddir',)
    actions = ['launch_reclaim_task']

    @admin.action(description="Lancer ou relancer la tâche de vérification espace disque")
    def launch_reclaim_task(self, request, queryset):
        launched = 0
        for obj in queryset:
            run_reclaim_space_check.delay(obj.id)
            launched += 1
        self.message_user(request, f"{launched} tâche(s) (re)lancées.")


@admin.register(ChecksumValidatorRun)
class ChecksumValidatorRunAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaddir', 'fromdate', 'todate', 'status', 'progresspercentage', 'createdat', 'completedat')
    list_filter = ('status',)
    search_fields = ('uploaddir',)
    actions = ['launch_validator_task']

    @admin.action(description="Lancer ou relancer la tâche de validation hash")
    def launch_validator_task(self, request, queryset):
        launched = 0
        for obj in queryset:
            run_checksum_validator_check.delay(obj.id)
            launched += 1
        self.message_user(request, f"{launched} tâche(s) (re)lancées.")
