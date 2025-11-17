# core/admin.py

from django.contrib import admin
from .models import Categoria, Producto, Venta, ItemVenta, Perfil

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'creado_en']
    search_fields = ['nombre']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'stock', 'activo', 'stock_bajo']
    list_filter = ['categoria', 'activo']
    search_fields = ['nombre', 'codigo_barras']
    list_editable = ['precio', 'stock', 'activo']


class ItemVentaInline(admin.TabularInline):
    model = ItemVenta
    extra = 0
    readonly_fields = ['nombre_producto', 'cantidad', 'precio_unitario', 'subtotal']


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'total', 'metodo_pago', 'estado', 'creado_en']
    list_filter = ['metodo_pago', 'estado', 'creado_en']
    search_fields = ['id', 'usuario__username']
    inlines = [ItemVentaInline]
    readonly_fields = ['total', 'creado_en']


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'rol', 'telefono', 'creado_en']
    list_filter = ['rol']
    search_fields = ['usuario__username', 'telefono']