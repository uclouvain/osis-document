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
import json
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from django.test import TestCase, override_settings

from osis_document.api.utils import confirm_remote_upload, get_remote_metadata, get_remote_token
from osis_document.exceptions import UploadConfirmationException


def to_json_bytes(value):
    return json.dumps(value).encode("utf8")


@override_settings(
    OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/',
    OSIS_DOCUMENT_API_SHARED_SECRET='very-secret',
)
class RemoteUtilsTestCase(TestCase):
    def test_get_remote_token_bad_uuid(self):
        with patch('urllib.request') as request_mock:
            request_mock.urlopen.return_value.__enter__.side_effect = HTTPError('', 404, '', {}, None)
            self.assertIsNone(get_remote_token('bbc1ba15-42d2-48e9-9884-7631417bb1e1'))

    def test_get_remote_token(self):
        with patch('urllib.request') as request_mock:
            request_mock.urlopen.return_value.__enter__.return_value.read.return_value = to_json_bytes(
                {"token": "something"}
            )
            self.assertEqual(get_remote_token('bbc1ba15-42d2-48e9-9884-7631417bb1e1'), "something")

    def test_get_remote_metadata_bad_token(self):
        with patch('urllib.request') as request_mock:
            request_mock.urlopen.return_value.__enter__.side_effect = HTTPError('', 404, '', {}, None)
            self.assertIsNone(get_remote_metadata('some_token'))

    def test_get_remote_metadata(self):
        with patch('urllib.request') as request_mock:
            request_mock.urlopen.return_value.__enter__.return_value.read.return_value = to_json_bytes({"foo": "bar"})
            self.assertEqual(get_remote_metadata('some_token'), {"foo": "bar"})

    def test_confirm_remote_upload_bad_token(self):
        with patch('urllib.request') as request_mock:
            request_mock.urlopen.return_value.__enter__.side_effect = HTTPError('', 404, '', {}, None)
            with self.assertRaises(UploadConfirmationException):
                confirm_remote_upload('some_token')

    def test_confirm_remote_upload(self):
        with patch('urllib.request') as request_mock:
            request_mock.urlopen.return_value.__enter__.return_value.read.return_value = to_json_bytes(
                {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            )
            self.assertEqual(confirm_remote_upload('some_token'), 'bbc1ba15-42d2-48e9-9884-7631417bb1e1')
            expected_url = 'http://dummyurl.com/document/confirm-upload/some_token'
            request_mock.Request.assert_called_with(expected_url, method='POST', data=b'{}')

    def test_confirm_remote_upload_with_upload_to(self):
        with patch('urllib.request') as request_mock:
            request_mock.urlopen.return_value.__enter__.return_value.read.return_value = to_json_bytes(
                {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            )
            self.assertEqual(confirm_remote_upload('some_token', 'path/'), 'bbc1ba15-42d2-48e9-9884-7631417bb1e1')
            expected_url = 'http://dummyurl.com/document/confirm-upload/some_token'
            request_mock.Request.assert_called_with(
                expected_url,
                method='POST',
                data=b'{"upload_to": "path/"}',
            )

    def test_confirm_remote_upload_with_related_model(self):
        related_model = {
            'app': 'app_name',
            'model': 'model_name',
            'field': 'field_name',
            'instance_filter_fields': ['id'],
        }
        with patch('urllib.request') as request_mock:
            request_mock.urlopen.return_value.__enter__.return_value.read.return_value = to_json_bytes(
                {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            )
            self.assertEqual(
                confirm_remote_upload(
                    token='some_token',
                    related_model=related_model,
                ),
                'bbc1ba15-42d2-48e9-9884-7631417bb1e1',
            )
            expected_url = 'http://dummyurl.com/document/confirm-upload/some_token'
            request_mock.Request.assert_called_with(
                expected_url,
                method='POST',
                data=to_json_bytes({'related_model': related_model}),
            )

    def test_confirm_remote_upload_with_related_model_and_instance(self):
        related_model = {
            'app': 'app_name',
            'model': 'model_name',
            'field': 'field_name',
            'instance_filter_fields': ['id'],
        }
        fake_instance = Mock(id=10)
        with patch('urllib.request') as request_mock:
            request_mock.urlopen.return_value.__enter__.return_value.read.return_value = to_json_bytes(
                {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            )
            self.assertEqual(
                confirm_remote_upload(
                    token='some_token',
                    related_model=related_model,
                    related_model_instance=fake_instance,
                ),
                'bbc1ba15-42d2-48e9-9884-7631417bb1e1',
            )
            expected_url = 'http://dummyurl.com/document/confirm-upload/some_token'
            request_mock.Request.assert_called_with(
                expected_url,
                method='POST',
                data=to_json_bytes(
                    {
                        'related_model': {
                            'app': 'app_name',
                            'model': 'model_name',
                            'field': 'field_name',
                            'instance_filters': {'id': 10},
                        },
                    }
                ),
            )
