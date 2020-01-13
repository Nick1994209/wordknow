# Generated by Django 2.2.3 on 2019-08-05 15:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20190805_1448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learningstatus',
            name='learn_word',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.Word', verbose_name='На этом слове остановились изучать'),
        ),
        migrations.AlterField(
            model_name='learningstatus',
            name='repeat_words',
            field=models.ManyToManyField(blank=True, null=True, to='app.WordStatus'),
        ),
        migrations.AlterField(
            model_name='learningstatus',
            name='repetition_word_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='from_repetition', to='app.WordStatus', verbose_name='На этом слове остановились повторять'),
        ),
    ]
