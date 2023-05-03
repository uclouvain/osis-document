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
import uuid
from pathlib import Path
from typing import List
from uuid import UUID

from django.conf import settings
from django.db.models import Q
from pypdf import PdfMerger

from osis_document.contrib.post_processing.processor import Processor
from osis_document.enums import PostProcessingType
from osis_document.exceptions import FormatInvalidException, MissingFileException
from osis_document.models import Upload


class Merger(Processor):
    type = PostProcessingType.MERGE.name

    def process(self, input_uuid_files: list, filename=None) -> List[UUID]:
        input_files = Upload.objects.filter(
            Q(uuid__in=input_uuid_files) | Q(output_files__uuid__in=input_uuid_files)
        ).distinct('uuid')
        if len(input_files) != len(input_uuid_files):
            raise MissingFileException

        pdf_merger = PdfMerger()
        for file in input_files:
            if file.mimetype != "application/pdf":
                raise FormatInvalidException
            pdf_merger.append(file.file.path)
        path = Path(settings.OSIS_UPLOAD_FOLDER) / self._get_output_filename(filename)
        pdf_merger.write(path)
        pdf_merger.close()

        pdf_upload_object = self._create_upload_instance(path=path)
        self._create_post_processing_instance(input_files=input_files, output_file=pdf_upload_object)
        return [pdf_upload_object.uuid]

    @staticmethod
    def _get_output_filename(filename: str):
        if filename:
            return f"{filename}.pdf"
        return f"merge_{uuid.uuid4()}.pdf"


merger = Merger()
