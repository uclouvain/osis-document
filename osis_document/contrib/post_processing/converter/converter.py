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
from uuid import UUID

from osis_document.models import Upload, PostProcessing


class Converter(ABC):
    @abstractmethod
    def convert(self, upload_input_object: Upload, output_filename=None) -> UUID:
        pass

    @staticmethod
    @abstractmethod
    def get_supported_format() -> list:
        pass

    @staticmethod
    @abstractmethod
    def _get_output_filename(output_filename: str, upload_input_object: Upload) -> str:
        pass

    @staticmethod
    @abstractmethod
    def _create_upload_instance(path: str) -> Upload:
        pass

    @staticmethod
    @abstractmethod
    def _create_post_processing_instance(upload_input_object: Upload, upload_output_object: Upload) -> PostProcessing:
        pass
