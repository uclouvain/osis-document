# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.forms import modelform_factory
from django.test import TestCase, override_settings
from django.utils.translation import gettext as _

from osis_document.contrib import FileField
from osis_document.enums import FileStatus, DocumentExpirationPolicy
from osis_document.models import Token, Upload
from osis_document.tests.document_test.models import TestDocument
from osis_document.tests.factories import WriteTokenFactory
from osis_document.utils import confirm_upload


@override_settings(
    OSIS_DOCUMENT_BASE_URL='http://dummyurl.com/document/',
    OSIS_DOCUMENT_API_SHARED_SECRET='very-secret',
)
class FieldTestCase(TestCase):
    @patch('osis_document.api.utils.get_remote_metadata')
    @patch('osis_document.api.utils.get_several_remote_metadata')
    def test_model_form_validation(
        self,
        get_several_remote_metadata,
        get_remote_metadata,
    ):
        get_remote_metadata.return_value = None
        get_several_remote_metadata.return_value = None
        ModelForm = modelform_factory(TestDocument, fields='__all__')

        form = ModelForm({})
        self.assertTrue(form.is_valid())

        form = ModelForm({'documents_0': []})
        self.assertFalse(form.is_valid())

        form = ModelForm({'documents_0': 'something'})
        self.assertFalse(form.is_valid())
        self.assertIn(_("File upload is either non-existent or has expired"), form.errors['documents'][0])

        token = WriteTokenFactory()

        get_remote_metadata.return_value = {
            "size": 1024,
            "mimetype": "image/jpeg",
            "name": "test.jpg",
            "url": "http://dummyurl.com/document/file/AZERTYIOOHGFDFGHJKLKJHG",
        }
        get_several_remote_metadata.return_value = {
            str(token.token): get_remote_metadata.return_value
        }
        form = ModelForm({'documents_0': token.token})
        self.assertTrue(form.is_valid(), form.errors)

    @patch('osis_document.api.utils.get_remote_metadata')
    @patch('osis_document.api.utils.get_several_remote_metadata')
    @patch('osis_document.api.utils.confirm_remote_upload')
    def test_model_form_submit(
        self,
        confirm_remote_upload,
        get_several_remote_metadata,
        get_remote_metadata,
    ):
        # For the sake of simplicity, let's say a remote confirm is local
        confirm_remote_upload.side_effect = lambda token, upload_to, **_: str(confirm_upload(token, upload_to))

        token = WriteTokenFactory()
        get_remote_metadata.return_value = {
            "size": 1024,
            "mimetype": "image/jpeg",
            "name": "test.jpg",
            "url": "http://dummyurl.com/document/file/AZERTYIOOHGFDFGHJKLKJHG",
        }
        get_several_remote_metadata.return_value = {
            str(token.token): get_remote_metadata.return_value
        }
        ModelForm = modelform_factory(TestDocument, fields='__all__')

        form = ModelForm({'documents_0': token.token})
        self.assertTrue(form.is_valid(), form.errors)
        # 7 queries (
            # one for loading obj,
            # one for upload state,
            # one for deleting token,
            # one for getting old documents fields value,
            # one for getting old other_documents fields value,
            # one for getting old documents_expirables fields value,
            # one for saving obj
        # )
        with self.assertNumQueries(7):
            document = form.save()

        self.assertIsNone(Token.objects.filter(token=token.token).first())
        token.upload.refresh_from_db()
        self.assertEqual(len(document.documents), 1)
        self.assertEqual(token.upload.status, FileStatus.UPLOADED.name)

        token = WriteTokenFactory(upload=Upload.objects.first())
        get_several_remote_metadata.return_value = {
            str(token.token): get_remote_metadata.return_value
        }
        form = ModelForm({'documents_0': token.token})
        # 3 queries (
            # one for loading obj,
            # one for deleting token,
            # one for getting old documents fields value,
            # one for getting old other_documents fields value,
            # one for getting old documents_expirables fields value,
            # one for saving obj
        # )
        with self.assertNumQueries(6):
            document = form.save()

        # Saving an empty form should empty the field
        form = ModelForm({}, instance=document)
        self.assertTrue(form.is_valid(), form.errors)
        document = form.save()
        self.assertEqual(len(document.documents), 0)

    @patch('osis_document.api.utils.get_remote_metadata')

    @patch('osis_document.api.utils.get_several_remote_metadata')
    def test_model_form_confirms_remotely_with_correct_path(
        self,
        get_several_remote_metadata,
        get_remote_metadata,
    ):
        token = WriteTokenFactory()

        get_remote_metadata.return_value = {"name": "test.jpg"}
        get_several_remote_metadata.return_value = {
            str(token.token): get_remote_metadata.return_value
        }
        ModelForm = modelform_factory(TestDocument, fields='__all__')
        form = ModelForm({'documents_0': token.token})
        self.assertTrue(form.is_valid(), form.errors)

        with patch('requests.post') as request_mock:
            request_mock.return_value.json.return_value = {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            form.save()
        expected_url = f'http://dummyurl.com/document/confirm-upload/{token.token}'
        request_mock.assert_called_with(expected_url, json={'upload_to': 'path'}, headers={'X-Api-Key': 'very-secret'})

    @patch('osis_document.api.utils.get_remote_metadata')

    @patch('osis_document.api.utils.get_several_remote_metadata')
    def test_model_form_confirms_remotely_with_document_expiration_policy(
        self,
        get_several_remote_metadata,
        get_remote_metadata,
    ):
        token = WriteTokenFactory()

        get_remote_metadata.return_value = {"name": "test.jpg"}
        get_several_remote_metadata.return_value = {
            str(token.token): get_remote_metadata.return_value
        }
        ModelForm = modelform_factory(TestDocument, fields='__all__')

        form = ModelForm({'documents_expirables_0': token.token})
        self.assertTrue(form.is_valid(), form.errors)

        with patch('requests.post') as request_mock:
            request_mock.return_value.json.return_value = {"uuid": "bbc1ba15-42d2-48e9-9884-7631417bb1e1"}
            form.save()
        expected_url = f'http://dummyurl.com/document/confirm-upload/{token.token}'
        request_mock.assert_called_with(
            expected_url,
            json={
                'upload_to': 'path',
                'document_expiration_policy': DocumentExpirationPolicy.EXPORT_EXPIRATION_POLICY.value,
            },
            headers={'X-Api-Key': 'very-secret'}
        )

    def test_update_or_create(self):
        doc_pk = TestDocument.objects.create(documents=[WriteTokenFactory().upload_id]).pk

        instance, updated = TestDocument.objects.update_or_create(pk=doc_pk)
        self.assertFalse(updated)
        self.assertEqual(len(instance.documents), 1)

        instance = TestDocument.objects.get(pk=doc_pk)
        self.assertEqual(len(instance.documents), 1)

    def test_create_from_uuid_orm(self):
        doc_pk = TestDocument.objects.create(documents=[WriteTokenFactory().upload_id]).pk

        instance = TestDocument.objects.filter(pk=doc_pk).first()
        self.assertIsNotNone(instance)
        self.assertEqual(len(instance.documents), 1)

    @patch('osis_document.api.utils.get_remote_metadata')
    @patch('osis_document.api.utils.get_several_remote_metadata')
    def test_create_from_uuid_saving(
        self,
        get_several_remote_metadata,
        get_remote_metadata,
    ):
        token = WriteTokenFactory()

        get_remote_metadata.return_value = {
            "size": 1024,
            "mimetype": "image/jpeg",
            "name": "test.jpg",
            "url": "http://dummyurl.com/document/file/AZERTYIOOHGFDFGHJKLKJHG",
        }
        get_several_remote_metadata.return_value = {
            str(token.token): get_remote_metadata.return_value
        }
        instance = TestDocument(documents=[token.token])
        with patch('osis_document.api.utils.confirm_remote_upload') as confirm_remote_upload:
            # For the sake of simplicity, let's say a remote confirm is local
            confirm_remote_upload.side_effect = lambda token, upload_to, **_: str(confirm_upload(token, upload_to))
            instance.save()

        self.assertEqual(len(instance.documents), 1)
        self.assertIsInstance(instance.documents[0], uuid.UUID)

        instance = TestDocument.objects.filter(pk=instance.pk).first()
        self.assertIsNotNone(instance)
        self.assertEqual(len(instance.documents), 1)
        self.assertIsInstance(instance.documents[0], uuid.UUID)

    @patch('osis_document.api.utils.get_remote_metadata')
    @patch('osis_document.api.utils.get_several_remote_metadata')
    def test_field_having_requirements(
        self,
        get_several_remote_metadata,
        get_remote_metadata,
    ):
        token = WriteTokenFactory()

        get_remote_metadata.return_value =  {
                "size": 1024,
                "mimetype": "image/jpeg",
                "name": "test.jpg",
                "url": "http://dummyurl.com/document/file/AZERTYIOOHGFDFGHJKLKJHG",
            }
        get_several_remote_metadata.return_value = {
            str(token.token): get_remote_metadata.return_value,
        }
        upload_id = token.upload_id

        field = FileField(min_files=1)
        with self.assertRaises(ValidationError):
            field.clean([], None)
        with self.assertRaises(ValidationError):
            field.clean(None, None)
        self.assertEqual(field.clean([upload_id], None), [upload_id])

        field = FileField(min_files=1, blank=True)
        with self.assertRaises(ValidationError):
            field.clean(None, None)
        self.assertEqual(field.clean([], None), [])
        self.assertEqual(field.clean([upload_id], None), [upload_id])

        field = FileField(min_files=1, null=True, blank=True)
        self.assertEqual(field.clean([], None), [])
        self.assertEqual(field.clean([upload_id], None), [upload_id])
