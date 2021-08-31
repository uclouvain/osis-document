# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.core import signing
from django.urls import reverse
from rest_framework import serializers

from osis_document.models import Token
from osis_document.utils import get_token


class TokenSerializer(serializers.ModelSerializer):
    token = serializers.CharField(read_only=True)
    upload_id = serializers.UUIDField(required=True)

    class Meta:
        model = Token
        fields = [
            'token',
            'upload_id',
            'access',
            'expires_at',
        ]

    def create(self, validated_data):
        validated_data['token'] = signing.dumps(str( validated_data['upload_id']))
        return super().create(validated_data)


class UploadUUIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = [
            'upload_id',
        ]


class MetadataSerializer(serializers.Serializer):
    size = serializers.IntegerField(read_only=True)
    mimetype = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True)

    def to_representation(self, instance):
        url = reverse('osis_document:get-file', kwargs={'token': get_token(instance.uuid)})
        return {
            'size': instance.size,
            'mimetype': instance.mimetype,
            'name': instance.file.name,
            'url': url,
            **instance.metadata,
        }
