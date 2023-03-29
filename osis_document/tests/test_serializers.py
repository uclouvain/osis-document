# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework import serializers

from osis_document.tests.document_test.models import TestDocument


class _TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestDocument
        fields = ['documents']


@override_settings(OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class SerializerTestCase(TestCase):
    def setUp(self):
        patcher = patch(
            'osis_document.api.utils.get_remote_metadata',
            return_value={
                "size": 1024,
                "mimetype": "application/pdf",
                "name": "test.pdf",
                "url": "http://dummyurl.com/document/file/AZERTYIOOHGFDFGHJKLKJHG",
            },
        )
        self.mock_remote_metadata = patcher.start()
        self.addCleanup(patcher.stop)

    def test_serializer_validator_is_called_without_error(self):
        self.assertTrue(_TestSerializer(data={'documents': ['test']}).is_valid())
        self.mock_remote_metadata.assert_called()

    def test_serializer_validator_is_called_with_error(self):
        self.mock_remote_metadata.return_value = None
        self.assertFalse(_TestSerializer(data={'documents': ['test']}).is_valid())
        self.mock_remote_metadata.assert_called()

    def test_serializer_validator_is_called_with_no_value(self):
        self.mock_remote_metadata.return_value = None
        self.assertTrue(_TestSerializer(data={'documents': []}).is_valid())
        self.mock_remote_metadata.assert_not_called()
