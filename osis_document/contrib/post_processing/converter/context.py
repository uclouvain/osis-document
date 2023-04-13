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
from uuid import UUID

from osis_document.contrib.post_processing.converter.converter import Converter
from osis_document.models import Upload


class Context:

    def __init__(self, converter: Converter, upload_object: Upload, output_filename: str) -> None:
        self._upload_object = upload_object
        self._converter = converter
        self.output_filename = output_filename

    @property
    def converter(self) -> Converter:
        return self._converter

    @property
    def upload_object(self) -> Upload:
        return self._upload_object

    @converter.setter
    def converter(self, converter: Converter) -> None:
        self._converter = converter

    @upload_object.setter
    def upload_object(self, upload_object: Upload) -> None:
        self._upload_object = upload_object

    def make_conversion(self) -> UUID:
        return self._converter.convert(upload_input_object=self._upload_object, output_filename=self.output_filename)
