# Generated by Django 3.0.5 on 2020-05-02 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rumors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='truthfulness_points',
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='text',
            name='truthfulness_points',
            field=models.BigIntegerField(default=0),
        ),
    ]
