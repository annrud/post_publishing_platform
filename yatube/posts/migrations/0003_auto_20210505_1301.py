# Generated by Django 2.2.6 on 2021-05-05 13:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20210401_1344'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'default_related_name': 'posts', 'ordering': ['-pub_date']},
        ),
    ]
