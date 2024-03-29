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
from unittest.mock import Mock, patch

import uuid
from django.test import TestCase, override_settings
from requests import HTTPError

from osis_document.api.utils import (
    confirm_remote_upload,
    get_remote_metadata,
    get_remote_token,
    declare_remote_files_as_deleted,
    documents_remote_duplicate,
)
from osis_document.enums import DocumentExpirationPolicy, DocumentError
from osis_document.exceptions import FileInfectedException, UploadInvalidException


@override_settings(
    OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/',
    OSIS_DOCUMENT_API_SHARED_SECRET='very-secret',
)
class RemoteUtilsTestCase(TestCase):
    def test_get_remote_token_bad_uuid(self):
        with patch('requests.post') as request_mock:
            request_mock.side_effect = HTTPError
            self.assertIsNone(get_remote_token('bbc1ba15-42d2-48e9-9884-7631417bb1e1'))

    def test_get_remote_token(self):
        with patch('requests.post') as request_mock:
            request_mock.return_value.json.return_value = {"token": "something"}
            self.assertEqual(get_remote_token('bbc1ba15-42d2-48e9-9884-7631417bb1e1'), "something")

    def test_get_remote_token_infected_file(self):
        with patch('requests.post') as request_mock:
            request_mock.return_value.status_code = 500
            request_mock.return_value.json.return_value = {"detail": FileInfectedException.default_detail}
            self.assertEqual(
                get_remote_token('bbc1ba15-42d2-48e9-9884-7631417bb1e1'),
                FileInfectedException.__class__.__name__,
            )

    def test_get_remote_token_not_found(self):
        with patch('requests.post') as request_mock:
            request_mock.return_value.status_code = 404
            self.assertEqual(
                get_remote_token('bbc1ba15-42d2-48e9-9884-7631417bb1e1'),
                UploadInvalidException.__class__.__name__,
            )

    def test_get_remote_metadata_bad_token(self):
        with patch('requests.get') as request_mock:
            request_mock.side_effect = HTTPError
            self.assertIsNone(get_remote_metadata('some_token'))

    def test_get_remote_metadata_not_found(self):
        with patch('requests.get') as request_mock:
            request_mock.return_value.status_code = 404
            self.assertIsNone(get_remote_metadata('some_token'))

    def test_get_remote_metadata(self):
        with patch('requests.get') as request_mock:
            request_mock.return_value.status_code = 200
            request_mock.return_value.json.return_value = {"foo": "bar"}
            self.assertEqual(get_remote_metadata('some_token'), {"foo": "bar"})

    def test_confirm_remote_upload(self):
        with patch('requests.post') as request_mock:
            request_mock.return_value.json.return_value = {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            self.assertEqual(confirm_remote_upload('some_token'), 'bbc1ba15-42d2-48e9-9884-7631417bb1e1')
            expected_url = 'http://dummyurl.com/document/confirm-upload/some_token'
            request_mock.assert_called_with(expected_url, json={}, headers={'X-Api-Key': 'very-secret'})

    def test_confirm_remote_upload_with_upload_to(self):
        with patch('requests.post') as request_mock:
            request_mock.return_value.json.return_value = {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            self.assertEqual(confirm_remote_upload('some_token', 'path/'), 'bbc1ba15-42d2-48e9-9884-7631417bb1e1')
            expected_url = 'http://dummyurl.com/document/confirm-upload/some_token'
            request_mock.assert_called_with(
                expected_url,
                json={"upload_to": "path/"},
                headers={'X-Api-Key': 'very-secret'},
            )

    def test_confirm_remote_upload_with_upload_to_and_document_expiration_policy(self):
        with patch('requests.post') as request_mock:
            request_mock.return_value.json.return_value = {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            self.assertEqual(
                confirm_remote_upload(
                    'some_token',
                    'path/',
                    document_expiration_policy=DocumentExpirationPolicy.EXPORT_EXPIRATION_POLICY.value,
                ),
                'bbc1ba15-42d2-48e9-9884-7631417bb1e1',
            )
            expected_url = 'http://dummyurl.com/document/confirm-upload/some_token'
            request_mock.assert_called_with(
                expected_url,
                json={
                    "upload_to": "path/",
                    "document_expiration_policy": DocumentExpirationPolicy.EXPORT_EXPIRATION_POLICY.value,
                },
                headers={'X-Api-Key': 'very-secret'},
            )

    def test_confirm_remote_upload_with_related_model(self):
        related_model = {
            'app': 'app_name',
            'model': 'model_name',
            'field': 'field_name',
            'instance_filter_fields': ['id'],
        }
        with patch('requests.post') as request_mock:
            request_mock.return_value.json.return_value = {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            self.assertEqual(
                confirm_remote_upload(
                    token='some_token',
                    related_model=related_model,
                ),
                'bbc1ba15-42d2-48e9-9884-7631417bb1e1',
            )
            expected_url = 'http://dummyurl.com/document/confirm-upload/some_token'
            request_mock.assert_called_with(
                expected_url,
                json={'related_model': related_model},
                headers={'X-Api-Key': 'very-secret'},
            )

    def test_confirm_remote_upload_with_related_model_and_instance(self):
        related_model = {
            'app': 'app_name',
            'model': 'model_name',
            'field': 'field_name',
            'instance_filter_fields': ['id'],
        }
        fake_instance = Mock(id=10)
        with patch('requests.post') as request_mock:
            request_mock.return_value.json.return_value = {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            self.assertEqual(
                confirm_remote_upload(
                    token='some_token',
                    related_model=related_model,
                    related_model_instance=fake_instance,
                ),
                'bbc1ba15-42d2-48e9-9884-7631417bb1e1',
            )
            expected_url = 'http://dummyurl.com/document/confirm-upload/some_token'
            request_mock.assert_called_with(
                expected_url,
                json={
                    'related_model': {
                        'app': 'app_name',
                        'model': 'model_name',
                        'field': 'field_name',
                        'instance_filters': {'id': 10},
                    },
                },
                headers={'X-Api-Key': 'very-secret'},
            )


@override_settings(
    OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/',
    OSIS_DOCUMENT_API_SHARED_SECRET='very-secret',
)
class DeclareRemoteFilesAsDeletedTestCase(TestCase):
    def test_declare_remote_files_as_deleted(self):
        files_to_delete = [uuid.uuid4(), uuid.uuid4()]

        with patch('requests.post') as request_mock:
            request_mock.return_value.status_code = 204
            self.assertIsNone(declare_remote_files_as_deleted(files_to_delete))
            self.assertEqual(request_mock.call_args[0][0], 'http://dummyurl.com/document/declare-files-as-deleted')
            self.assertDictEqual(
                request_mock.call_args[1],
                {'json': {'files': [str(file) for file in files_to_delete]}, 'headers': {'X-Api-Key': 'very-secret'}},
            )


@override_settings(
    OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/',
    OSIS_DOCUMENT_API_SHARED_SECRET='very-secret',
)
class DocumentsRemoteDuplicateTestCase(TestCase):
    def test_documents_remote_duplicate(self):
        files_to_duplicate = [str(uuid.uuid4()), str(uuid.uuid4())]
        duplicates_files = [str(uuid.uuid4()), str(uuid.uuid4())]

        with patch('requests.post') as request_mock:
            request_mock.return_value.status_code = 201
            request_mock.return_value.json.return_value = {
                # Retrieved because the duplicate is created
                files_to_duplicate[0]: {'upload_id': duplicates_files[0]},
                # Not retrieved because the upload is not found
                files_to_duplicate[1]: {'error': DocumentError.get_dict_error(DocumentError.UPLOAD_NOT_FOUND.name)},
            }
            result = documents_remote_duplicate(
                uuids=files_to_duplicate,
                with_modified_upload=True,
                upload_path_by_uuid={
                    files_to_duplicate[0]: 'custom_path/file.pdf',
                    files_to_duplicate[1]: 'custom_path2/file2.pdf',
                },
            )

            # Check call
            self.assertEqual(request_mock.call_args[0][0], 'http://dummyurl.com/document/duplicate')
            self.assertDictEqual(
                request_mock.call_args[1],
                {
                    'json': {
                        'uuids': files_to_duplicate,
                        'with_modified_upload': True,
                        'upload_path_by_uuid': {
                            files_to_duplicate[0]: 'custom_path/file.pdf',
                            files_to_duplicate[1]: 'custom_path2/file2.pdf',
                        },
                    },
                    'headers': {'X-Api-Key': 'very-secret'},
                },
            )

            # Check result
            self.assertEqual(result, {files_to_duplicate[0]: duplicates_files[0]})
