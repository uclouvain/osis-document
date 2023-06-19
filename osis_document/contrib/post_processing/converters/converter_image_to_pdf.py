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
from pathlib import Path
from typing import List

from PIL import Image
from django.conf import settings

from osis_document.exceptions import ConversionError
from osis_document.models import Upload
from .converter import Converter
from ..converter_registry import converter_registry


class ConverterImageToPdf(Converter):
    def convert(self, upload_input_object: Upload, output_filename: str) -> Path:
        try:
            image = Image.open(upload_input_object.file)
            image_pdf = image.convert('RGB')
            new_filepath = Path(settings.MEDIA_ROOT) / output_filename
            image_pdf.save(new_filepath, quality=95, resolution=19.0, optimize=True)
            return new_filepath
        except Exception:
            raise ConversionError

    @staticmethod
    def get_supported_formats() -> List[str]:
        return ['image/png', 'image/jpg', 'image/jpeg']


converter_registry.add_converter(ConverterImageToPdf())
