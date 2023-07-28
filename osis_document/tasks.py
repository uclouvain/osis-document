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

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.timezone import now

try:
    from document.celery import app
except ImportError:
    from backoffice.celery import app
from osis_document.enums import FileStatus, PostProcessingStatus
from osis_document.exceptions import PostProcessingNotPending
from osis_document.models import Upload, Token, PostProcessingController
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
def make_one_pending_post_processing(uuid=None, post_processing_controller_object=None):
    if uuid:
        post_processing_controller = PostProcessingController.objects.select_for_update(skip_locked=True).get(uuid=uuid)
    elif post_processing_controller_object:
        post_processing_controller = post_processing_controller_object
    else:
        raise ValueError
    with transaction.atomic():
        current_processing_uuids = [uuid for uuid in post_processing_controller.data['base_input']]
        result_dict = {}
        if post_processing_controller.status == PostProcessingStatus.PENDING.name:
            for action in post_processing_controller.data["post_process_actions"]:
                try:
                    result_dict.setdefault(action, {'input': [], 'output': []})
                    output_data = post_process(
                        uuid_list=current_processing_uuids,
                        post_process_actions=[action],
                        post_process_params=post_processing_controller.data["post_process_params"],
                    )
                    post_processing_controller.results[action]['upload_objects'] = output_data[action]['output']['upload_objects']
                    post_processing_controller.results[action]['post_processing_objects'] = output_data[action]['output'][
                        'post_processing_objects']
                    post_processing_controller.results[action]['status'] = PostProcessingStatus.DONE.name
                    post_processing_controller.save()
                    result_dict[action]['input'] = current_processing_uuids
                    result_dict[action]['output'] = output_data[action]['output']['upload_objects']
                    current_processing_uuids = output_data[action]['output']['upload_objects']

                except ValidationError as e:
                    post_processing_controller.results[action]['errors'] = {
                        'messages': e.messages,
                        'params': str(e.params['value'])
                    }
                    post_processing_controller.results[action]['status'] = PostProcessingStatus.FAILED.name
                    post_processing_controller.save()
                    break
                except Exception as e:
                    post_processing_controller.results[action]['errors'] = {
                        'messages': e.args or e.default_detail
                    }
                    post_processing_controller.results[action]['status'] = PostProcessingStatus.FAILED.name
                    post_processing_controller.save()
                    break

            if any([post_processing_controller.results[item]['status'] == PostProcessingStatus.FAILED.name for item in
                    post_processing_controller.results]):
                post_processing_controller.status = PostProcessingStatus.FAILED.name
            else:
                post_processing_controller.status = PostProcessingStatus.DONE.name

            post_processing_controller.save()

            return result_dict
        else:
            raise PostProcessingNotPending


@app.task
def make_all_pending_async_post_processing():
    qs = PostProcessingController.objects.select_for_update(skip_locked=True).filter(
        status=PostProcessingStatus.PENDING.name
    )
    for post_process_async in qs:
        make_one_pending_post_processing(post_processing_controller_object=post_process_async)

