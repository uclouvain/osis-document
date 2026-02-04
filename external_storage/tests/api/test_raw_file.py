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
from datetime import datetime, timedelta
from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from external_storage.exceptions import TokenNotFound, FileReferenceNotFound
from external_storage.models import Token
from osis_document.exceptions import TokenExpired


class RawFileViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.client = APIClient()
        cls.url_pattern = "external_storage:raw-file"

    def _create_token(self):
        metadata = {
            "path": f"{Path(__file__).parent.parent}/assets/file.txt",
            "name": 'file_sample.txt'
        }

        expires_at = datetime.now() + timedelta(hours=1)
        return Token.objects.create(
            external_storage_name=Token.ExternalStorageName.EPC.name,
            expires_at=expires_at,
            metadata=metadata,
        )

    def test_token_not_found(self):
        url = reverse(self.url_pattern, kwargs={"token": "unknown"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, TokenNotFound.status_code)
        self.assertEqual(response.data["detail"], TokenNotFound.default_detail)

    def test_token_expired(self):
        token = self._create_token()
        token.expires_at = datetime.now() - timedelta(hours=1)
        token.created_at = token.expires_at - timedelta(hours=1)
        token.save()

        url = reverse(self.url_pattern, kwargs={"token": token.token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, TokenExpired.status_code)
        self.assertEqual(response.data["detail"], TokenExpired.default_detail)

    def test_file_reference_not_found_missing_path(self):
        token = self._create_token()
        del token.metadata['path']
        token.save()

        url = reverse(self.url_pattern, kwargs={"token": token.token})

        response = self.client.get(url)
        self.assertEqual(response.status_code, FileReferenceNotFound.status_code)
        self.assertEqual(response.data["detail"], FileReferenceNotFound.default_detail)

    def test_file_reference_not_found_non_existing_file(self):
        token = self._create_token()
        token.metadata.update({
            "path": f"{Path(__file__).parent}/assets/file_not_existing.txt",
        })
        token.save()

        url = reverse(self.url_pattern, kwargs={"token": token.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, FileReferenceNotFound.status_code)
        self.assertEqual(response.data["detail"], FileReferenceNotFound.default_detail)

    @override_settings(OSIS_DOCUMENT_DOMAIN_LIST=[])
    def test_without_download(self):
        token = self._create_token()
        url = reverse(self.url_pattern, kwargs={"token": token.token})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        body = b"".join(response.streaming_content)
        self.assertEqual(body, b"file for testing")

    @override_settings(OSIS_DOCUMENT_DOMAIN_LIST=["https://example.com", "https://foo.bar"])
    def test_ok_with_download_and_content_security_policy_headers(self):
        token = self._create_token()
        url = reverse(self.url_pattern, kwargs={"token": token.token}) + "?dl=1"
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        body = b"".join(response.streaming_content)
        self.assertEqual(body, b"file for testing")

        content_disposition = response["Content-Disposition"]
        self.assertIn("attachment", content_disposition)
        self.assertIn('filename="file_sample.txt"', content_disposition)

        self.assertEqual(
            response["Content-Security-Policy"],
            "frame-ancestors https://example.com https://foo.bar;"
        )
        self.assertEqual(response["X-Frame-Options"], ";")
