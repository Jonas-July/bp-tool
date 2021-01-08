# Generated by Django 3.1.5 on 2021-01-08 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bp', '0004_ag_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='bp',
            name='pretix_event_ag',
            field=models.CharField(blank=True, max_length=50, verbose_name='Pretix Event Slug (AG)'),
        ),
        migrations.AddField(
            model_name='bp',
            name='pretix_event_tl',
            field=models.CharField(blank=True, max_length=50, verbose_name='Pretix Event Slug (TL)'),
        ),
    ]
