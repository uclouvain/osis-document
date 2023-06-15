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
import uuid
from unittest import mock

from django.test import TestCase, override_settings
from django.utils.datetime_safe import datetime

from osis_document.enums import FileStatus, PostProcessingStatus, PostProcessingType
from osis_document.models import Token, Upload, PostProcessAsync
from osis_document.exceptions import MissingFileException
from osis_document.tasks import cleanup_old_uploads, make_pending_async_post_processing
from osis_document.tests.factories import WriteTokenFactory, PdfUploadFactory, PdfUploadFactory, \
    CorrectPDFUploadFactory, TextDocumentUploadFactory, ImageUploadFactory, PendingPostProcessingAsyncFactory, \
    DonePostProcessingAsyncFactory, FailedPostProcessingAsyncFactory


class CleanupTaskTestCase(TestCase):
    def test_cleanup_task(self):
        with mock.patch('django.utils.timezone.now', return_value=datetime(1990, 1, 1)):
            # Should be kept
            PdfUploadFactory(status=FileStatus.UPLOADED.name)
            # Token should be deleted but file kept
            WriteTokenFactory(upload__status=FileStatus.UPLOADED.name)
            # Should be deleted
            upload = PdfUploadFactory()

        PdfUploadFactory(status=FileStatus.UPLOADED.name)
        WriteTokenFactory()
        WriteTokenFactory(upload=upload)

        self.assertEqual(Upload.objects.count(), 5)
        self.assertEqual(Token.objects.count(), 3)

        cleanup_old_uploads()

        # Should have delete 2 tokens and a file
        self.assertEqual(Upload.objects.count(), 4)
        self.assertEqual(Token.objects.count(), 1)


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class MakePendingAsyncPostProcessTaskTestCase(TestCase):
    def setUp(self) -> None:
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}
        self.text = TextDocumentUploadFactory()
        self.img = ImageUploadFactory()
        self.action_list = [PostProcessingType.CONVERT.name, PostProcessingType.MERGE.name]
        self.action_param_dict = {
            PostProcessingType.CONVERT.name: {},
            PostProcessingType.MERGE.name: {"output_filename": "a_test_merge_with_params_and_filename",
                                            "pages_dimension": "A4"
                                            }
        }
        self.done_post_processing = DonePostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[self.text.uuid, self.img.uuid],
            action_params=self.action_param_dict,
            result={
                PostProcessingType.CONVERT.name: {"status": PostProcessingStatus.DONE.name},
                PostProcessingType.MERGE.name: {"status": PostProcessingStatus.DONE.name}
            }
        )
        self.failed_post_processing = FailedPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[self.text.uuid, self.img.uuid],
            action_params=self.action_param_dict,
            result={
                PostProcessingType.CONVERT.name: {"status": PostProcessingStatus.PENDING.name},
                PostProcessingType.MERGE.name: {"status": PostProcessingStatus.PENDING.name}
            }
        )

    def test_failed_on_first_process(self):
        result_dict = {
            PostProcessingType.CONVERT.name: {"status": PostProcessingStatus.PENDING.name},
            PostProcessingType.MERGE.name: {"status": PostProcessingStatus.PENDING.name}
        }
        pending_post_process = PendingPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[self.text.uuid, uuid.uuid4()],
            action_params=self.action_param_dict,
            result=result_dict
        )
        self.client.raise_request_exception = False
        self.assertEqual(len(PostProcessAsync.objects.all()), 3)
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.PENDING.name)), 1)
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.FAILED.name)), 1)
        make_pending_async_post_processing()
        pending_post_process.refresh_from_db()
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.PENDING.name)), 0)
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.FAILED.name)), 2)
        self.assertEqual(pending_post_process.status, PostProcessingStatus.FAILED.name)
        self.assertEqual(pending_post_process.results['CONVERT']['status'], PostProcessingStatus.FAILED.name)
        self.assertEqual(pending_post_process.results['MERGE']['status'], PostProcessingStatus.PENDING.name)

    def test_failed_on_second_process(self):
        result_dict = {
            PostProcessingType.CONVERT.name: {"status": PostProcessingStatus.PENDING.name},
            "bad_post_process_name": {"status": PostProcessingStatus.PENDING.name}
        }
        pending_post_process = PendingPostProcessingAsyncFactory(
            action=[PostProcessingType.CONVERT.name, "bad_post_process_name"],
            base_input=[self.text.uuid, self.img.uuid],
            action_params={
                PostProcessingType.CONVERT.name: {},
                "bad_post_process_name": {"output_filename": "a_test_merge_with_params_and_filename",
                                          "pages_dimension": "A4"
                                          }
            },
            result=result_dict
        )
        self.client.raise_request_exception = False
        self.assertEqual(len(PostProcessAsync.objects.all()), 3)
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.PENDING.name)), 1)
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.FAILED.name)), 1)
        make_pending_async_post_processing()
        pending_post_process.refresh_from_db()
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.PENDING.name)), 0)
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.FAILED.name)), 2)
        self.assertEqual(pending_post_process.status, PostProcessingStatus.FAILED.name)
        self.assertEqual(pending_post_process.results['CONVERT']['status'], PostProcessingStatus.DONE.name)
        self.assertEqual(pending_post_process.results["bad_post_process_name"]['status'], PostProcessingStatus.FAILED.name)
        self.assertIsNotNone(pending_post_process.results["bad_post_process_name"]['errors'])

    def test_done_process(self):
        result_dict = {
            PostProcessingType.CONVERT.name: {"status": PostProcessingStatus.PENDING.name},
            PostProcessingType.MERGE.name: {"status": PostProcessingStatus.PENDING.name}
        }
        pending_post_process = PendingPostProcessingAsyncFactory(
            action=self.action_list,
            base_input=[self.text.uuid, self.img.uuid],
            action_params=self.action_param_dict,
            result=result_dict
        )
        self.assertEqual(len(PostProcessAsync.objects.all()), 3)
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.PENDING.name)), 1)
        make_pending_async_post_processing()
        pending_post_process.refresh_from_db()
        self.assertEqual(len(PostProcessAsync.objects.filter(status=PostProcessingStatus.PENDING.name)), 0)
        self.assertEqual(pending_post_process.status, PostProcessingStatus.DONE.name)
        for action in self.action_list:
            self.assertEqual(pending_post_process.results[action]['status'], PostProcessingStatus.DONE.name)
