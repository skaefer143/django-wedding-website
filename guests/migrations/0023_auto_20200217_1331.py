# Generated by Django 2.2.3 on 2020-02-17 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guests', '0022_party_reminder_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='party',
            name='received_gifts',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='party',
            name='thank_you_sent',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]