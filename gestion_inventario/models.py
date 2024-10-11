#models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import os
from django.conf import settings
import shutil
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db.models import Sum

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    rubro = models.CharField(max_length=100)
    ruc_dni = models.CharField(max_length=20)
    fecha_registro = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nombre
    
class Usuario(AbstractUser):
    es_administrador = models.BooleanField(default=False)
    es_empleado = models.BooleanField(default=False)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo_electronico = models.EmailField()
    edad = models.PositiveIntegerField()
    genero = models.CharField(max_length=10, choices=[('M', 'Masculino'), ('F', 'Femenino')])
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    numero_dni = models.CharField(max_length=20)

    def user_directory_path(instance, filename):
        # El archivo se guardará en media/fotos/ inicialmente
        return os.path.join('fotos/', filename)

    foto = models.ImageField(upload_to=user_directory_path, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Guardar el objeto primero para asegurar que la imagen se suba a media/fotos/
        super(Usuario, self).save(*args, **kwargs)
        if self.foto:
            # Ruta de destino en static/fotos/
            static_path = os.path.join(settings.STATICFILES_DIRS[0], 'fotos', os.path.basename(self.foto.name))
            # Ruta de origen en media/fotos/
            media_path = os.path.join(settings.MEDIA_ROOT, self.foto.name)
            
            # Crear el directorio si no existe
            os.makedirs(os.path.dirname(static_path), exist_ok=True)
            
            # Copiar el archivo desde media/ a static/
            try:
                shutil.copy2(media_path, static_path)
            except FileNotFoundError:
                print(f"El archivo {media_path} no se encontró y no pudo ser copiado a {static_path}.")
            
            # Mantener el archivo también en media/fotos/
            # (No se elimina el archivo en media/fotos/)
            
            # La ruta de la foto en la base de datos sigue apuntando a media/fotos/
            # Por lo tanto, no actualizamos self.foto.name en este caso.

    def __str__(self):
        return self.username

class Pedido(models.Model):
    
    nombre_pedido = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='pedido/', default='images/modelo.jpg')
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto total editable por el usuario.")
    inversion = models.DecimalField(max_digits=10, decimal_places=2, help_text="Inversión del cliente.")  # Nuevo campo de inversión
    modo_pago = models.CharField(
        max_length=50,
        choices=[
            ('contado', 'Contado'),
            ('yape', 'Yape'),
            ('transferencia', 'Transferencia'),
            ('otros', 'Otros')
        ]
    )
    fecha_entrega = models.DateField()
    detalles = models.TextField()
    productos = models.ManyToManyField('Producto', through='PedidoProducto')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    estado = models.CharField(
        max_length=50,
        choices=[
            ('pendiente', 'Pendiente'),
            ('en proceso', 'En Proceso'),
            ('completado', 'Completado'),
            ('proveedor', 'Proveedor'),
            ('entregado', 'Entregado'),
            ('cancelado', 'Cancelado'),
            # Agrega aquí otros estados si es necesario
        ],
        default='pendiente'
    )

    def calcular_total_calculado(self):
        if not self.pk:
            return 0  # Retornar 0 si el pedido no ha sido guardado aún

        # Calcular el total sumando el precio de cada producto multiplicado por su cantidad
        return sum(
            pp.producto.precio_unitario * pp.cantidad for pp in self.pedido_productos.all()
        )


    def save(self, *args, **kwargs):
        # Guardar el pedido primero
        super(Pedido, self).save(*args, **kwargs)

        # Si hay una imagen cargada (y no es la imagen por defecto), copiarla a /static/pedido/
        if self.imagen and self.imagen.name != 'images/modelo.jpg':
            source_path = os.path.join(settings.MEDIA_ROOT, str(self.imagen))
            static_path = os.path.join(settings.STATICFILES_DIRS[0], 'pedido', os.path.basename(self.imagen.name))

            # Crear el directorio en /static/pedido/ si no existe
            os.makedirs(os.path.dirname(static_path), exist_ok=True)

            # Copiar la imagen desde /media/pedido/ a /static/pedido/
            try:
                shutil.copy2(source_path, static_path)
            except FileNotFoundError:
                print(f"No se encontró el archivo {source_path}.")
            except Exception as e:
                print(f"Error al copiar la imagen: {e}")

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    inventario_cargado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Pedido {self.nombre_pedido} - {self.cliente.nombre}"


class PedidoProducto(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='pedido_productos')
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.producto.nombre} en pedido {self.pedido.nombre_pedido} (Cantidad: {self.cantidad})"


class InventarioContinuo(models.Model):

    AREA_CHOICES = [
        ('Recepción', 'Recepción'),
        ('Diseño', 'Diseño'),
        ('Sublimado', 'Sublimado'),
        ('Confección', 'Confección'),
        ('Vinilado', 'Vinilado'),
        ('Bordado', 'Bordado'),
        ('Embalaje', 'Embalaje'),
    ]

    # Usar una importación diferida para evitar el ciclo de importación
    def get_producto_model():
        from gestion_inventario.models import Producto
        return Producto

    producto = models.ForeignKey('gestion_inventario.Producto', on_delete=models.CASCADE)
    nombre_area = models.CharField(max_length=100, choices=AREA_CHOICES)
    cantidad_inicial = models.PositiveIntegerField()
    cantidad_actual = models.PositiveIntegerField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)  # Se asigna automáticamente al crear
    cantidad_minima = models.PositiveIntegerField(default=0)

    def porcentaje_restante(self):
        if self.cantidad_inicial > 0:
            return round((self.cantidad_actual / self.cantidad_inicial) * 100, 2)
        return 0

    def __str__(self):
        return self.producto.nombre
    


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nombre

    def delete(self, *args, **kwargs):
        if self.producto_set.exists():
            # Aquí no eliminamos la categoría si tiene productos asociados
            return False
        else:
            super(Categoria, self).delete(*args, **kwargs)
            return True
    
class Producto(models.Model):
    INVENTARIO_CHOICES = [
        ('continuo', 'Inventario Continuo'),
        ('bajo_demanda', 'Inventario Bajo Demanda'),
    ]

    AREA_CHOICES = [
        ('recepcion', 'Recepción'),
        ('diseno', 'Diseño'),
        ('sublimado', 'Sublimado'),
        ('confeccion', 'Confección'),
        ('vinilado', 'Vinilado'),
        ('bordado', 'Bordado'),
        ('embalaje', 'Embalaje'),
    ]

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE)
    proveedor = models.ForeignKey('Proveedor', on_delete=models.CASCADE)
    tipo_inventario = models.CharField(max_length=50, choices=INVENTARIO_CHOICES)
    area = models.CharField(max_length=50, choices=AREA_CHOICES)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    imagen = models.ImageField(upload_to='producto/', blank=True, null=True)  # Campo para la imagen

    def save(self, *args, **kwargs):
        # Guardar primero el producto
        super(Producto, self).save(*args, **kwargs)

        # Si hay una imagen cargada (y no es la imagen por defecto), copiarla a /static/producto/
        if self.imagen and self.imagen.name != 'images/producto.jpg':
            source_path = os.path.join(settings.MEDIA_ROOT, str(self.imagen))
            static_path = os.path.join(settings.STATICFILES_DIRS[0], 'producto', os.path.basename(self.imagen.name))

            # Crear el directorio en /static/producto/ si no existe
            os.makedirs(os.path.dirname(static_path), exist_ok=True)

            # Copiar la imagen desde /media/producto/ a /static/producto/
            try:
                shutil.copy2(source_path, static_path)
            except FileNotFoundError:
                print(f"No se encontró el archivo {source_path}.")
            except Exception as e:
                print(f"Error al copiar la imagen: {e}")

    def __str__(self):
        return self.nombre
    
class Actividad(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tipo_accion = models.CharField(max_length=50)
    detalle = models.TextField()
    inventario_nombre = models.CharField(max_length=255, blank=True, null=True)
    area = models.CharField(max_length=255, blank=True, null=True)
    cambio_valor = models.CharField(max_length=255, blank=True, null=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.tipo_accion} - {self.fecha_hora}"


class Area(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    funcion = models.TextField()
    jefe = models.CharField(max_length=100)
    instrumentos = models.TextField()

    def __str__(self):
        return self.nombre
    
class Proveedor(models.Model):
    TIPO_PROVEEDOR_CHOICES = [
        ('materia_prima', 'Materia Prima'),
        ('componentes', 'Componentes'),
        ('productos', 'Productos'),
        ('servicios', 'Servicios')
    ]

    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    correo_electronico = models.EmailField()
    persona_contacto = models.CharField(max_length=255)
    ruc = models.CharField(max_length=20)
    tipo_proveedor = models.CharField(max_length=50, choices=TIPO_PROVEEDOR_CHOICES)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
    
class InventarioBajoDemanda(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='inventarios')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Inventario de Pedido {self.pedido.nombre_pedido} - {self.cliente.nombre}"
    
    @property
    def total_cantidad_inicial(self):
        return self.productos_inventario.aggregate(total=Sum('cantidad_suministrada'))['total'] or 0

    @property
    def total_cantidad_actual(self):
        return self.productos_inventario.aggregate(total=Sum('cantidad_actual'))['total'] or 0

    @property
    def valor_actual_productos(self):
        total = 0
        for pi in self.productos_inventario.all():
            total += pi.producto.precio_unitario * pi.cantidad_actual
        return total

    @property
    def porcentaje_valor_actual(self):
        if self.pedido.inversion > 0:
            return (self.valor_actual_productos / self.pedido.inversion) * 100
        else:
            return 0
    
class ProductoInventario(models.Model):
    inventario = models.ForeignKey(InventarioBajoDemanda, on_delete=models.CASCADE, related_name='productos_inventario')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_suministrada = models.PositiveIntegerField()
    cantidad_actual = models.PositiveIntegerField()

    def porcentaje_restante(self):
        return (self.cantidad_actual / self.cantidad_suministrada) * 100

    def __str__(self):
        return f"{self.producto.nombre} en Inventario {self.inventario.id}"

class ProductoContinuo(models.Model):
    producto = models.ForeignKey('gestion_inventario.Producto', on_delete=models.CASCADE)
    nombre_area = models.CharField(max_length=100, choices=InventarioContinuo.AREA_CHOICES)
    cantidad_inicial = models.PositiveIntegerField()
    cantidad_actual = models.PositiveIntegerField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def porcentaje_restante(self):
        if self.cantidad_inicial > 0:
            return round((self.cantidad_actual / self.cantidad_inicial) * 100, 2)
        return 0

    def __str__(self):
        return f"{self.producto.nombre} - {self.nombre_area}"
