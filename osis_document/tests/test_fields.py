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
from django.forms import modelform_factory
from django.test import TestCase, override_settings
from django.utils.translation import gettext as _

from osis_document.enums import FileStatus
from osis_document.models import Token, Upload
from osis_document.tests.document_test.models import TestDocument
from osis_document.tests.factories import WriteTokenFactory


@override_settings(ROOT_URLCONF='osis_document.tests.document_test.urls',
                   OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/')
class FieldTestCase(TestCase):
    def test_model_form_validation(self):
        ModelForm = modelform_factory(TestDocument, fields='__all__')

        form = ModelForm({})
        self.assertTrue(form.is_valid())

        form = ModelForm({
            'documents_0': [],
        })
        self.assertFalse(form.is_valid())

        form = ModelForm({
            'documents_0': 'something',
        })
        self.assertFalse(form.is_valid())
        self.assertIn(_("File upload is either non-existent or has expired"), form.errors['documents'][0])

        token = WriteTokenFactory()
        form = ModelForm({
            'documents_0': token.token,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_model_form_submit(self):
        ModelForm = modelform_factory(TestDocument, fields='__all__')

        token = WriteTokenFactory()
        form = ModelForm({
            'documents_0': token.token,
        })
        self.assertTrue(form.is_valid(), form.errors)

        # 4 queries (one for loading obj, one for upload state, one for deleting token, one for saving obj)
        with self.assertNumQueries(4):
            document = form.save()

        self.assertIsNone(Token.objects.filter(token=token.token).first())
        token.upload.refresh_from_db()
        self.assertEqual(len(document.documents), 1)
        self.assertEqual(token.upload.status, FileStatus.UPLOADED.name)

        token = WriteTokenFactory(upload=Upload.objects.first())
        form = ModelForm({
            'documents_0': token.token,
        })
        # 4 queries (one for loading obj, one for loading toke, one for deleting token, one for saving obj)
        with self.assertNumQueries(4):
            document = form.save()

        # Saving an empty form should empty the field
        form = ModelForm({}, instance=document)
        self.assertTrue(form.is_valid(), form.errors)
        document = form.save()
        self.assertEqual(len(document.documents), 0)
