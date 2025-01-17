# Generated by Django 5.0.7 on 2024-09-23 01:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_inventario', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='actividad',
            name='area',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='actividad',
            name='cambio_valor',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='actividad',
            name='inventario_nombre',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='actividad',
            name='fecha_hora',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='actividad',
            name='tipo_accion',
            field=models.CharField(max_length=50),
        ),
    ]
