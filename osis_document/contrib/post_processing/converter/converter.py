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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from uuid import UUID

from django.core.files import File

from osis_document.enums import PostProcessingType
from osis_document.models import Upload, PostProcessing
from osis_document.utils import calculate_hash


class Converter(ABC):
    @abstractmethod
    def convert(self, upload_input_object: Upload, output_filename=None) -> UUID:
        pass

    @staticmethod
    @abstractmethod
    def get_supported_formats() -> List:
        pass

    @staticmethod
    @abstractmethod
    def _get_output_filename(output_filename: str, upload_input_object: Upload) -> str:
        pass

    @staticmethod
    def _create_upload_instance(path: str) -> Upload:
        with Path(path).open(mode='rb') as f:
            file = File(f, name=Path(path).name)
            instance = Upload(
                mimetype="application/pdf",
                size=file.size,
                metadata={'hash': calculate_hash(file), 'name': file.name},
            )
            instance.file = Path(path).name
            instance.file.file = file
            instance.save()
            return instance

    @staticmethod
    def _create_post_processing_instance(upload_input_object: Upload, upload_output_object: Upload) -> PostProcessing:
        instance = PostProcessing(type=PostProcessingType.CONVERT.name)
        instance.save()
        instance.input_files.add(upload_input_object)
        instance.output_files.add(upload_output_object)
        return instance
