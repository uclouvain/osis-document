# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase, URLPatternsTestCase

from osis_document.enums import PostProcessingStatus, PostProcessingType, PostProcessingWanted
from osis_document.tests.factories import (
    ImageUploadFactory,
    CorrectPDFUploadFactory,
    TextDocumentUploadFactory,
    MergePostProcessingFactory,
    ConvertPostProcessingFactory,
    PendingPostProcessingAsyncFactory,
    DonePostProcessingAsyncFactory,
    FailedPostProcessingAsyncFactory,
)


@override_settings(OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class GetProgressAsyncPostProcessingViewTestCase(APITestCase, URLPatternsTestCase):
    from django.urls import path, include

    app_name = 'osis_document'
    urlpatterns = [
        path('', include('osis_document.urls', namespace="osis_document")),
    ]

    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}
        self.pdf = CorrectPDFUploadFactory()
        self.text = TextDocumentUploadFactory()
        self.img = ImageUploadFactory()
        self.base_input_object = [self.pdf.uuid, self.text.uuid, self.img.uuid]
        self.action_list = [PostProcessingType.CONVERT.name, PostProcessingType.MERGE.name]
        self.action_param_dict = {
            PostProcessingType.CONVERT.name: {},
            PostProcessingType.MERGE.name: {
                "output_filename": "a_test_merge_with_params_and_filename",
                "pages_dimension": "A4",
            },
        }
        self.convert_text = ConvertPostProcessingFactory()
        self.convert_text_output = CorrectPDFUploadFactory()
        self.convert_text.input_files.add(self.text)
        self.convert_text.output_files.add(self.convert_text_output)
        self.convert_img = ConvertPostProcessingFactory()
        self.convert_img_output = CorrectPDFUploadFactory()
        self.convert_img.input_files.add(self.img)
        self.convert_img.output_files.add(self.convert_img_output)

    def test_get_progress_of_PENDING_async_post_process(self):
        result_dict = {
            PostProcessingType.CONVERT.name: {
                "status": PostProcessingStatus.DONE.name,
                "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid],
            },
            PostProcessingType.MERGE.name: {
                "status": PostProcessingStatus.PENDING.name,
            },
        }
        async_post_process = PendingPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict,
        )

        request_data = {'pk': async_post_process.uuid, 'wanted_post_process': PostProcessingWanted.CONVERT.name}
        response = self.client.get(
            reverse('osis_document:get-progress-post-processing', kwargs={'pk': async_post_process.uuid}),
            data=request_data,
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data.get('progress'), 50.0)
        self.assertEqual(response.data.get('wanted_post_process_status'), PostProcessingStatus.DONE.name)

        request_data = {'pk': async_post_process.uuid, 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.get(
            reverse('osis_document:get-progress-post-processing', kwargs={'pk': async_post_process.uuid}),
            data=request_data,
        )
        self.assertEqual(response.data.get('wanted_post_process_status'), PostProcessingStatus.PENDING.name)

    def test_get_progress_of_DONE_async_post_process(self):
        merge = MergePostProcessingFactory()
        merge_output = CorrectPDFUploadFactory()
        merge.input_files.add(self.convert_text_output, self.convert_img_output)
        merge.output_files.add(merge_output)
        result_dict = {
            PostProcessingType.CONVERT.name: {
                "status": PostProcessingStatus.DONE.name,
                "upload_objects": [self.convert_img_output.uuid, self.convert_text_output.uuid],
                "post_processing_objects": [self.convert_img.uuid, self.convert_text.uuid],
            },
            PostProcessingType.MERGE.name: {
                "status": PostProcessingStatus.DONE.name,
                "upload_objects": [merge_output.uuid],
                "post_processing_objects": [merge.uuid],
            },
        }
        async_post_process = DonePostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict,
        )

        request_data = {'pk': async_post_process.uuid, 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.get(
            reverse('osis_document:get-progress-post-processing', kwargs={'pk': async_post_process.uuid}),
            data=request_data,
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data.get('progress'), 100.0)
        self.assertEqual(response.data.get('wanted_post_process_status'), PostProcessingStatus.DONE.name)

        request_data = {'pk': async_post_process.uuid}
        response = self.client.get(
            reverse('osis_document:get-progress-post-processing', kwargs={'pk': async_post_process.uuid}),
            data=request_data,
        )
        self.assertIsNone(response.data.get('wanted_post_process_status'))

    def test_get_progress_of_FAILED_async_post_process(self):
        result_dict = {
            PostProcessingType.CONVERT.name: {
                "status": PostProcessingStatus.DONE.name,
                "upload_objects": [self.convert_text_output.uuid, self.convert_img_output.uuid],
                "post_processing_objects": [self.convert_text.uuid, self.convert_img.uuid],
            },
            PostProcessingType.MERGE.name: {
                "errors": {
                    "params": "[<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>]",
                    "messages": [
                        "La valeur « [<Upload: Upload 'a_test_merge_with_params_and_filename.pdf'>] » n’est pas un UUID valide."
                    ],
                },
                "status": PostProcessingStatus.FAILED.name,
            },
        }
        async_post_process = FailedPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[upload for upload in self.base_input_object],
            action_params=self.action_param_dict,
            result=result_dict,
        )

        request_data = {'pk': async_post_process.uuid, 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.get(
            reverse('osis_document:get-progress-post-processing', kwargs={'pk': str(async_post_process.uuid)}),
            data=request_data,
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data.get('progress'), 50.0)
        self.assertEqual(response.data.get('wanted_post_process_status'), PostProcessingStatus.FAILED.name)

    def test_get_progress_with_bad_uuid(self):
        request_data = {'pk': uuid.uuid4(), 'wanted_post_process': PostProcessingWanted.MERGE.name}
        response = self.client.get(
            reverse('osis_document:get-progress-post-processing', kwargs={'pk': uuid.uuid4()}), data=request_data
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(response.data.get('error'))
        self.assertIsNone(response.data.get('progress'))
        self.assertIsNone(response.data.get('wanted_post_process_status'))
