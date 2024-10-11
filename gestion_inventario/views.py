#views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Usuario
from .forms import RegistroForm, LoginForm, InventarioContinuoForm, PedidoForm
from gestion_inventario.models import InventarioContinuo, Actividad
from django.contrib.auth.views import LoginView
from collections import defaultdict
import openpyxl
from openpyxl.drawing.image import Image as OpenPyxlImage
import matplotlib
matplotlib.use('Agg')  # Configurar el backend antes de importar pyplot
import matplotlib.pyplot as plt
from io import BytesIO
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.db import models
import os
import shutil
from django.conf import settings
from django.db import models
from .models import Cliente
from .forms import ClienteForm, ProveedorForm, ProductoForm
from .models import Pedido
from .models import Producto, Categoria, PedidoProducto, Proveedor, InventarioBajoDemanda, ProductoInventario, ProductoContinuo
from django.core.exceptions import ValidationError
from .models import Area
from django.db.models import Sum
from django.forms.models import modelformset_factory
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from datetime import date
from django import template
from openpyxl import Workbook
from django.db.models import Sum, F, Q
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from django.contrib.staticfiles import finders
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.db import transaction
from django.contrib.messages.views import SuccessMessageMixin

# Función para determinar la imagen de perfil según el género del usuario
def obtener_imagen_perfil(usuario):
    if usuario.genero == 'F':
        return 'mujer.jpg'
    elif usuario.genero == 'M':
        return 'varon.jpg'
    return 'default.jpg'  # Imagen por defecto si el género no está especificado

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])  # Utiliza 'password1' en lugar de 'password'
            user.save()
            login(request, user)
            messages.success(request, 'Usuario registrado exitosamente.')
            if user.es_administrador:
                return redirect('admin_home')
            else:
                return redirect('empleado_home')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'login.html'

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form, error="Credenciales incorrectas"))

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if user.es_administrador:
                return reverse('admin_home')
            else:
                return reverse('empleado_home')
        return reverse('login')

@login_required
def cerrar_inventario(request):
    user = request.user
    # Verificar si el usuario es administrador
    if user.es_administrador:
        return redirect('admin_home')
    # Verificar si el usuario es empleado
    elif user.es_empleado:
        return redirect('empleado_home')

@login_required
@user_passes_test(lambda u: u.es_administrador)
def listar_usuarios(request):
    administradores = Usuario.objects.filter(es_administrador=True)
    empleados = Usuario.objects.filter(es_empleado=True)
    return render(request, 'listar_usuarios.html', {
        'administradores': administradores,
        'empleados': empleados
    })

@login_required
def ver_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    imagen_perfil = obtener_imagen_perfil(usuario)  # Obtener la imagen de perfil según el género
    return render(request, 'ver_usuario.html', {'usuario': usuario, 'imagen_perfil': imagen_perfil})

class UsuarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Usuario
    form_class = RegistroForm
    template_name = 'editar_usuario.html'  
    success_url = reverse_lazy('listar_usuarios')  # Redirigir a la lista de usuarios después de guardar

    def form_valid(self, form):
        # Guardar el formulario
        response = super().form_valid(form)
        # Agregar mensaje de éxito
        messages.success(self.request, 'Usuario actualizado exitosamente.')
        # Redirigir a ver_usuario con el pk del usuario que fue editado
        return redirect(reverse('ver_usuario', kwargs={'pk': self.object.pk}))


    def get_success_url(self):
        # Redirigir a la página de ver usuario
        return reverse('ver_usuario', kwargs={'pk': self.object.pk})

class UsuarioCreateView(LoginRequiredMixin, CreateView):
    model = Usuario
    form_class = RegistroForm
    template_name = 'crear_usuario.html'
    success_url = reverse_lazy('listar_usuarios')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Usuario creado exitosamente.')
        return response

class UsuarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Usuario
    template_name = 'eliminar_usuario.html'
    success_url = reverse_lazy('listar_usuarios')

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Registrar la actividad antes de la eliminación
        Actividad.objects.create(
            usuario=request.user,
            tipo_accion='eliminar',
            detalle=f'Eliminó {instance.username} del sistema.',  # Asumiendo que 'username' es el nombre del usuario
            fecha_hora=timezone.now()
        )
        
        # Agregar mensaje de éxito
        messages.success(self.request, 'Usuario eliminado exitosamente.')
        
        response = super().delete(request, *args, **kwargs)
        return response


class ClienteListView(ListView):
    model = Cliente
    template_name = 'cliente_list.html'
    context_object_name = 'clientes'

class ClienteCreateView(CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'cliente_form.html'
    success_url = reverse_lazy('cliente_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Mensaje de éxito al crear cliente
        messages.success(self.request, 'Cliente creado exitosamente.')
        return response

class ClienteUpdateView(UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'cliente_form.html'
    success_url = reverse_lazy('cliente_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Mensaje de éxito al actualizar cliente
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return response


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'cliente_confirm_delete.html'
    success_url = reverse_lazy('cliente_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Eliminar cliente
        self.object.delete()
        # Mensaje de éxito al eliminar cliente
        messages.success(request, 'Cliente eliminado exitosamente.')
        return redirect(self.success_url)


def ver_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    return render(request, 'ver_cliente.html', {'cliente': cliente})

@login_required
def admin_home(request):
    mensajes_alerta = []

    # Verificar inventario continuo
    productos_continuos_bajo_stock = InventarioContinuo.objects.filter(cantidad_actual__lt=models.F('cantidad_inicial') * 0.1)
    if productos_continuos_bajo_stock.exists():
        mensajes_alerta.append(('El inventario continuo tiene productos en bajo stock.', 'rojo'))

    # Renderizar la plantilla con el contexto adecuado
    return render(request, 'admin_home.html', {
        'nombre_usuario': request.user.username,
        'rol': 'ADMINISTRADOR',
        'mensajes_alerta': mensajes_alerta
         })

@login_required
def empleado_home(request):
    return render(request, 'empleado_home.html', {'nombre_usuario': request.user.username, 'rol': 'EMPLEADO'})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

class ProductoListView(ListView):
    model = Producto
    template_name = 'producto_list.html'
    context_object_name = 'productos'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categorias_con_productos = Categoria.objects.filter(producto__isnull=False).distinct()
        productos_por_categoria = {categoria.nombre: Producto.objects.filter(categoria=categoria) for categoria in categorias_con_productos}
        context['productos_por_categoria'] = productos_por_categoria
        return context

class ProductoCreateView(LoginRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'
    success_url = reverse_lazy('producto_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Mensaje de éxito
        messages.success(self.request, 'Producto registrado exitosamente.')
        return response

class ProductoUpdateView(LoginRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'
    success_url = reverse_lazy('producto_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Mensaje de éxito
        messages.success(self.request, 'Producto actualizado exitosamente.')
        return response



class ProductoDeleteView(LoginRequiredMixin, DeleteView):
    model = Producto
    template_name = 'producto_confirm_delete.html'  # La plantilla que confirmará la eliminación
    success_url = reverse_lazy('producto_list')  # Redirigir después de la eliminación exitosa

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Eliminar el producto
        self.object.delete()
        # Mostrar un mensaje de éxito
        messages.success(request, 'Producto eliminado exitosamente.')
        return redirect(self.success_url)


def cerrar_gestor(request):
    return redirect('admin_home')

class CategoriaCreateView(CreateView):
    model = Categoria
    fields = ['nombre', 'descripcion']
    template_name = 'categoria_form.html'
    success_url = reverse_lazy('categoria_create')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Mensaje de éxito
        messages.success(self.request, 'Categoría creada exitosamente.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasar todas las categorías al contexto
        context['categorias'] = Categoria.objects.all()
        return context
    
class CategoriaUpdateView(UpdateView):
    model = Categoria
    fields = ['nombre', 'descripcion']
    template_name = 'categoria_form.html'
    success_url = reverse_lazy('categoria_create')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Mensaje de éxito
        messages.success(self.request, 'Categoría actualizada exitosamente.')
        return response
    
class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'categoria_confirm_delete.html'
    success_url = reverse_lazy('categoria_create')

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            # Intentar eliminar la categoría
            self.object.delete()
            # Si se elimina correctamente, mostrar mensaje de éxito
            messages.success(request, "Categoría eliminada exitosamente.")
        except IntegrityError:
            # Si ocurre un error de integridad (por ejemplo, restricción de clave foránea)
            messages.error(request, "No se puede eliminar esta categoría porque está relacionada con otros registros.")
        except Categoria.DoesNotExist:
            # Si la categoría no existe
            messages.error(request, "La categoría que intentas eliminar no existe.")
        except Exception as e:
            # Para cualquier otro error
            messages.error(request, "Ocurrió un error al intentar eliminar la categoría. Por favor, inténtalo de nuevo.")
            # Opcional: registrar el error para depuración
            # print(e)
        return redirect(self.success_url)
# Vistas para Inventario Continuo

class InventarioContinuoListView(LoginRequiredMixin, ListView):
    model = ProductoContinuo  # Usamos ProductoContinuo
    template_name = 'inventario_continuo_list.html'
    context_object_name = 'inventarios'

    def get(self, request, *args, **kwargs):
        # Registrar actividad de listar inventario
        Actividad.objects.create(
            usuario=request.user,
            tipo_accion='listar',
            detalle='Ingresó a la vista de lista del inventario continuo.',
            fecha_hora=timezone.now()
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items_by_area = defaultdict(list)
        porcentajes_por_area = {}

        # Agrupar los productos por área
        for item in self.object_list:
            # Calcular el porcentaje restante para cada producto
            if item.cantidad_inicial > 0:
                item.porcentaje_restante = round((item.cantidad_actual / item.cantidad_inicial) * 100, 2)
            else:
                item.porcentaje_restante = 0  # Evitar división por cero

            items_by_area[item.nombre_area].append(item)

        # Calcular el porcentaje de productos restantes para cada área
        for area, items in items_by_area.items():
            total_inicial = sum(item.cantidad_inicial for item in items)
            total_actual = sum(item.cantidad_actual for item in items)

            if total_inicial > 0:
                porcentaje_area = round((total_actual / total_inicial) * 100, 2)
            else:
                porcentaje_area = 0  # Si no hay cantidades iniciales, el porcentaje es 0

            porcentajes_por_area[area] = porcentaje_area

        # Pasar los datos al contexto
        context['items_by_area'] = dict(items_by_area)
        context['porcentajes_por_area'] = porcentajes_por_area

        return context

class InventarioContinuoCreateView(LoginRequiredMixin, CreateView):
    model = ProductoContinuo  # Usamos el modelo ProductoContinuo
    form_class = InventarioContinuoForm
    template_name = 'inventario_continuo_form.html'
    success_url = reverse_lazy('inventario_continuo_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener los productos con inventario continuo
        context['productos_continuos'] = Producto.objects.filter(tipo_inventario='continuo')
        return context

    def form_valid(self, form):
        print(form.cleaned_data)  # Depuración
        instance = form.save(commit=False)
        producto = form.cleaned_data.get('producto')

        # Asignar el área automáticamente desde el producto
        instance.nombre_area = producto.area  # Suponiendo que el área está relacionada con el producto
        instance.cantidad_actual = form.cleaned_data.get('cantidad_inicial')  # Inicializar cantidad actual
        instance.save()

        # Registrar actividad de usuario al añadir un producto
        Actividad.objects.create(
            usuario=self.request.user,
            tipo_accion='añadir',
            detalle=f'Añadió el producto {producto.nombre} al inventario continuo en el área {instance.nombre_area}.',
            fecha_hora=timezone.now()
        )

        messages.success(self.request, 'Producto añadido correctamente al inventario continuo.')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Imprimir los errores del formulario para depuración
        print("Errores del formulario:", form.errors)

        # Mensaje de error si el formulario no es válido
        messages.error(self.request, 'Error al añadir el producto. Revisa los datos e inténtalo de nuevo.')
        return super().form_invalid(form)

class InventarioContinuoUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductoContinuo  # Asegúrate de estar utilizando el modelo correcto
    fields = ['cantidad_actual']  # Solo permitimos editar la cantidad actual
    template_name = 'actualizar_producto.html'
    success_url = reverse_lazy('inventario_continuo_list')

    def form_valid(self, form):
        instance = form.save(commit=False)

        # Aquí ya tienes la instancia, puedes usar instance.cantidad_actual directamente
        old_value = instance.cantidad_actual  # Cantidad actual antes de la actualización
        new_value = form.cleaned_data['cantidad_actual']  # Nueva cantidad actual del formulario

        # Actualizar la cantidad en la instancia
        instance.cantidad_actual = new_value
        instance.save()

        # Registrar la actividad del usuario al actualizar el producto
        Actividad.objects.create(
            usuario=self.request.user,
            tipo_accion='actualizar',
            detalle=f'Actualizó la cantidad actual de {instance.producto.nombre} en el inventario continuo.',
            area=instance.nombre_area,
            cambio_valor=f'de {old_value} a {new_value}',
            fecha_hora=timezone.now()
        )

        messages.success(self.request, 'Cantidad actualizada correctamente.')
        return super().form_valid(form)


class InventarioContinuoDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductoContinuo
    template_name = 'inventario_confirm_delete.html'
    success_url = reverse_lazy('inventario_continuo_list')

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            # Acceso correcto a nombre_area y producto.nombre
            area = instance.nombre_area  
            Actividad.objects.create(
                usuario=request.user,
                tipo_accion='eliminar',
                detalle=f'Eliminó {instance.producto.nombre} del inventario continuo.',
                area=area,
                fecha_hora=timezone.now()
            )
        except Exception as e:
            # Manejar errores y mostrar un mensaje de error
            messages.error(request, f"Error eliminando el producto: {str(e)}")
            return HttpResponseRedirect(self.success_url)

        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Producto eliminado correctamente.')
        return response

def producto_detalles(request, producto_id):
    try:
        producto = get_object_or_404(Producto, id=producto_id)

        # Ruta correcta para servir la imagen desde /static/producto/
        imagen_url = f'/static/producto/{os.path.basename(producto.imagen.name)}' if producto.imagen else '/static/images/producto.jpg'

        data = {
            'descripcion': producto.descripcion,
            'precio_unitario': str(producto.precio_unitario),
            'categoria': producto.categoria.nombre,
            'proveedor': producto.proveedor.nombre,
            'area': producto.area,
            'imagen_url': imagen_url,  # Usamos la ruta estática corregida
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    

def productos_continuos_api(request):
    productos = Producto.objects.filter(tipo_inventario='continuo').select_related('categoria', 'proveedor').values(
        'id', 'nombre', 'descripcion', 'precio_unitario', 'categoria__nombre', 'proveedor__nombre', 'area', 'imagen'
    )
    return JsonResponse(list(productos), safe=False)


@login_required
def gestor_pedidos(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    pedidos = Pedido.objects.filter(cliente=cliente)
    return render(request, 'gestor_pedidos.html', {'cliente': cliente, 'pedidos': pedidos})

class PedidoCreateView(LoginRequiredMixin, CreateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'pedido_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = get_object_or_404(Cliente, pk=self.kwargs['cliente_id'])
        context['cliente_id'] = cliente.id
        context['cliente_nombre'] = cliente.nombre
        return context

    def form_valid(self, form):
        cliente = get_object_or_404(Cliente, pk=self.kwargs['cliente_id'])
        form.instance.cliente = cliente
        
        # Manejo de la imagen por defecto si no se proporciona ninguna
        if 'imagen' not in self.request.FILES:
            form.instance.imagen = 'pedido/images/modelo.jpg'

        self.object = form.save()

        # Eliminar las relaciones anteriores de productos
        PedidoProducto.objects.filter(pedido=self.object).delete()

        # Guardar las nuevas relaciones de productos con las cantidades
        productos = form.cleaned_data.get('productos')
        for producto in productos:
            cantidad = int(self.request.POST.get(f'cantidad_{producto.id}', 1))
            PedidoProducto.objects.create(pedido=self.object, producto=producto, cantidad=cantidad)

        messages.success(self.request, 'Pedido creado exitosamente.')

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('gestor_pedidos', kwargs={'cliente_id': self.kwargs['cliente_id']})

class PedidoUpdateView(LoginRequiredMixin, UpdateView):
    model = Pedido
    form_class = PedidoForm
    template_name = 'pedido_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pedido = self.object  # Pedido actual

        # Añadir información del cliente
        context['cliente_id'] = pedido.cliente.id
        context['cliente_nombre'] = pedido.cliente.nombre

        # Obtener los productos y las cantidades asociadas al pedido
        productos_cantidades = PedidoProducto.objects.filter(pedido=pedido).select_related('producto')
        context['productos_cantidades'] = [
            {'producto': pp.producto, 'cantidad': pp.cantidad} for pp in productos_cantidades
        ]

        return context

    def form_valid(self, form):
        # Guardar el pedido primero
        self.object = form.save()

        # Eliminar relaciones de productos anteriores para evitar duplicados
        PedidoProducto.objects.filter(pedido=self.object).delete()

        # Guardar nuevas relaciones de productos con sus cantidades
        productos = form.cleaned_data.get('productos', [])
        if productos:
            # Usar bulk_create para mejorar el rendimiento al crear múltiples objetos
            pedido_productos = [
                PedidoProducto(
                    pedido=self.object, 
                    producto=producto, 
                    cantidad=int(self.request.POST.get(f'cantidad_{producto.id}', 1))
                )
                for producto in productos
            ]
            PedidoProducto.objects.bulk_create(pedido_productos)

        messages.success(self.request, 'Pedido actualizado exitosamente.')

        return redirect(self.get_success_url())

    def get_success_url(self):
        # Redirigir a la lista de pedidos del cliente
        return reverse('gestor_pedidos', kwargs={'cliente_id': self.object.cliente.id})



class PedidoDeleteView(LoginRequiredMixin, DeleteView):
    model = Pedido
    template_name = 'pedido_confirm_delete.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        # Mensaje de éxito al eliminar el pedido
        messages.success(request, 'Pedido eliminado exitosamente.')

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('gestor_pedidos', kwargs={'cliente_id': self.object.cliente.id})

@login_required
def ver_pedido(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    
    # Obtener los productos y las cantidades usando la relación a través del modelo intermedio PedidoProducto
    productos_cantidades = PedidoProducto.objects.filter(pedido=pedido).select_related('producto')

    # Calcular el monto total de cada producto multiplicando su precio por la cantidad
    productos_con_subtotal = []
    for item in productos_cantidades:
        subtotal = item.producto.precio_unitario * item.cantidad
        productos_con_subtotal.append({
            'producto': item.producto,
            'cantidad': item.cantidad,
            'subtotal': subtotal
        })

    monto_total_productos = pedido.productos.aggregate(Sum('precio_unitario'))['precio_unitario__sum'] or 0
    return render(request, 'ver_pedido.html', {
        'pedido': pedido,
        'monto_total_productos': monto_total_productos,
        'productos_con_subtotal': productos_con_subtotal
    })



class AreaListView(ListView):
    model = Area
    template_name = 'gestion_inventario/area_list.html'
    context_object_name = 'areas'

class AreaUpdateView(UpdateView):
    model = Area
    fields = ['nombre', 'descripcion', 'funcion', 'jefe', 'instrumentos']
    template_name = 'gestion_inventario/area_form.html'
    success_url = reverse_lazy('listar_areas')  # Usa el nombre de la URL en lugar de la ruta estática

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['volver_url'] = reverse_lazy('listar_areas')  # Añadir contexto para el botón "Volver"
        return context
    
def listar_areas(request):
    areas = Area.objects.all()
    return render(request, 'area_list.html', {'areas': areas})

class ProveedorListView(ListView):
    model = Proveedor
    template_name = 'gestor_proveedor.html'
    context_object_name = 'proveedores'

@login_required
def cerrar_gestor_proveedor(request):
    return redirect('admin_home')

class ProveedorCreateView(CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'registrar_proveedor.html'
    success_url = reverse_lazy('gestor_proveedor')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Mensaje de éxito
        messages.success(self.request, 'Proveedor registrado exitosamente.')
        return response
    
class ProveedorUpdateView(UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'registrar_proveedor.html'  # Reutiliza la misma plantilla de creación
    success_url = reverse_lazy('gestor_proveedor')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Mensaje de éxito
        messages.success(self.request, 'Proveedor actualizado exitosamente.')
        return response

class ProveedorDeleteView(LoginRequiredMixin, DeleteView):
    model = Proveedor
    template_name = 'proveedor_confirm_delete.html'  # La plantilla dedicada a la confirmación de eliminación
    success_url = reverse_lazy('gestor_proveedor')  # Redirigir después de la eliminación exitosa

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(request, "Categoria eliminado exitosamente.")
        except IntegrityError:
            messages.error(request, "No se puede eliminar esta categoría porque está relacionada con otros registros.")
        return redirect(self.success_url)

@csrf_exempt
def cargar_inventario(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id)
        
        # Obtener o crear el inventario sin el campo 'estado'
        inventario, created = InventarioBajoDemanda.objects.get_or_create(
            pedido=pedido,
            defaults={
                'cliente': pedido.cliente,
                # 'estado' eliminado porque ya no existe en InventarioBajoDemanda
            }
        )

        if created:
            # Crear los productos asociados al inventario
            productos = PedidoProducto.objects.filter(pedido=pedido)
            for producto in productos:
                ProductoInventario.objects.create(
                    inventario=inventario,
                    producto=producto.producto,
                    cantidad_suministrada=producto.cantidad,
                    cantidad_actual=producto.cantidad
                )
            
            # Actualizar el estado del pedido
            pedido.inventario_cargado = True
            pedido.estado = 'en proceso'  # Usar el valor correcto del estado
            pedido.save()

            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "already_loaded"})


class GestionarInventarioView(LoginRequiredMixin, DetailView):
    model = InventarioBajoDemanda
    template_name = 'gestionar_inventario.html'
    context_object_name = 'inventario'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        productos_inventario = ProductoInventario.objects.filter(inventario=self.object)

        # Agrupar productos por área
        productos_por_area = defaultdict(list)
        for producto in productos_inventario:
            productos_por_area[producto.producto.get_area_display()].append(producto)

        context['productos_por_area'] = dict(productos_por_area)
        return context

class InventarioBajoDemandaListView(ListView):
    model = InventarioBajoDemanda
    template_name = 'inventario_bajo_demanda_list.html'
    context_object_name = 'inventarios'

    def get(self, request, *args, **kwargs):
        # Registrar actividad de listar inventarios bajo demanda
        Actividad.objects.create(
            usuario=request.user,
            tipo_accion='listar',
            detalle='Ingresó a la vista de lista del inventario bajo demanda.',
            fecha_hora=timezone.now()
        )
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener todos los inventarios con relaciones prefetch/related
        inventarios = InventarioBajoDemanda.objects.select_related('pedido', 'cliente').prefetch_related('productos_inventario__producto')

        # Agrupar los inventarios por cliente usando defaultdict
        inventarios_por_cliente = defaultdict(list)
        today = date.today()  # Fecha actual

        for inventario in inventarios:
            # Calcular total suministrado y actual
            total_suministrado = inventario.productos_inventario.aggregate(total=Sum('cantidad_suministrada'))['total'] or 0
            total_actual = inventario.productos_inventario.aggregate(total=Sum('cantidad_actual'))['total'] or 0

            # Calcular el porcentaje completado
            if total_suministrado > 0:
                porcentaje_completado = ((total_suministrado - total_actual) / total_suministrado) * 100
            else:
                porcentaje_completado = 0

            inventario.porcentaje_completado = round(porcentaje_completado, 2)  # Redondear a 2 decimales

            # Calcular los días restantes
            fecha_entrega = inventario.pedido.fecha_entrega
            dias_restantes = (fecha_entrega - today).days
            inventario.dias_restantes = dias_restantes  # Añadir días restantes al inventario

            # Agrupar inventarios por cliente
            inventarios_por_cliente[inventario.cliente.nombre].append(inventario)

        # Agregar el diccionario agrupado al contexto
        context['inventarios_por_cliente'] = dict(inventarios_por_cliente)
        return context
    

class InventarioBajoDemandaDeleteView(LoginRequiredMixin, DeleteView):
    model = InventarioBajoDemanda
    pk_url_kwarg = 'inventario_id'
    template_name = 'inventariobajodemanda_confirm_delete.html'
    success_url = reverse_lazy('inventario_bajo_demanda_list')

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        pedido = instance.pedido

        # Actualizar el estado del pedido
        pedido.inventario_cargado = False
        pedido.estado = 'pendiente'
        pedido.save()

        # Eliminar el inventario
        instance.delete()

        # Mensaje de éxito
        messages.success(request, 'El inventario ha sido eliminado exitosamente.')

        # Redirigir manualmente para asegurarnos que los mensajes se guarden y se muestren
        return redirect(self.success_url)



class ProductoInventarioUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductoInventario
    template_name = 'editar_producto_inventario.html'
    fields = ['cantidad_actual']  # Solo la cantidad actual es editable

    def get_context_data(self, **kwargs):
        # Obtiene el contexto estándar de la vista y agrega información adicional
        context = super().get_context_data(**kwargs)
        context['producto_inventario'] = self.object  # Asegura que el objeto producto_inventario esté disponible en el template
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        old_value = ProductoInventario.objects.get(pk=instance.pk).cantidad_actual
        new_value = form.cleaned_data['cantidad_actual']
        instance.save()

        area = instance.producto.area # Asumiendo que producto.area es una instancia de Area
        inventario_nombre = instance.inventario.pedido.nombre_pedido   # Asegúrate de que InventarioBajoDemanda tiene un campo 'nombre'

        # Registrar actividad de actualización
        Actividad.objects.create(
            usuario=self.request.user,
            tipo_accion='actualizar',
            detalle=f'Actualizó la cantidad actual de {instance.producto.nombre} en el inventario bajo demanda.',
            area=area,
            inventario_nombre=inventario_nombre,
            cambio_valor=f'de {old_value} a {new_value}',
            fecha_hora=timezone.now()
        )

        # Mensaje de éxito
        messages.success(self.request, 'Cantidad actualizada correctamente.')

        # Redirigir a la vista de gestionar inventario
        return redirect('gestionar_inventario', pk=instance.inventario.id)

    def get_success_url(self):
        # Redirige a la página anterior (gestionar inventario), o a '/' si no hay HTTP_REFERER
        return self.request.META.get('HTTP_REFERER', '/')


class ProductoInventarioDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductoInventario
    template_name = 'producto_inventario_confirm_delete.html'  # Plantilla de confirmación de eliminación
    success_url = reverse_lazy('inventario_bajo_demanda_list')

    def post(self, request, *args, **kwargs):
        producto_inventario = self.get_object()
        
        # Acceder al área del producto (CharField)
        area = producto_inventario.producto.area
        
        # Acceder al nombre del pedido relacionado al inventario
        inventario_nombre = producto_inventario.inventario.pedido.nombre_pedido  # Corrección aquí
        
        # Registrar la actividad de eliminación
        Actividad.objects.create(
            usuario=request.user,
            tipo_accion='eliminar',
            detalle=f'Eliminó {producto_inventario.producto.nombre} del inventario bajo demanda.',
            area=area,
            inventario_nombre=inventario_nombre,
            fecha_hora=timezone.now()
        )

        # Mensaje de éxito
        messages.success(request, 'El producto ha sido eliminado exitosamente.')
        
        # Proceder con la eliminación
        return super().delete(request, *args, **kwargs)

@login_required
def ver_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'ver_producto.html', {'producto': producto})

@login_required
def exportar_actividad_excel(request):
    wb = Workbook()
    ws_continuo = wb.active
    ws_continuo.title = "Inventario Continuo"

    # Crear una nueva hoja para Inventario Bajo Demanda
    ws_demanda = wb.create_sheet(title="Inventario Bajo Demanda")

    # Encabezados para Inventario Continuo
    headers_continuo = ['Nombre de usuario', 'Acción realizada', 'Área', 'Cambio de valor', 'Hora de la acción']
    ws_continuo.append(headers_continuo)

    # Encabezados para Inventario Bajo Demanda
    headers_demanda = ['Nombre de usuario', 'Acción realizada', 'Nombre del inventario', 'Área', 'Cambio de valor', 'Hora de la acción']
    ws_demanda.append(headers_demanda)

    # Obtener las actividades
    actividades = Actividad.objects.all()

    for actividad in actividades:
        usuario_nombre = actividad.usuario.username
        accion_realizada = actividad.tipo_accion
        inventario_nombre = actividad.inventario_nombre if actividad.inventario_nombre else ''
        area = actividad.area if actividad.area else ''
        cambio_valor = actividad.cambio_valor if actividad.cambio_valor else ''
        fecha_hora = actividad.fecha_hora.strftime('%Y-%m-%d %H:%M:%S')

        if actividad.inventario_nombre:
            # Actividad del Inventario Bajo Demanda
            ws_demanda.append([usuario_nombre, accion_realizada, inventario_nombre, area, cambio_valor, fecha_hora])
        else:
            # Actividad del Inventario Continuo
            ws_continuo.append([usuario_nombre, accion_realizada, area, cambio_valor, fecha_hora])

    # Preparar la respuesta
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="actividad_usuarios.xlsx"'

    wb.save(response)
    return response



@login_required
def informacion_general_pedidos(request):
    # Obtener todos los inventarios bajo demanda
    inventarios = InventarioBajoDemanda.objects.select_related('pedido', 'cliente').prefetch_related('productos_inventario__producto')

    # Agrupar inventarios por cliente
    inventarios_por_cliente = defaultdict(list)
    today = date.today()

    # Variables para el cálculo del porcentaje general de "Abastecimiento de Pedidos"
    total_pedidos = 0
    pedidos_a_tiempo = 0

    for inventario in inventarios:
        # Calcular días restantes
        fecha_entrega = inventario.pedido.fecha_entrega
        dias_restantes = (fecha_entrega - today).days
        inventario.dias_restantes = dias_restantes

        # Determinar si el pedido está atrasado
        inventario.atrasado = dias_restantes < 0

        # Obtener estado del pedido
        inventario.pedido.estado_pedido = inventario.pedido.estado

        # Calcular porcentaje de completado del pedido
        total_suministrado = inventario.total_cantidad_inicial  # Usando el método del modelo
        total_actual = inventario.total_cantidad_actual  # Usando el método del modelo

        if total_suministrado > 0:
            porcentaje_completado = ((total_suministrado - total_actual) / total_suministrado) * 100
            porcentaje_productos_restantes = (total_actual / total_suministrado) * 100
        else:
            porcentaje_completado = 0
            porcentaje_productos_restantes = 0

        inventario.porcentaje_completado = round(porcentaje_completado, 2)
        inventario.porcentaje_productos_restantes = round(porcentaje_productos_restantes, 2)

        # Calcular valor actual de los productos
        #inventario.valor_actual_productos = inventario.valor_actual_productos#  # Usando el método del modelo

        # Calcular porcentaje de valor actual en relación a la inversión
        #inventario.porcentaje_valor_actual = inventario.porcentaje_valor_actual#  # Usando el método del modelo

        # Sumar para "Abastecimiento de Pedidos"
        total_pedidos += 1
        if not inventario.atrasado:
            pedidos_a_tiempo += 1

        # Añadir inventario al grupo de su cliente
        inventarios_por_cliente[inventario.cliente].append(inventario)

    # Calcular porcentaje general de "Abastecimiento de Pedidos"
    if total_pedidos > 0:
        porcentaje_abastecimiento = (pedidos_a_tiempo / total_pedidos) * 100
    else:
        porcentaje_abastecimiento = 0

    context = {
        'inventarios_por_cliente': dict(inventarios_por_cliente),
        'porcentaje_abastecimiento': round(porcentaje_abastecimiento, 2),
        'today': today,
    }

    return render(request, 'informacion_general_pedidos.html', context)

@login_required
def generar_pdf_informacion_general_pedidos(request):
    # Obtener todos los inventarios bajo demanda
    inventarios = InventarioBajoDemanda.objects.select_related('pedido', 'cliente').prefetch_related('productos_inventario__producto')

    # Agrupar inventarios por cliente
    inventarios_por_cliente = defaultdict(list)
    today = date.today()

    # Variables para el cálculo del porcentaje general de "Abastecimiento de Pedidos"
    total_pedidos = 0
    pedidos_a_tiempo = 0

    for inventario in inventarios:
        # Calcular días restantes
        fecha_entrega = inventario.pedido.fecha_entrega
        dias_restantes = (fecha_entrega - today).days
        inventario.dias_restantes = dias_restantes

        # Determinar si el pedido está atrasado
        inventario.atrasado = dias_restantes < 0

        # Obtener estado del pedido
        inventario.pedido.estado = inventario.pedido.estado

        # Calcular porcentaje de completado del pedido
        total_suministrado = inventario.productos_inventario.aggregate(total=Sum('cantidad_suministrada'))['total'] or 0
        total_actual = inventario.productos_inventario.aggregate(total=Sum('cantidad_actual'))['total'] or 0
        productos = inventario.productos_inventario.all()

        if total_suministrado > 0:
            porcentaje_completado = ((total_suministrado - total_actual) / total_suministrado) * 100
        else:
            porcentaje_completado = 0

        inventario.porcentaje_completado = round(porcentaje_completado, 2)

        # Calcular porcentajes por producto
        for producto_inventario in productos:
            if producto_inventario.cantidad_suministrada > 0:
                producto_inventario.porcentaje_restante = round(
                    (producto_inventario.cantidad_actual / producto_inventario.cantidad_suministrada) * 100, 2)
            else:
                producto_inventario.porcentaje_restante = 0

        # Sumar para "Abastecimiento de Pedidos"
        total_pedidos += 1
        if not inventario.atrasado:
            pedidos_a_tiempo += 1

        # Añadir inventario al grupo de su cliente
        inventarios_por_cliente[inventario.cliente].append(inventario)

    # Calcular porcentaje general de "Abastecimiento de Pedidos"
    if total_pedidos > 0:
        porcentaje_abastecimiento = (pedidos_a_tiempo / total_pedidos) * 100
    else:
        porcentaje_abastecimiento = 0

    context = {
        'inventarios_por_cliente': dict(inventarios_por_cliente),
        'porcentaje_abastecimiento': round(porcentaje_abastecimiento, 2),
        'today': today,
    }

    # Renderizar la plantilla a una cadena HTML
    html_string = render_to_string('informacion_general_pedidos.html', context, request=request)

    # Encontrar la ruta base para archivos estáticos
    base_url = request.build_absolute_uri('/')

    # Generar el PDF usando WeasyPrint
    html = HTML(string=html_string, base_url=base_url)
    result = html.write_pdf()

    # Registrar la actividad de generación de PDF
    Actividad.objects.create(
        usuario=request.user,
        tipo_accion='exportar',
        detalle='Exportó la información general de pedidos a PDF.',
        fecha_hora=timezone.now()
    )

    # Devolver el PDF como respuesta
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="informacion_general_pedidos.pdf"'
    response.write(result)
    return response

