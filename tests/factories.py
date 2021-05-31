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
from datetime import timedelta

import factory
from django.conf import settings
from django.utils.timezone import now
from factory.fuzzy import FuzzyText

from osis_document.enums import TokenAccess
from osis_document.models import Upload, Token


class PdfUploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    file = factory.django.FileField(data=b'hello world', filename='the_file.pdf')
    size = 1024
    mimetype = 'application/pdf'


class WriteTokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Token

    token = FuzzyText(length=154, chars=string.ascii_letters + string.digits + ':-')
    created_at = factory.LazyFunction(now)
    expires_at = factory.LazyAttribute(
        lambda o: o.created_at + timedelta(seconds=getattr(settings, 'OSIS_DOCUMENT_TOKEN_MAX_AGE', 60 * 15))
    )
    upload = factory.SubFactory(PdfUploadFactory)
    access = TokenAccess.WRITE.name


class ReadTokenFactory(WriteTokenFactory):
    access = TokenAccess.READ.name
