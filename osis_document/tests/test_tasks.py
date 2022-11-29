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
from unittest import mock

from django.test import TestCase
from django.utils.datetime_safe import datetime

from osis_document.enums import FileStatus
from osis_document.models import Token, Upload
from osis_document.tasks import cleanup_old_uploads
from osis_document.tests.factories import WriteTokenFactory, PdfUploadFactory


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
