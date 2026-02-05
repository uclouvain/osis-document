# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2026 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import patch, MagicMock

import requests
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from external_storage.constants import EPC_EXTERNAL_STORAGE_NAME
from external_storage.exceptions import ExternalStorageAPICallTimeout, ExternalStorageAPICallException
from external_storage.models import Token


@override_settings(OSIS_DOCUMENT_API_SHARED_SECRET="test-secret-key")
class GetStudentFilesCountTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url_pattern = "external_storage:epc_student_files_count"

        cls.noma = "12345678"
        cls.sample_api_response = {
            "fichierDocumentDescription": [
                {
                    "cheminAbsolu": "/mnt/FichiersEPC/",
                    "dateEnregistrement": "2025-11-04T16:51:23.162+01:00",
                    "description": "AUTRE_DOCUMENT",
                    "descriptionDetaillee": "CVRC - Recours - Acceptation financiabilité",
                    "id": "4517638",
                    "nom": "CVRC - Décision recours - acceptation.pdf",
                    "nomFichier": "D7A1A25C-TRZEA-4160-9AF8-DFDFDFDFDFD.pdf",
                    "typeContenu": "APPLICATION_PDF",
                    "utilisateurUpload": "reredzdz"
                },
                {
                    "cheminAbsolu": "/mnt/FichiersEPC/",
                    "dateEnregistrement": "2021-11-30T15:28:17.702+01:00",
                    "description": "RECOURS_OBTENU",
                    "id": "2943511",
                    "nom": "Décision recours.pdf",
                    "nomFichier": "EC8BF38F-ERFS-4B3F-DFEZA-82973E58A3A5.pdf",
                    "typeContenu": "APPLICATION_PDF",
                    "utilisateurUpload": "ererere",
                    "anac": "2020"
                },
                {
                    "cheminAbsolu": "/mnt/FichiersEPC/",
                    "dateEnregistrement": "2021-11-30T15:28:17.702+01:00",
                    "description": "RECOURS_OBTENU",
                    "id": "294ezezez3511",
                    "nom": "Décision recours 2.pdf",
                    "nomFichier": "EC8BF38F-ERFS-4B3F-DFEZA-ezeze.pdf",
                    "typeContenu": "APPLICATION_PDF",
                    "utilisateurUpload": "ererere",
                }
            ]
        }

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.credentials(HTTP_X_API_KEY="test-secret-key")

    @override_settings(
        STUDENT_FILES_API_URL="https://mock-epc.com/{noma}",
        STUDENT_FILES_API_AUTHORIZATION_HEADER="Basic 123654789878789",
        STUDENT_FILES_API_CALL_TIMEOUT=10,
    )
    @patch('external_storage.api.epc.views.requests.get')
    def test_get_student_files_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        url = reverse(self.url_pattern, kwargs={"noma": self.noma})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Token.objects.count(), 0)
        self.assertEqual(response.data['count'], 3)


@override_settings(OSIS_DOCUMENT_API_SHARED_SECRET="test-secret-key")
class GetStudentFilesTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url_pattern = "external_storage:epc_student_files"

        cls.noma = "12345678"
        cls.sample_api_response = {
            "fichierDocumentDescription": [
                {
                    "cheminAbsolu": "/mnt/FichiersEPC/",
                    "dateEnregistrement": "2025-11-04T16:51:23.162+01:00",
                    "description": "AUTRE_DOCUMENT",
                    "descriptionDetaillee": "CVRC - Recours - Acceptation financiabilité",
                    "id": "4517638",
                    "nom": "CVRC - Décision recours - acceptation.pdf",
                    "nomFichier": "D7A1A25C-TRZEA-4160-9AF8-DFDFDFDFDFD.pdf",
                    "typeContenu": "APPLICATION_PDF",
                    "utilisateurUpload": "reredzdz"
                },
                {
                    "cheminAbsolu": "/mnt/FichiersEPC/",
                    "dateEnregistrement": "2021-11-30T15:28:17.702+01:00",
                    "description": "RECOURS_OBTENU",
                    "id": "2943511",
                    "nom": "Décision recours.pdf",
                    "nomFichier": "EC8BF38F-ERFS-4B3F-DFEZA-82973E58A3A5.pdf",
                    "typeContenu": "APPLICATION_PDF",
                    "utilisateurUpload": "ererere",
                    "anac": "2020"
                }
            ]
        }

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.credentials(HTTP_X_API_KEY="test-secret-key")

    @override_settings(
        STUDENT_FILES_API_URL="https://mock-epc.com/{noma}",
        STUDENT_FILES_API_AUTHORIZATION_HEADER="Basic 123654789878789",
        STUDENT_FILES_API_CALL_TIMEOUT=10,
    )
    @patch('external_storage.api.epc.views.requests.get')
    def test_get_student_files_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = self.sample_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        url = reverse(self.url_pattern, kwargs={"noma": self.noma})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mock_get.assert_called_once_with(
            "https://mock-epc.com/12345678",
            headers={'Authorization': 'Basic 123654789878789'},
            timeout=10
        )

        # Check token created for access to file
        tokens_qs = Token.objects.filter(external_storage_name=EPC_EXTERNAL_STORAGE_NAME)
        self.assertEqual(tokens_qs.count(), 2)
        self.assertTrue(tokens_qs.filter(metadata__external_storage_id='4517638').exists())
        self.assertTrue(tokens_qs.filter(metadata__external_storage_id='2943511').exists())

        # Check response view
        self.assertEqual(len(response.data), 2)
        self.assertIn("token", response.data[0])
        self.assertIn("token", response.data[1])

    @override_settings(STUDENT_FILES_API_URL=None)
    def test_student_files_api_url_not_configured(self):
        url = reverse(self.url_pattern, kwargs={"noma": self.noma})
        with self.assertRaises(ImproperlyConfigured):
            self.client.get(url)

    @override_settings(
        STUDENT_FILES_API_URL="https://mock-epc.com/{noma}",
        STUDENT_FILES_API_AUTHORIZATION_HEADER="Basic 123654789878789",
    )
    @patch('external_storage.api.epc.views.requests.get')
    def test_api_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()

        url = reverse(self.url_pattern, kwargs={"noma": self.noma})
        response = self.client.get(url)

        self.assertEqual(response.status_code, ExternalStorageAPICallTimeout.status_code)
        self.assertEqual(response.data["detail"], ExternalStorageAPICallTimeout.default_detail)
        self.assertEqual(Token.objects.count(), 0)

    @override_settings(
        STUDENT_FILES_API_URL="https://mock-epc.com/{noma}",
        STUDENT_FILES_API_AUTHORIZATION_HEADER="Basic 123654789878789",
    )
    @patch('external_storage.api.epc.views.requests.get')
    def test_api_http_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.HTTPError()

        url = reverse(self.url_pattern, kwargs={"noma": self.noma})
        response = self.client.get(url)

        self.assertEqual(response.status_code, ExternalStorageAPICallException.status_code)
        self.assertEqual(response.data["detail"], ExternalStorageAPICallException.default_detail)
        self.assertEqual(Token.objects.count(), 0)

    @override_settings(
        STUDENT_FILES_API_URL="https://mock-epc.com/{noma}",
        STUDENT_FILES_API_AUTHORIZATION_HEADER="Basic 123654789878789",
    )
    @patch('external_storage.api.epc.views.requests.get')
    def test_empty_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"fichierDocumentDescription": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        url = reverse(self.url_pattern, kwargs={"noma": self.noma})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        self.assertEqual(Token.objects.count(), 0)

    @override_settings(
        STUDENT_FILES_API_URL="https://mock-epc.com/{noma}",
        STUDENT_FILES_API_AUTHORIZATION_HEADER="Basic 123654789878789",
    )
    @patch('external_storage.api.epc.views.requests.get')
    def test_null_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"fichierDocumentDescription": None}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        url = reverse(self.url_pattern, kwargs={"noma": self.noma})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        self.assertEqual(Token.objects.count(), 0)
