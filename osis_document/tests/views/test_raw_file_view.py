# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2025 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.datetime_safe import datetime

from osis_document.enums import FileStatus
from osis_document.tests.factories import PdfUploadFactory, ReadTokenFactory, ModifiedUploadFactory


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class FileViewTestCase(TestCase):
    from django.urls import path, include

    app_name = 'osis_document'
    urlpatterns = [
        path('', include('osis_document.urls', namespace="osis_document")),
    ]

    @override_settings(OSIS_DOCUMENT_DOMAIN_LIST=[])
    def test_get_file_valid_token(self):
        token = ReadTokenFactory()
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': token.token,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.has_header('Content-Security-Policy'))

    @override_settings(OSIS_DOCUMENT_DOMAIN_LIST=['127.0.0.1'])
    def test_get_file_with_csp(self):
        token = ReadTokenFactory()
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': token.token,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('Content-Security-Policy'))
        self.assertNotIn('attachment', response['Content-Disposition'])

    def test_get_file_as_attachement(self):
        token = ReadTokenFactory()
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': token.token,
                },
            )
            + '?dl=1'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('attachment', response['Content-Disposition'])

    def test_get_file_bad_hash(self):
        token = ReadTokenFactory(upload__metadata={'hash': 'badvalue'})
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': token.token,
                },
            )
        )
        self.assertEqual(response.status_code, 409)

    def test_get_file_bad_token(self):
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': 'token',
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_get_file_infected(self):
        token = ReadTokenFactory(upload__status=FileStatus.INFECTED.name)
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': token.token,
                },
            )
        )
        self.assertEqual(response.status_code, 500)

    def test_get_file_expired_token(self):
        from datetime import timedelta

        date_expiration = datetime.now() - timedelta(seconds=60)
        token = ReadTokenFactory(expires_at=date_expiration)
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': token.token,
                },
            ),
            follow=False,
        )
        self.assertEqual(response.status_code, 403)

    def test_get_modified_file(self):
        modified_upload = ModifiedUploadFactory()
        token = ReadTokenFactory(upload=modified_upload.upload, for_modified_upload=True)
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': token.token,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), modified_upload.file.read())

    def test_get_modified_file_without_modified_file(self):
        upload = PdfUploadFactory()
        token = ReadTokenFactory(upload=upload, for_modified_upload=True)
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': token.token,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), upload.file.read())

    def test_get_original_upload_with_modified_file(self):
        modified_upload = ModifiedUploadFactory()
        token = ReadTokenFactory(upload=modified_upload.upload, for_modified_upload=False)
        response = self.client.get(
            reverse(
                'osis_document:raw-file',
                kwargs={
                    'token': token.token,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), modified_upload.upload.file.read())
