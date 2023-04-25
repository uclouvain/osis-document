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
from django.contrib.contenttypes.models import ContentType
from django.core import signing
from django.core.exceptions import FieldDoesNotExist, FieldError
from django.utils.translation import gettext_lazy as _
from osis_document.models import Token, Upload
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class RequestUploadResponseSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="A writing token for the uploaded file")


class ConfirmUploadResponseSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(help_text="The uuid of the persisted file upload")


class DeclareFileAsInfectedSerializer(serializers.Serializer):
    path = serializers.CharField(help_text="The path to the file to declare as infected")

    def validate_path(self, value):
        # Path must exist on the file system and be part of an upload
        upload = Upload.objects.filter(file=value).first()
        if not upload or not upload.file.storage.exists(upload.file.path):
            raise serializers.ValidationError(_("File does not exist"))
        return upload


class ContentTypeSerializer(serializers.Serializer):
    app = serializers.CharField(
        help_text="The name of the application containing the desired model",
        required=True,
    )
    model = serializers.CharField(
        help_text="The name of the desired model",
        required=True,
    )
    field = serializers.CharField(
        help_text="The name of the file field in the desired model",
        required=True,
    )
    instance_filters = serializers.JSONField(
        help_text="Lookup arguments allowing to filter the model instances to return one single object that will be "
        "used to compute the upload directory path (via the 'upload_to' property)",
        required=False,
    )

    def to_internal_value(self, data):
        # Get the content type
        content_type = ContentType(
            app_label=data['app'],
            model=data['model'],
        )
        model_class = content_type.model_class()

        if not model_class:
            raise ValidationError("The following model cannot be found: " + "'{app}:{model}'".format_map(data))

        internal_value = {
            'content_type': content_type,
        }

        # Get the file field thanks to the content type and the specified name
        try:
            internal_value['content_type_field'] = model_class._meta.get_field(data['field'])

        except FieldDoesNotExist:
            raise ValidationError(
                "The following field cannot be found: " + "'{field}' (in '{app}:{model}')".format_map(data),
            )

        # Get the instance thanks to the content type and the specified filters
        if data.get('instance_filters'):
            try:
                internal_value['instance'] = content_type.get_object_for_this_type(**data['instance_filters'])
            except FieldError:
                raise ValidationError('The provided filters contain an unknown field')
            except (model_class.DoesNotExist, model_class.MultipleObjectsReturned):
                raise ValidationError(
                    'Impossible to find one single object on which to compute the upload directory path',
                )

        return internal_value


class ConfirmUploadRequestSerializer(serializers.Serializer):
    related_model = ContentTypeSerializer(
        help_text="The related model having the file field",
        required=False,
    )
    upload_to = serializers.CharField(
        help_text="This attribute provides a way of setting the upload directory",
        required=False,
    )

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        # If the 'upload_to' property isn't specified, maybe we can get it from the related model
        if not internal_value.get('upload_to') and internal_value.get('related_model'):
            internal_value['upload_to'] = getattr(
                internal_value['related_model']['content_type_field'],
                'upload_to',
                None,
            )

        return internal_value


class MetadataSerializer(serializers.Serializer):
    size = serializers.IntegerField(help_text="The size, in bytes, of the file")
    mimetype = serializers.CharField(help_text="The file's mimetype")
    name = serializers.CharField(help_text="The file's name")
    uploaded_at = serializers.DateTimeField(help_text="The file's upload date")
    url = serializers.CharField(help_text="An url for direct access to the raw file")


class ChangeMetadataSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="The file's new name")


class RotateImageSerializer(serializers.Serializer):
    rotate = serializers.IntegerField(help_text="The rotation requested, in degrees, usually 90, 180 or 270")


class RotateImageResponseSerializer(serializers.Serializer):
    token = serializers.CharField(help_text="A fresh writing token for the rotated file")


class TokenListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        tokens = [Token(**(self.child.complete_new_validated_data(token))) for token in validated_data]
        return Token.objects.bulk_create(tokens)


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
        list_serializer_class = TokenListSerializer

    @staticmethod
    def complete_new_validated_data(validated_data):
        validated_data['token'] = signing.dumps(str(validated_data['upload_id']))
        return validated_data

    def create(self, validated_data):
        validated_data = self.complete_new_validated_data(validated_data)
        return super().create(validated_data)


class PostProcessing(serializers.Serializer):
    files_uuid = serializers.ListField(
        help_text="A list of files UUID",
        required=True,
    )
    post_process_types = serializers.ListField(
        help_text="A list of actions to perform on the files",
        required=True,
    )
