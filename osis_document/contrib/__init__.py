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
from osis_document.contrib.fields import FileField
from osis_document.contrib.forms import FileUploadField
from osis_document.contrib.post_processing.converter_registry import ConverterRegistry

from osis_document.contrib.post_processing.converters.converter import Converter
from osis_document.contrib.post_processing.converters.converter_image_to_pdf import ConverterImageToPdf
from osis_document.contrib.post_processing.converters.converter_text_document_to_pdf import ConverterTextDocumentToPdf
from osis_document.contrib.post_processing.merger import merger
from osis_document.contrib.serializers import FileField as FileFieldSerializer
from osis_document.contrib.widgets import FileUploadWidget

__all__ = [
    'FileField',
    'FileUploadField',
    'FileUploadWidget',
    'FileFieldSerializer',
    'merger',
    'ConverterRegistry',
    'Converter',
    'ConverterImageToPdf',
    'ConverterTextDocumentToPdf',
]
