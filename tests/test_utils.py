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

from django.test import TestCase

from osis_document.tests.factories import TokenFactory, UploadFactory
from osis_document.utils import is_uuid, get_metadata


class IsUuidTestCase(TestCase):
    def test_is_uuid(self):
        self.assertFalse(is_uuid('foobar'))
        self.assertFalse(is_uuid(''))
        self.assertFalse(is_uuid(152))
        self.assertFalse(is_uuid(None))
        self.assertTrue(is_uuid('12345678-1234-5678-1234-567812345678'))


class MetadataTestCase(TestCase):
    def test_with_token(self):
        token = TokenFactory()
        self.assertEqual(
            get_metadata(token.token),
            {'mimetype': 'application/pdf', 'size': 1024},
        )

    def test_with_uuid(self):
        upload = UploadFactory()
        self.assertEqual(
            get_metadata(upload.uuid),
            {'mimetype': 'application/pdf', 'size': 1024},
        )
