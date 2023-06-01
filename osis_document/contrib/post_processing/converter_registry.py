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
from os.path import splitext
from typing import List, Optional, Dict
from uuid import UUID

from .converters.converter import Converter
from osis_document.contrib.post_processing.processor import Processor
from osis_document.enums import PostProcessingType
from osis_document.exceptions import FormatInvalidException, MissingFileException
from osis_document.models import Upload


class ConverterRegistry(Processor):
    """Register and launch appropriate converters"""

    type = PostProcessingType.CONVERT.name

    converters = []

    def add_converter(self, converter: Converter) -> None:
        self.converters.append(converter)

    def process(self, upload_objects_uuids: List[UUID], output_filename: Optional[str] = None) -> Dict[str, List[UUID]]:
        upload_objects = Upload.objects.filter(uuid__in=upload_objects_uuids)
        process_return = {
            'upload_objects': [],
            'post_processing_objects': []
        }
        converter: Converter
        for converter in self.converters:
            for upload_object in upload_objects:
                if upload_object.mimetype == 'application/pdf' and upload_object.uuid not in process_return['upload_objects']:
                    process_return['upload_objects'].append(upload_object.uuid)

                if upload_object.mimetype in converter.get_supported_formats():
                    new_file_name = self._get_output_filename(output_filename, upload_object)
                    path = converter.convert(upload_input_object=upload_object, output_filename=new_file_name)
                    new_instance = self._create_upload_instance(path)
                    process_return['post_processing_objects'].append(
                        self._create_post_processing_instance(
                            input_files=[upload_object],
                            output_file=new_instance
                        ).uuid
                    )
                    process_return['upload_objects'].append(new_instance.uuid)

        if not process_return:
            raise FormatInvalidException

        if len(upload_objects_uuids) != len(process_return['upload_objects']):
            raise MissingFileException

        return process_return

    @staticmethod
    def _get_output_filename(output_filename: Optional[str], upload_input_object: Upload) -> str:
        if output_filename:
            return output_filename + '.pdf'
        return splitext(upload_input_object.metadata['name'])[0] + '.pdf'


converter_registry = ConverterRegistry()
