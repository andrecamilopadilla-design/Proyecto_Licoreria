# core/urls.py - REEMPLAZAR TODO

from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Tienda para Clientes
    path('tienda/', views.tienda_view, name='tienda'),
    path('tienda/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('tienda/actualizar/<int:producto_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('tienda/eliminar/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('tienda/finalizar/', views.finalizar_compra, name='finalizar_compra'),
    path('mis-pedidos/', views.mis_pedidos_view, name='mis_pedidos'),
    
    # Dashboard Administrativo
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Productos
    path('productos/', views.productos_lista_view, name='productos_lista'),
    path('productos/crear/', views.producto_crear_view, name='producto_crear'),
    path('productos/<int:pk>/editar/', views.producto_editar_view, name='producto_editar'),
    path('productos/<int:pk>/eliminar/', views.producto_eliminar_view, name='producto_eliminar'),
    
    # Ventas
    path('ventas/', views.ventas_lista_view, name='ventas_lista'),
    path('ventas/crear/', views.venta_crear_view, name='venta_crear'),
    path('ventas/<int:pk>/', views.venta_detalle_view, name='venta_detalle'),
    
    # Reportes
    path('reportes/', views.reportes_view, name='reportes'),
]