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
from datetime import date, datetime, timedelta
from unittest import mock
from unittest.mock import Mock, patch

from django.core.exceptions import FieldError
from django.test import TestCase, override_settings

from osis_document.enums import FileStatus
from osis_document.exceptions import Md5Mismatch
from osis_document.models import Upload
from osis_document.tests.factories import PdfUploadFactory, WriteTokenFactory
from osis_document.utils import confirm_upload, generate_filename, get_metadata, is_uuid, save_raw_upload


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class MetadataTestCase(TestCase):
    def test_with_token(self):
        token = WriteTokenFactory()
        metadata = get_metadata(token.token)
        self.assertEqual(metadata['size'], 1024)
        self.assertEqual(metadata['mimetype'], 'application/pdf')
        self.assertEqual(metadata['md5'], '5eb63bbbe01eeed093cb22bb8f5acdc3')
        self.assertIn('url', metadata)

        with mock.patch('django.utils.timezone.now', return_value=datetime(1990, 1, 1)):
            old_token = WriteTokenFactory(upload=token.upload)
            self.assertIsNone(get_metadata(old_token.token))

    def test_bad_md5(self):
        token = WriteTokenFactory(upload__metadata={'md5': 'badvalue'})
        with self.assertRaises(Md5Mismatch):
            get_metadata(token.token)


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class RawUploadTestCase(TestCase):
    def test_with_bytes(self):
        token = save_raw_upload(
            file=bytes('my file content', encoding='utf8'),
            name='my_file_name.txt',
            mimetype='text/plain',
        )
        metadata = get_metadata(token.token)
        self.assertEqual(metadata['size'], 48)
        self.assertEqual(metadata['mimetype'], 'text/plain')
        self.assertEqual(metadata['md5'], 'ebf9d9524ad7f702a2c3a75f060024f1')


class IsUuidTestCase(TestCase):
    def test_is_uuid(self):
        self.assertFalse(is_uuid(WriteTokenFactory().token))
        self.assertFalse(is_uuid(1))
        self.assertTrue(is_uuid('a91c3af8-91eb-4b68-96fc-0769a28a95c3'))
        self.assertTrue(is_uuid(uuid.UUID('a91c3af8-91eb-4b68-96fc-0769a28a95c3')))


class GenerateFilenameTestCase(TestCase):
    def test_with_callable_upload_to_without_instance(self):
        generated_filename = generate_filename(
            instance=None,
            filename='my_file.txt',
            upload_to=(lambda _, filename: 'path/{}'.format(filename)),
        )
        self.assertEqual(generated_filename, 'path/my_file.txt')

    def test_with_callable_upload_to_with_instance(self):
        generated_filename = generate_filename(
            instance=Mock(attr_a=10),
            filename='my_file.txt',
            upload_to=(lambda instance, filename: 'path/{}/{}'.format(instance.attr_a, filename)),
        )
        self.assertEqual(generated_filename, 'path/10/my_file.txt')

    def test_with_string_upload_to(self):
        generated_filename = generate_filename(
            instance=None,
            filename='my_file.txt',
            upload_to='my-path/',
        )
        self.assertEqual(generated_filename, 'my-path/my_file.txt')

    def test_with_date_string_upload_to(self):
        with patch('osis_document.utils.datetime') as mock_datetime:
            mock_datetime.datetime.now.return_value = date(2022, 1, 10)
            mock_datetime.side_effect = lambda *args, **kw: date(*args, **kw)

            generated_filename = generate_filename(
                instance=None,
                filename='my_file.txt',
                upload_to='%Y/%m/%d',
            )
            self.assertEqual(generated_filename, '2022/01/10/my_file.txt')

    def test_with_undefined_upload(self):
        generated_filename = generate_filename(
            instance=None,
            filename='my_file.txt',
            upload_to=None,
        )
        self.assertEqual(generated_filename, 'my_file.txt')


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class ConfirmUploadTestCase(TestCase):
    def test_with_token(self):
        token = WriteTokenFactory()
        original_upload = token.upload
        # The file has been saved at the root path
        self.assertTrue(original_upload.file.storage.exists(original_upload.file.name))
        self.assertEqual(original_upload.status, FileStatus.REQUESTED.name)
        # Confirm the upload
        original_upload_uuid = confirm_upload(token.token, upload_to='path/')
        # The file has been moved to the 'path/' repository
        updated_upload = Upload.objects.get(uuid=original_upload_uuid)
        self.assertFalse(original_upload.file.storage.exists(original_upload.file.name))
        self.assertNotEqual(original_upload.file.name, updated_upload.file.name)
        # The status file has been updated
        self.assertEqual(updated_upload.status, FileStatus.UPLOADED.name)

    def test_with_confirmed_upload(self):
        original_upload = PdfUploadFactory(status=FileStatus.UPLOADED.name)
        token = WriteTokenFactory(upload=original_upload)
        self.assertTrue(original_upload.file.storage.exists(original_upload.file.name))
        # Confirm the upload
        original_upload_uuid = confirm_upload(token.token, upload_to='path/')
        # The file hasn't been moved
        updated_upload = Upload.objects.get(uuid=original_upload_uuid)
        self.assertTrue(original_upload.file.storage.exists(original_upload.file.name))
        self.assertEqual(original_upload.file.name, updated_upload.file.name)

    def test_with_unknown_token(self):
        with self.assertRaises(FieldError):
            confirm_upload('unknown-token', upload_to='path/')

    def test_with_expired_token(self):
        token = WriteTokenFactory()
        token.expires_at = token.created_at - timedelta(1)
        token.save()
        with self.assertRaises(FieldError):
            confirm_upload(token.token, upload_to='path/')
