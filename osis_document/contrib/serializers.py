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

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from osis_document.validators import TokenValidator


class FileField(serializers.ListField):
    default_error_messages = {
        'invalid_token': _('Invalid token'),
    }

    def __init__(self, *args, **kwargs):
        if not isinstance(kwargs['child'], serializers.CharField):
            # ModelSerializer may instantiate the child field with UUIDField, messing with our token logic
            kwargs['child'] = serializers.CharField(
                **{
                    attr: getattr(kwargs['child'], attr)
                    for attr in [
                        'read_only',
                        'write_only',
                        'required',
                        'default',
                        'initial',
                        'source',
                        'label',
                        'help_text',
                        'style',
                        'error_messages',
                        'validators',
                        'allow_null',
                    ]
                }
            )
        super().__init__(*args, **kwargs)
        if not any(isinstance(validator, TokenValidator) for validator in self.validators):
            self.validators.append(TokenValidator(message=self.error_messages['invalid_token']))
