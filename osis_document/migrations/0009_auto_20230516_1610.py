# Generated by Django 3.2.18 on 2023-05-16 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('osis_document', '0008_remove_postprocessasync_input_files'),
    ]

    operations = [
        migrations.AlterField(
            model_name='postprocessasync',
            name='post_processing_object',
            field=models.ManyToManyField(blank=True, related_name='post_processing_object', to='osis_document.PostProcessing', verbose_name='Output'),
        ),
        migrations.AlterField(
            model_name='postprocessing',
            name='input_files',
            field=models.ManyToManyField(related_name='post_processing_input_files', to='osis_document.Upload', verbose_name='Input'),
        ),
        migrations.AlterField(
            model_name='postprocessing',
            name='output_files',
            field=models.ManyToManyField(related_name='post_processing_output_files', to='osis_document.Upload', verbose_name='Output'),
        ),
    ]
