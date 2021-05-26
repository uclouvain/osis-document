# Generated by Django 2.2.13 on 2021-05-20 12:15

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid

import osis_document.enums


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Upload',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False, verbose_name='UUID')),
                ('file', models.FileField(upload_to='', verbose_name='File')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='Uploaded at')),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modified at')),
                ('mimetype', models.CharField(max_length=255, verbose_name='MIME Type')),
                ('size', models.IntegerField(verbose_name='Size (in bytes)')),
                ('status', models.CharField(choices=[('REQUESTED', 'Requested'), ('UPLOADED', 'Uploaded')], default=osis_document.enums.FileStatus('Requested'), max_length=255, verbose_name='Status')),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField(default=dict, verbose_name='Metadata')),
            ],
            options={
                'verbose_name': 'Upload',
            },
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=1024, verbose_name='Token')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('access', models.CharField(choices=[('READ', 'Read'), ('WRITE', 'Write')], max_length=255, verbose_name='Access type')),
                ('upload', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tokens', to='osis_document.Upload', verbose_name='Upload')),
            ],
        ),
    ]
