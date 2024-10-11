from django.contrib import admin
from .models import Usuario, InventarioContinuo, Actividad, Area

# Registrar otros modelos
admin.site.register(Usuario)
admin.site.register(InventarioContinuo)
admin.site.register(Actividad)

# Registrar el modelo Area con opciones de admin personalizadas
@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'funcion', 'jefe', 'instrumentos')  # Asegúrate de que 'jefe' sea un campo de Area
    ordering = ('nombre',)
    list_editable = ('descripcion', 'funcion', 'jefe', 'instrumentos')  # Hacer todos estos campos editables directamente en la lista
    
    def has_add_permission(self, request):
        return False  # Deshabilita la opción de añadir nuevas áreas

    def has_delete_permission(self, request, obj=None):
        return False  # Deshabilita la opción de eliminar áreas
