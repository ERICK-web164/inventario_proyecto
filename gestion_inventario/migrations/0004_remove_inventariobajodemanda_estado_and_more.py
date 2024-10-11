# Generated by Django 5.0.7 on 2024-10-01 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_inventario', '0003_productocontinuo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inventariobajodemanda',
            name='estado',
        ),
        migrations.AlterField(
            model_name='pedido',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('en proceso', 'En Proceso'), ('completado', 'Completado'), ('proveedor', 'Proveedor'), ('entregado', 'Entregado'), ('cancelado', 'Cancelado')], default='pendiente', max_length=50),
        ),
    ]