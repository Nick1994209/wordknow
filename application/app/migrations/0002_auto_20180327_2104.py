# Generated by Django 2.0.3 on 2018-03-27 21:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='chat_id',
            field=models.CharField(max_length=100, unique=True, verbose_name='ID чата в телеграме'),
        ),
    ]
