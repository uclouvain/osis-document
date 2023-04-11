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
import string
from pathlib import Path

import factory
from django.core.files import File
from factory.fuzzy import FuzzyText

from backoffice.settings.base import OSIS_UPLOAD_FOLDER
from osis_document.enums import TokenAccess
from osis_document.models import Token, Upload
from osis_document.utils import calculate_hash


class PdfUploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    file = factory.django.FileField(data=b'hello world', filename='the_file.pdf')
    size = 1024
    mimetype = 'application/pdf'
    metadata = {
        'hash': 'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9',
        'name': 'the_file.pdf',
    }


class TextDocumentUploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    file = File(Path(OSIS_UPLOAD_FOLDER + 'OSIS-Document.docx').open(mode='rb'), name='a_DOCX_file.docx')
    size = file.size
    mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    metadata = {
        'hash': calculate_hash(file),
        'name': 'a_DOCX_file.docx',
    }


class CorrectPDFUploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    file = File(Path(OSIS_UPLOAD_FOLDER + 'file-sample_1MB_doc.pdf').open(mode='rb'), name='a_PDF_file.pdf')
    size = file.size
    mimetype = 'application/pdf'
    metadata = {
        'hash': calculate_hash(file),
        'name': 'a_PDF_file.pdf',
    }


class ImageUploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    file = factory.django.ImageField(filename='the_file.jpg')
    size = 1024
    mimetype = 'image/jpeg'
    metadata = {
        'hash': '50d858e0985ecc7f60418aaf0cc5ab587f42c2570a884095a9e8ccacd0f6545c',
        'name': 'the_file.jpg',
    }


class BadExtensionUploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    file = File(Path(OSIS_UPLOAD_FOLDER + 'sample-zip-file.zip').open(mode='rb'), name='sample-zip-file.zip')
    size = 380
    mimetype = "application/zip"
    metadata = {
        'hash': calculate_hash(file),
        'name': 'sample-zip-file.zip',
    }


class WriteTokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Token

    token = FuzzyText(length=154, chars=string.ascii_letters + string.digits + ':-')
    upload = factory.SubFactory(PdfUploadFactory)
    access = TokenAccess.WRITE.name


class ReadTokenFactory(WriteTokenFactory):
    access = TokenAccess.READ.name
