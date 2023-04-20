# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List
from uuid import UUID

from osis_document.contrib.post_processing.converter.converter import Converter
from osis_document.exceptions import FormatInvalidException
from osis_document.models import Upload


class ConverterRegistry:
    """Register and launch appropriate converters"""
    converters = []

    def add_converter(self, converter: Converter) -> None:
        self.converters.append(converter)

    def process(self, upload_objects_uuid: List[UUID], output_filename: str) -> UUID:
        upload_objects = Upload.objects.filter(uuid__in=upload_objects_uuid)
        for converter in self.converters:
            for upload_object in upload_objects:
                if upload_object.mimetype in converter.get_supported_formats():
                    return converter.convert(upload_input_object=upload_object, output_filename=output_filename)
        raise FormatInvalidException


converter_registry = ConverterRegistry()

