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
import os
import uuid

from django.shortcuts import resolve_url
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from osis_document.enums import DocumentError
from osis_document.models import Upload, ModifiedUpload
from osis_document.tests.factories import PdfUploadFactory, ModifiedUploadFactory


@override_settings(ROOT_URLCONF="osis_document.urls", OSIS_DOCUMENT_API_SHARED_SECRET='foobar')
class DuplicateUploadViewTestCase(APITestCase):
    default_file_path = 'tests/duplicate/'
    default_file_name = 'tests/duplicate/the_file.pdf'

    def setUp(self):
        self.client.defaults = {'HTTP_X_API_KEY': 'foobar'}

    def test_duplicate_unknown_upload(self):
        unknown_upload_uuid = str(uuid.uuid4())
        response = self.client.post(
            resolve_url('duplicate'),
            {
                'uuids': [unknown_upload_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        json_response = response.json()

        self.assertIn(unknown_upload_uuid, json_response)

        self.assertEqual(
            json_response[unknown_upload_uuid],
            {'error': {'code': DocumentError.UPLOAD_NOT_FOUND.name, 'message': DocumentError.UPLOAD_NOT_FOUND.value}},
        )

    def test_duplicate_upload(self):
        upload = PdfUploadFactory()

        original_upload_uuid = upload.uuid
        original_upload_uuid_str = str(original_upload_uuid)

        response = self.client.post(
            resolve_url('duplicate'),
            {
                'uuids': [original_upload_uuid],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        json_response = response.json()

        self.assertIn(original_upload_uuid_str, json_response)

        uploads = Upload.objects.all()
        self.assertEqual(len(uploads), 2)
        self.assertIn(upload, uploads)

        if uploads[0].uuid == original_upload_uuid:
            original_upload, new_upload = uploads
        else:
            new_upload, original_upload = uploads

        # Check that the original upload has not been updated
        self.assertEqual(original_upload.expires_at, upload.expires_at)
        self.assertEqual(original_upload.mimetype, upload.mimetype)
        self.assertEqual(original_upload.size, upload.size)
        self.assertEqual(original_upload.status, upload.status)
        self.assertEqual(original_upload.metadata, upload.metadata)
        self.assertEqual(original_upload.uploaded_at, upload.uploaded_at)
        self.assertEqual(original_upload.modified_at, upload.modified_at)
        self.assertEqual(original_upload.uuid, upload.uuid)
        self.assertEqual(original_upload.file, upload.file)

        # Check that the new upload is a valid copy of the original
        self.assertEqual(original_upload.expires_at, new_upload.expires_at)
        self.assertEqual(original_upload.mimetype, new_upload.mimetype)
        self.assertEqual(original_upload.size, new_upload.size)
        self.assertEqual(original_upload.status, new_upload.status)
        self.assertEqual(original_upload.metadata, new_upload.metadata)

        self.assertNotEqual(original_upload.uploaded_at, new_upload.uploaded_at)
        self.assertNotEqual(original_upload.modified_at, new_upload.modified_at)
        self.assertNotEqual(original_upload.uuid, new_upload.uuid)
        self.assertNotEqual(original_upload.file, new_upload.file)

        # Check that the file names are different
        original_file_name = os.path.basename(original_upload.file.name)
        new_file_name = os.path.basename(new_upload.file.name)

        self.assertNotEqual(original_file_name, new_file_name)

        # Check that the new file has been created in the same directory as the original
        original_file_path = os.path.dirname(original_upload.file.name)
        new_file_path = os.path.dirname(new_upload.file.name)

        self.assertEqual(original_file_path, new_file_path)

    def test_duplicate_upload_with_modified_upload(self):
        modified_upload = ModifiedUploadFactory()
        upload = modified_upload.upload

        original_upload_uuid = upload.uuid
        original_upload_uuid_str = str(original_upload_uuid)

        # The upload must be duplicated but not the modified one
        response = self.client.post(
            resolve_url('duplicate'),
            {
                'uuids': [original_upload_uuid],
                'with_modified_upload': False,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        json_response = response.json()

        self.assertIn(original_upload_uuid_str, json_response)

        modified_uploads = ModifiedUpload.objects.all()
        self.assertEqual(len(modified_uploads), 1)
        self.assertIn(modified_upload, modified_uploads)

        uploads = Upload.objects.all()
        self.assertEqual(len(uploads), 2)
        self.assertIn(upload, uploads)

        uploads[1 if uploads[0].uuid == original_upload_uuid else 0].delete()

        # The upload must be duplicated and the modified one
        response = self.client.post(
            resolve_url('duplicate'),
            {
                'uuids': [original_upload_uuid],
                'with_modified_upload': True,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        json_response = response.json()

        self.assertIn(original_upload_uuid_str, json_response)

        modified_uploads = ModifiedUpload.objects.all()
        self.assertEqual(len(modified_uploads), 2)
        self.assertIn(modified_upload, modified_uploads)

        if modified_uploads[0].upload.uuid == original_upload_uuid:
            original_modified_upload, new_modified_upload = modified_uploads
        else:
            new_modified_upload, original_modified_upload = modified_uploads

        uploads = Upload.objects.all()
        self.assertCountEqual(
            uploads,
            [original_modified_upload.upload, new_modified_upload.upload],
        )

        # Check that the original upload has not been updated
        self.assertEqual(original_modified_upload.upload.expires_at, upload.expires_at)
        self.assertEqual(original_modified_upload.upload.mimetype, upload.mimetype)
        self.assertEqual(original_modified_upload.upload.size, upload.size)
        self.assertEqual(original_modified_upload.upload.status, upload.status)
        self.assertEqual(original_modified_upload.upload.metadata, upload.metadata)
        self.assertEqual(original_modified_upload.upload.uploaded_at, upload.uploaded_at)
        self.assertEqual(original_modified_upload.upload.modified_at, upload.modified_at)
        self.assertEqual(original_modified_upload.upload.uuid, upload.uuid)
        self.assertEqual(original_modified_upload.upload.file, upload.file)

        # Check that the original modified upload has not been updated
        self.assertEqual(original_modified_upload.size, modified_upload.size)
        self.assertEqual(original_modified_upload.created_at, modified_upload.created_at)
        self.assertEqual(original_modified_upload.modified_at, modified_upload.modified_at)
        self.assertEqual(original_modified_upload.file, modified_upload.file)

        # Check that the modified upload is a valid copy of the original
        self.assertEqual(original_modified_upload.size, new_modified_upload.size)

        self.assertNotEqual(original_modified_upload.created_at, new_modified_upload.created_at)
        self.assertNotEqual(original_modified_upload.modified_at, new_modified_upload.modified_at)
        self.assertNotEqual(original_modified_upload.file, new_modified_upload.file)

        # Check that the file names are different
        original_file_name = os.path.basename(original_modified_upload.file.name)
        new_file_name = os.path.basename(new_modified_upload.file.name)

        self.assertNotEqual(original_file_name, new_file_name)

        # Check that the new file has been created in the same directory as the original
        original_file_path = os.path.dirname(original_modified_upload.file.name)
        new_file_path = os.path.dirname(new_modified_upload.file.name)

        self.assertEqual(original_file_path, new_file_path)

        # Check that the upload is a valid copy of the original
        self.assertEqual(original_modified_upload.upload.expires_at, new_modified_upload.upload.expires_at)
        self.assertEqual(original_modified_upload.upload.mimetype, new_modified_upload.upload.mimetype)
        self.assertEqual(original_modified_upload.upload.size, new_modified_upload.upload.size)
        self.assertEqual(original_modified_upload.upload.status, new_modified_upload.upload.status)
        self.assertEqual(original_modified_upload.upload.metadata, new_modified_upload.upload.metadata)

        self.assertNotEqual(original_modified_upload.upload.uploaded_at, new_modified_upload.upload.uploaded_at)
        self.assertNotEqual(original_modified_upload.upload.modified_at, new_modified_upload.upload.modified_at)
        self.assertNotEqual(original_modified_upload.upload.uuid, new_modified_upload.upload.uuid)
        self.assertNotEqual(original_modified_upload.upload.file, new_modified_upload.upload.file)

        # Check that the file names are different
        original_file_name = os.path.basename(original_modified_upload.upload.file.name)
        new_file_name = os.path.basename(new_modified_upload.upload.file.name)

        self.assertNotEqual(original_file_name, new_file_name)

        # Check that the new file has been created in the same directory as the original
        original_file_path = os.path.dirname(original_modified_upload.upload.file.name)
        new_file_path = os.path.dirname(new_modified_upload.upload.file.name)

        self.assertEqual(original_file_path, new_file_path)

    def test_duplicate_upload_with_specific_upload_paths(self):
        modified_upload = ModifiedUploadFactory()
        upload = modified_upload.upload

        original_upload_uuid = upload.uuid
        original_upload_uuid_str = str(original_upload_uuid)

        custom_file_path = self.default_file_path + 'custom'

        response = self.client.post(
            resolve_url('duplicate'),
            {
                'uuids': [original_upload_uuid],
                'with_modified_upload': True,
                'upload_path_by_uuid': {original_upload_uuid_str: custom_file_path + '/file_name'},
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        json_response = response.json()

        self.assertIn(original_upload_uuid_str, json_response)

        modified_uploads = ModifiedUpload.objects.all()
        self.assertEqual(len(modified_uploads), 2)
        self.assertIn(modified_upload, modified_uploads)

        if modified_uploads[0].upload.uuid == original_upload_uuid:
            original_modified_upload, new_modified_upload = modified_uploads
        else:
            new_modified_upload, original_modified_upload = modified_uploads

        uploads = Upload.objects.all()
        self.assertCountEqual(
            uploads,
            [original_modified_upload.upload, new_modified_upload.upload],
        )

        # Check that the upload is uploaded to the correct directory
        self.assertNotEqual(original_modified_upload.upload.file, new_modified_upload.upload.file)

        # Check that the file names are different
        original_file_name = os.path.basename(original_modified_upload.upload.file.name)
        new_file_name = os.path.basename(new_modified_upload.upload.file.name)

        self.assertNotEqual(original_file_name, new_file_name)
        self.assertIn('file_name', new_file_name)

        # Check that the new file has been created in the specific directory
        original_file_path = os.path.dirname(original_modified_upload.upload.file.name)
        new_file_path = os.path.dirname(new_modified_upload.upload.file.name)

        self.assertNotEqual(original_file_path, new_file_path)
        self.assertEqual(new_file_path, custom_file_path)

        # Check that the modified upload is uploaded to the correct directory
        self.assertNotEqual(original_modified_upload.file, new_modified_upload.file)

        # Check that the file names are different
        original_file_name = os.path.basename(original_modified_upload.file.name)
        new_file_name = os.path.basename(new_modified_upload.file.name)

        self.assertNotEqual(original_file_name, new_file_name)
        self.assertIn('file_name', new_file_name)

        # Check that the new file has been created in the specific directory
        original_file_path = os.path.dirname(original_modified_upload.file.name)
        new_file_path = os.path.dirname(new_modified_upload.file.name)

        self.assertNotEqual(original_file_path, new_file_path)
        self.assertEqual(new_file_path, custom_file_path)
