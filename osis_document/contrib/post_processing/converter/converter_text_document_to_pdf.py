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
import os
import subprocess
from os.path import splitext
from typing import List
from uuid import UUID

from osis_document.contrib.post_processing.converter.converter import Converter
from osis_document.exceptions import FormatInvalidException, ConversionError
from osis_document.models import Upload

from backoffice.settings.base import OSIS_UPLOAD_FOLDER
from .converter_registry import converter_registry


class ConverterTextDocumentToPdf(Converter):
    def convert(self, upload_input_object: Upload, output_filename=None) -> UUID:
        if upload_input_object.mimetype not in self.get_supported_formats():
            raise FormatInvalidException
        try:
            new_file_name = self._get_output_filename(output_filename=output_filename,
                                                      upload_input_object=upload_input_object
                                                      )
            command = f'lowriter --headless --convert-to pdf:writer_pdf_Export --outdir {OSIS_UPLOAD_FOLDER} {upload_input_object.file.path}'
            subprocess.run(command, shell=True)

            os.rename(f'{splitext(upload_input_object.file.path)[0]}.pdf', f'{OSIS_UPLOAD_FOLDER}{new_file_name}')
            pdf_upload_object = self._create_upload_instance(path=f'{OSIS_UPLOAD_FOLDER}{new_file_name}')
            self._create_post_processing_instance(upload_input_object=upload_input_object,
                                                  upload_output_object=pdf_upload_object
                                                  )
            return pdf_upload_object.uuid
        except Exception:
            raise ConversionError

    @staticmethod
    def get_supported_formats() -> List:
        return ['text/plain', 'application/msword',
                'application/vnd.oasis.opendocument.text',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

    @staticmethod
    def _get_output_filename(output_filename: str, upload_input_object: Upload) -> str:
        if output_filename:
            return output_filename + '.pdf'
        else:
            return splitext(upload_input_object.metadata['name'])[0] + '.pdf'


converter_registry.add_converter(ConverterTextDocumentToPdf())
