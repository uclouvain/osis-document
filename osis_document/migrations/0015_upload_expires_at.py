# Generated by Django 3.2.21 on 2023-11-07 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('osis_document', '0014_auto_20231016_1637'),
    ]

    operations = [
        migrations.AddField(
            model_name='upload',
            name='expires_at',
            field=models.DateField(blank=True, null=True, verbose_name='Expires at'),
        ),
    ]
