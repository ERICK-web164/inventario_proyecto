#forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from gestion_inventario.models import Usuario, InventarioContinuo
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.forms import ModelForm
from django.db.models import Sum
from .models import Cliente
from .models import Pedido, Producto, PedidoProducto, Proveedor, InventarioBajoDemanda, ProductoInventario, ProductoContinuo
from .models import Area
from django.forms import DateField, DateInput


from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from .models import Usuario

class RegistroForm(UserCreationForm):
    nombre = forms.CharField(max_length=100, label=_('Nombre'))
    apellido = forms.CharField(max_length=100, label=_('Apellido'))
    correo_electronico = forms.EmailField(label=_('Correo Electrónico'))
    edad = forms.IntegerField(label=_('Edad'))
    genero = forms.ChoiceField(choices=[('M', 'Masculino'), ('F', 'Femenino')], label=_('Género'))
    direccion = forms.CharField(max_length=255, label=_('Dirección'))
    ciudad = forms.CharField(max_length=100, label=_('Ciudad'))
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}), 
        input_formats=['%Y-%m-%d'],  # Formato para asegurar la correcta entrada de fechas
        label=_('Fecha de Nacimiento')
    )
    numero_dni = forms.CharField(max_length=20, label=_('Número de DNI'))
    foto = forms.ImageField(required=False, label=_('Foto'))
    es_administrador = forms.BooleanField(required=False, label=_('Es Administrador'))
    es_empleado = forms.BooleanField(required=False, label=_('Es Empleado'))

    class Meta:
        model = Usuario
        fields = [
            'username', 'nombre', 'apellido', 'correo_electronico', 'edad', 
            'genero', 'direccion', 'ciudad', 'fecha_nacimiento', 'numero_dni', 
            'foto', 'es_administrador', 'es_empleado'
        ]

    def __init__(self, *args, **kwargs):
        super(RegistroForm, self).__init__(*args, **kwargs)
        # Asegurarse de que el campo fecha_nacimiento esté correctamente preestablecido
        if self.instance and self.instance.pk and self.instance.fecha_nacimiento:
            self.fields['fecha_nacimiento'].initial = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Verificar si el nombre de usuario ya existe, excluyendo la instancia actual
        if Usuario.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Ya existe un usuario con este nombre."))
        return username

    def clean_foto(self):
        foto = self.cleaned_data.get('foto')

        if foto:
            # Validar el tamaño de la imagen (máximo 2 MB)
            if foto.size > 2 * 1024 * 1024:
                raise ValidationError(_("La imagen no debe exceder los 2 MB."))
            
            # Obtener dimensiones de la imagen
            width, height = get_image_dimensions(foto)
            if width < 100 or height < 100:
                raise ValidationError(_("La imagen es muy pequeña (mínimo 100x100 píxeles)."))
            if width > 2000 or height > 2000:
                raise ValidationError(_("La imagen es muy grande (máximo 2000x2000 píxeles)."))
            
            # Validar el tipo MIME de la imagen solo si se ha subido una nueva
            foto_file = self.files.get('foto')
            if foto_file:
                content_type = foto_file.content_type
                if content_type not in ['image/jpeg', 'image/png', 'image/gif']:
                    raise ValidationError(_("Formato de imagen no soportado (solo JPEG, PNG y GIF)."))
            else:
                # Si no hay un archivo nuevo, no es necesario validar el content_type
                pass

        return foto



class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'contacto', 'direccion', 'telefono', 'email', 'rubro', 'ruc_dni']

class LoginForm(AuthenticationForm):
    username = forms.CharField(max_length=254, label=_('Nombre de Usuario'))
    password = forms.CharField(widget=forms.PasswordInput, label=_('Contraseña'))

    class Meta:
        model = Usuario
        fields = ['username', 'password']


class PedidoForm(forms.ModelForm):
    fecha_entrega = forms.DateField(
        widget=DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )

    productos = forms.ModelMultipleChoiceField(
        queryset=Producto.objects.filter(tipo_inventario='bajo_demanda'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'producto-checkbox'}),
        required=False,
        label='Productos (Inventario Bajo Demanda)'
    )
    
    total_calculado = forms.DecimalField(
        label="Suma Total Calculada",
        required=False,
        widget=forms.NumberInput(attrs={'readonly': 'readonly'})
    )
    
    class Meta:
        model = Pedido
        fields = [
            'nombre_pedido', 'descripcion', 'imagen', 'monto_total', 'inversion',
            'modo_pago', 'fecha_entrega', 'detalles', 'productos', 'estado'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'inversion': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
        }

    def __init__(self, *args, **kwargs):
        super(PedidoForm, self).__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            print(f"Fecha de entrega desde la instancia: {self.instance.fecha_entrega}")
            self.fields['total_calculado'].initial = self.instance.calcular_total_calculado()
        else:
            self.fields['total_calculado'].initial = 0

        print(f"Valor inicial del campo fecha_entrega: {self.fields['fecha_entrega'].initial}")
        # En modo de creación, ocultar el estado y asignar el valor por defecto
        if not self.instance.pk:
            self.fields['estado'].widget = forms.HiddenInput()
            self.fields['estado'].initial = 'pendiente'
            self.fields['estado'].required = False
        else:
            # Si estamos en modo de edición, mostrar el estado y hacerlo requerido
            self.fields['estado'].required = True

    def clean(self):
        cleaned_data = super().clean()
        productos = cleaned_data.get('productos')

        if productos:
            total_calculado = 0
            for producto in productos:
                cantidad_str = self.data.get(f'cantidad_{producto.pk}', '1')
                try:
                    cantidad = int(cantidad_str)
                except ValueError:
                    cantidad = 1

                total_calculado += producto.precio_unitario * cantidad
            
            # Actualizar el total_calculado con el valor calculado
            cleaned_data['total_calculado'] = total_calculado

        return cleaned_data

class InventarioContinuoForm(forms.ModelForm):
    class Meta:
        model = ProductoContinuo
        fields = ['producto', 'cantidad_inicial']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_inicial': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            
        }

    def clean(self):
        cleaned_data = super().clean()
        cantidad_inicial = cleaned_data.get('cantidad_inicial')
        if cantidad_inicial is None or cantidad_inicial < 1:
            self.add_error('cantidad_inicial', 'La cantidad suministrada debe ser mayor que 0.')
        return cleaned_data



class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['nombre', 'descripcion', 'funcion', 'jefe', 'instrumentos']

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'direccion', 'telefono', 'correo_electronico', 'persona_contacto', 'ruc', 'tipo_proveedor']

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio_unitario', 'categoria', 'proveedor', 'tipo_inventario', 'area', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'tipo_inventario': forms.Select(attrs={'class': 'form-select'}),
            'area': forms.Select(attrs={'class': 'form-select'}),
        }

