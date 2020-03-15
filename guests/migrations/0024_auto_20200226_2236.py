# Generated by Django 2.2.4 on 2020-02-27 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guests', '0023_auto_20200217_1331'),
    ]

    operations = [
        migrations.AddField(
            model_name='party',
            name='receives_a_thank_you_note',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='party',
            name='thank_you_extra_sentence',
            field=models.TextField(blank=True, null=True),
        ),
    ]