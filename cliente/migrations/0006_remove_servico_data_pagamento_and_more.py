# Generated by Django 5.1.5 on 2025-02-17 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cliente', '0005_servico_data_pagamento'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servico',
            name='data_pagamento',
        ),
        migrations.AddField(
            model_name='pagamento',
            name='data_pagamento',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
