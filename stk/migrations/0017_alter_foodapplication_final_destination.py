# Generated by Django 5.2.1 on 2025-06-02 04:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stk', '0016_alter_foodapplication_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foodapplication',
            name='final_destination',
            field=models.CharField(choices=[('awaiting_test_result', 'Test Sonucu Bekleniyor'), ('cold_storage', 'Soğuk Hava Deposu'), ('compost_center', 'Gübre Atık Merkezi'), ('disposal', 'İmha Edilecek'), ('distributed', 'Dağıtıldı')], default='awaiting_test_result', max_length=50),
        ),
    ]
