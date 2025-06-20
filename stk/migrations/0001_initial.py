# Generated by Django 5.2.1 on 2025-05-24 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserRegistrationData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stk_ad', models.CharField(max_length=150)),
                ('stk_temsilci_ad', models.CharField(max_length=40)),
                ('stk_temsilci_soyad', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('adres', models.TextField()),
                ('cep_telefon', models.CharField(max_length=11)),
                ('stk_turu', models.CharField(max_length=10)),
                ('kutuk_no', models.CharField(blank=True, max_length=10, null=True)),
                ('etebligat', models.CharField(blank=True, max_length=19, null=True)),
                ('faaliyet_belgesi', models.FileField(upload_to='faaliyet_belgeleri/')),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
