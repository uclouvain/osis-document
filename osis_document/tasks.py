# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from datetime import timedelta
from celery.schedules import crontab

from django.conf import settings
from django.utils.timezone import now

try:
    from document.celery import app
except ImportError:
    from backoffice.celery import app
from osis_document.enums import FileStatus, PostProcessingStatus
from osis_document.models import Upload, Token, PostProcessAsync
from osis_document.utils import post_process


@app.task
def cleanup_old_uploads():
    qs = Upload.objects.filter(
        status=FileStatus.REQUESTED.name,
        uploaded_at__lte=now() - timedelta(seconds=settings.OSIS_DOCUMENT_TEMP_UPLOAD_MAX_AGE),
    )
    qs.delete()
    Token.objects.filter(
        expires_at__lte=now(),
    ).delete()


@app.task
def make_pending_async_post_processing():
    qs = PostProcessAsync.objects.filter(
        status=PostProcessingStatus.PENDING.name
    )
    for post_process_async in qs:
        base_uuids_list = [uuid for uuid in post_process_async.data['base_input']]
        intermediary_uuids_list = []
        for action in post_process_async.data["post_process_actions"]:
            try:
                output_data = post_process(
                    uuid_list=intermediary_uuids_list or base_uuids_list,
                    post_process_actions=[action],
                    post_process_params=post_process_async.data["post_process_params"],
                )
                post_process_async.results[action]['upload_objects'] = output_data[action]['output']['upload_objects']
                post_process_async.results[action]['post_processing_objects'] = output_data[action]['output']['post_processing_objects']
                post_process_async.results[action]['status'] = PostProcessingStatus.DONE.name
                post_process_async.save()
                intermediary_uuids_list = output_data[action]['output']['upload_objects']
            except Exception as e:
                if hasattr(e, 'message'):
                    post_process_async.results[action]['errors'] = {'messages': e.messages,
                                                                    'params': str(e.params['value'])}
                else:
                    post_process_async.results[action]['errors'] = {'messages': e.args or e.default_detail}
                post_process_async.results[action]['status'] = PostProcessingStatus.FAILED.name
                post_process_async.save()
                break
        post_process_async.status = PostProcessingStatus.DONE.name
        for action in post_process_async.data["post_process_actions"]:
            if post_process_async.results[action]['status'] == PostProcessingStatus.FAILED.name:
                post_process_async.status = PostProcessingStatus.FAILED.name
        post_process_async.save()
