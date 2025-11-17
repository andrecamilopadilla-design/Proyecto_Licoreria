# core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Categoria(models.Model):
    """Categorías de productos: Licores, Cervezas, Vinos, Snacks"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """Productos del inventario"""
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    codigo_barras = models.CharField(max_length=50, blank=True, unique=True, null=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio}"
    
    @property
    def stock_bajo(self):
        """Retorna True si el stock es menor a 10"""
        return self.stock < 10


class Venta(models.Model):
    """Registro de ventas"""
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
    ]
    
    ESTADOS = [
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ventas')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='completada')
    notas = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-creado_en']
    
    def __str__(self):
        return f"Venta #{self.id} - ${self.total}"


class ItemVenta(models.Model):
    """Items individuales de cada venta"""
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    nombre_producto = models.CharField(max_length=200)  # Guardamos el nombre por si se elimina el producto
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Item de Venta'
        verbose_name_plural = 'Items de Venta'
    
    def __str__(self):
        return f"{self.cantidad}x {self.nombre_producto}"


# core/models.py - ACTUALIZAR SOLO LA CLASE PERFIL

class Perfil(models.Model):
    """Perfil extendido del usuario"""
    ROLES = [
        ('admin', 'Administrador'),
        ('cajero', 'Cajero'),
        ('cliente', 'Cliente'),  # NUEVO ROL
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')  # Default cliente
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.TextField(blank=True)  # NUEVO CAMPO
    creado_en = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"