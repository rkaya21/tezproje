# Generated by Django 5.2.1 on 2025-06-01 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stk', '0009_foodapplication_courier_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='role',
            field=models.CharField(choices=[('stk', 'STK'), ('courier', 'Kurye'), ('admin', 'Yönetici')], default='stk', max_length=20),
        ),
    ]
