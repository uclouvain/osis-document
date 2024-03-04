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
from pathlib import Path
from typing import List, Dict
from uuid import UUID

from django.core.files import File
from osis_document.enums import FileStatus
from osis_document.models import PostProcessing, Upload
from osis_document.utils import calculate_hash


class Processor:
    type: str

    @classmethod
    def _create_upload_instance(cls, path: Path, filename: str) -> Upload:
        with path.open(mode='rb') as f:
            file = File(f, name=path.name)
            instance = Upload(
                mimetype="application/pdf",
                size=file.size,
                metadata={
                    'hash': calculate_hash(file),
                    'name': filename,
                    'post_processing': f'{cls.__module__}.{cls.__name__}',
                },
                status=FileStatus.UPLOADED.name
            )
            instance.file.save(path.name, file)
            # instance.file.save() also save the instance by default.
            return instance

    @classmethod
    def _create_post_processing_instance(cls, input_files: List[Upload], output_file: Upload) -> PostProcessing:
        instance = PostProcessing(type=cls.type)
        instance.save()
        instance.input_files.add(*input_files)
        instance.output_files.add(output_file)
        return instance

    def process(self, upload_objects_uuids: List[UUID], output_filename: str = None) -> Dict[str, List[UUID]]:
        raise NotImplemented
