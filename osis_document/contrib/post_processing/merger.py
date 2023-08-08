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
from pypdf import PaperSize, PageObject, PdfReader, PdfWriter

from django.conf import settings
from django.db.models import Q
from osis_document.contrib.post_processing.processor import Processor
from osis_document.enums import PostProcessingType
from osis_document.exceptions import FormatInvalidException, MissingFileException, InvalidMergeFileDimension
from osis_document.models import Upload


class Merger(Processor):
    type = PostProcessingType.MERGE.name

    def process(self, upload_objects_uuids: list, output_filename=None, pages_dimension=None) -> List[UUID]:
        input_files = Upload.objects.filter(
            Q(uuid__in=upload_objects_uuids) | Q(output_files__uuid__in=upload_objects_uuids)
        ).distinct('uuid')
        if len(input_files) != len(upload_objects_uuids):
            raise MissingFileException

        pdf_writer = PdfWriter()
        for file in input_files:
            if file.mimetype != "application/pdf":
                raise FormatInvalidException
            reader = PdfReader(stream=file.file.path)
            if pages_dimension:
                pdf_writer = self._merge_and_change_pages_dimension(
                    writer_instance=pdf_writer,
                    pages=reader.pages,
                    dimension=pages_dimension
                )
            else:
                pdf_writer.append_pages_from_reader(reader=reader)
        path = Path(settings.MEDIA_ROOT) / self._get_output_filename(output_filename)
        pdf_writer.write(path)
        pdf_writer.close()
        pdf_upload_object = self._create_upload_instance(path=path)
        self._create_post_processing_instance(input_files=input_files, output_file=pdf_upload_object)
        return [pdf_upload_object.uuid]

    @staticmethod
    def _merge_and_change_pages_dimension(writer_instance: PdfWriter, pages: List[PageObject], dimension):
        try :
            expected_page_width = getattr(PaperSize, dimension).width
        except AttributeError:
            raise InvalidMergeFileDimension
        for page in pages:
            current_page_width = page.mediabox.width
            if current_page_width != expected_page_width:
                y_translation_factor = expected_page_width / current_page_width
                page.scale_to(
                    expected_page_width,
                    page.mediabox.height * y_translation_factor,
                )
            writer_instance.add_page(page=page)
        return writer_instance

    @staticmethod
    def _get_output_filename(output_filename: str = None):
        if output_filename is not None:
            return f"{output_filename}.pdf"
        return f"merge_{uuid.uuid4()}.pdf"


merger = Merger()
