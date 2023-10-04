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
from typing import List, Dict
from uuid import UUID

from django.conf import settings
from django.db.models import Q
from pypdf import PaperSize, PageObject, PdfReader, PdfWriter

from osis_document.contrib.post_processing.processor import Processor
from osis_document.enums import PostProcessingType
from osis_document.exceptions import FormatInvalidException, MissingFileException, InvalidMergeFileDimension
from osis_document.models import Upload
from osis_document.utils import stringify_uuid_and_check_uuid_validity


class Cloner(Processor):
    type = PostProcessingType.MERGE.name

    def process(
        self,
        upload_objects_uuids: list,
        output_filename: str = None,
    ) -> Dict[str, List[UUID]]:
        input_files = Upload.objects.filter(
            Q(uuid__in=upload_objects_uuids) | Q(post_processing_output_files__uuid__in=upload_objects_uuids)
        ).distinct('uuid')

        upload_objects_str_uuids = []

        for upload_object_uuid in upload_objects_uuids:
            stringify_uuid = stringify_uuid_and_check_uuid_validity(upload_object_uuid)
            if stringify_uuid['uuid_valid']:
                upload_objects_str_uuids.append(stringify_uuid['uuid_stringify'])

        if len(input_files) != len(upload_objects_uuids) != len(upload_objects_str_uuids):
            raise MissingFileException

        # TODO

        return {
            'upload_objects': [],
            'post_processing_objects': [],
        }

    @staticmethod
    def _get_output_filename(output_filename: str = None):
        if output_filename:
            return f"{output_filename}{uuid.uuid4()}.pdf"
        return f"clone_{uuid.uuid4()}.pdf"

cloner = Cloner()
