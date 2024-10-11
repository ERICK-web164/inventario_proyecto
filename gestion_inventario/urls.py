from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from .views import (
    registro, CustomLoginView, listar_usuarios, UsuarioCreateView, UsuarioUpdateView, UsuarioDeleteView,
    admin_home, empleado_home, logout_view, cerrar_inventario,
    InventarioContinuoListView, InventarioContinuoCreateView, InventarioContinuoUpdateView, InventarioContinuoDeleteView, productos_continuos_api, producto_detalles,
    ver_usuario,
    # Vistas para la gestión de clientes
    ClienteListView, ClienteCreateView, ClienteUpdateView, ClienteDeleteView, ver_cliente,
    # Vistas para la gestión de pedidos
    gestor_pedidos, PedidoCreateView, PedidoUpdateView, PedidoDeleteView, ver_pedido,
    # Vistas para la gestión de productos y categorías
    ProductoListView, ProductoCreateView, CategoriaCreateView, cerrar_gestor,
    ProductoUpdateView, ProductoDeleteView, CategoriaDeleteView, CategoriaUpdateView, ver_producto,
    # Vistas para la gestión de áreas
    AreaListView, AreaUpdateView,
    # Vistas para la gestión de proveedores
    ProveedorListView, ProveedorCreateView, ProveedorUpdateView, ProveedorDeleteView, cerrar_gestor_proveedor,
    # vistas para inventario bajo demanda
    cargar_inventario, InventarioBajoDemandaListView, GestionarInventarioView, InventarioBajoDemandaDeleteView, ProductoInventarioUpdateView, ProductoInventarioDeleteView,
    #reporte de actividad
    exportar_actividad_excel

)

urlpatterns = [
    # Autenticación y registro
    path('registro/', registro, name='registro'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    
    

    # Gestión de usuarios
    path('usuarios/', listar_usuarios, name='listar_usuarios'),
    path('usuarios/ver/<int:pk>/', ver_usuario, name='ver_usuario'),
    path('usuarios/nuevo/', UsuarioCreateView.as_view(), name='crear_usuario'),
    path('usuarios/editar/<int:pk>/', UsuarioUpdateView.as_view(), name='actualizar_usuario'),
    path('usuarios/eliminar/<int:pk>/', UsuarioDeleteView.as_view(), name='eliminar_usuario'),

    # Gestión de clientes
    path('clientes/', ClienteListView.as_view(), name='cliente_list'),
    path('clientes/nuevo/', ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/editar/<int:pk>/', ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/eliminar/<int:pk>/', ClienteDeleteView.as_view(), name='cliente_delete'),
    path('clientes/ver/<int:pk>/', ver_cliente, name='ver_cliente'),

    # Gestión de pedidos
    path('clientes/<int:cliente_id>/pedidos/', gestor_pedidos, name='gestor_pedidos'),
    path('clientes/<int:cliente_id>/pedidos/nuevo/', PedidoCreateView.as_view(), name='nuevo_pedido'),
    path('pedidos/<int:pk>/ver/', ver_pedido, name='ver_pedido'),
    path('pedidos/<int:pk>/modificar/', PedidoUpdateView.as_view(), name='modificar_pedido'),
    path('pedidos/<int:pk>/eliminar/', PedidoDeleteView.as_view(), name='eliminar_pedido'),

    # Gestión de inventario continuo
    path('inventario_continuo/', InventarioContinuoListView.as_view(), name='inventario_continuo_list'),
    path('inventario_continuo/nuevo/', InventarioContinuoCreateView.as_view(), name='inventario_continuo_create'),
    path('inventario_continuo/editar/<int:pk>/', InventarioContinuoUpdateView.as_view(), name='inventario_continuo_update'),
    path('inventario_continuo/eliminar/<int:pk>/', InventarioContinuoDeleteView.as_view(), name='inventario_continuo_delete'),
    path('api/productos/continuos/', productos_continuos_api, name='productos_continuos_api'),
    path('api/productos/detalles/<int:producto_id>/', producto_detalles, name='producto_detalles'),

    # Gestión de productos y categorías
    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('productos/nuevo/', ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/editar/', ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/<int:pk>/eliminar/', ProductoDeleteView.as_view(), name='producto_delete'),
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='categoria_create'),
    path('categoria/<int:pk>/editar/', CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', CategoriaDeleteView.as_view(), name='categoria_delete'),
    path('cerrar_gestor/', cerrar_gestor, name='cerrar_gestor'),
    path('producto/<int:pk>/', ver_producto, name='ver_producto'),

    # Gestión de áreas
    path('areas/', AreaListView.as_view(), name='listar_areas'),
    path('areas/<int:pk>/editar/', AreaUpdateView.as_view(), name='area_update'),

    # Gestión de proveedores
    path('gestor_proveedores/', ProveedorListView.as_view(), name='gestor_proveedor'),
    path('gestor_proveedores/nuevo/', ProveedorCreateView.as_view(), name='registrar_proveedor'),
    path('gestor_proveedores/cerrar/', cerrar_gestor_proveedor, name='cerrar_gestor_proveedor'),
    path('gestor_proveedores/editar/<int:pk>/', ProveedorUpdateView.as_view(), name='editar_proveedor'),
    path('proveedores/<int:pk>/eliminar/', ProveedorDeleteView.as_view(), name='proveedor_delete'),

    # gestion de inventario bajo demanda
    path('cargar_inventario/<int:pedido_id>/', cargar_inventario, name='cargar_inventario'),
    path('inventario_bajo_demanda/', InventarioBajoDemandaListView.as_view(), name='inventario_bajo_demanda_list'),
    path('gestionar_inventario/<int:pk>/', GestionarInventarioView.as_view(), name='gestionar_inventario'),
    path('inventario_bajo_demanda/eliminar/<int:inventario_id>/', InventarioBajoDemandaDeleteView.as_view(), name='inventario_bajo_demanda_eliminar'),
    path('producto_inventario/<int:pk>/editar/', ProductoInventarioUpdateView.as_view(), name='editar_producto_inventario'),
    path('producto_inventario/<int:pk>/eliminar/', ProductoInventarioDeleteView.as_view(), name='eliminar_producto_inventario'),

    # generar reporte en excel
    path('exportar-actividad/', exportar_actividad_excel, name='exportar_actividad_excel'),

    # Otras vistas
    path('cerrar_inventario/', cerrar_inventario, name='cerrar_inventario'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('empleado_home/', empleado_home, name='empleado_home'),
    path('informacion_general_pedidos/', views.informacion_general_pedidos, name='informacion_general_pedidos'),
    path('informacion_general_pedidos/pdf/', views.generar_pdf_informacion_general_pedidos, name='informacion_general_pedidos_pdf'),
    
    # Favicon
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
]

# Servir archivos estáticos y de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
