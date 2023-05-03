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
from pathlib import Path
from typing import List

from django.conf import settings

from osis_document.exceptions import ConversionError, FormatInvalidException
from osis_document.models import Upload
from .converter import Converter
from ..converter_registry import converter_registry


class ConverterTextDocumentToPdf(Converter):
    def convert(self, upload_input_object: Upload, output_filename: str) -> Path:
        if upload_input_object.mimetype not in self.get_supported_formats():
            raise FormatInvalidException
        try:
            command = (
                f'lowriter '
                f'--headless '
                f'--convert-to pdf:writer_pdf_Export '
                f'--outdir {settings.OSIS_UPLOAD_FOLDER} {upload_input_object.file.path}'
            )
            result = subprocess.run(command, shell=True)
            if result.returncode:
                raise ConversionError(result.stderr)

            new_filepath = Path(settings.OSIS_UPLOAD_FOLDER) / output_filename
            os.rename(f'{splitext(upload_input_object.file.path)[0]}.pdf', new_filepath)
            return new_filepath
        except Exception as e:
            raise ConversionError(str(e))

    @staticmethod
    def get_supported_formats() -> List[str]:
        return [
            'text/plain',
            'application/msword',
            'application/vnd.oasis.opendocument.text',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        ]


converter_registry.add_converter(ConverterTextDocumentToPdf())
