# core/views.py - REEMPLAZAR TODO EL ARCHIVO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Categoria, Producto, Venta, ItemVenta, Perfil


# ============ AUTENTICACIÓN ============

def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        # Redirigir según rol
        if hasattr(request.user, 'perfil'):
            if request.user.perfil.rol == 'cliente':
                return redirect('tienda')
            else:
                return redirect('dashboard')
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.first_name or user.username}!')
            
            # Redirigir según rol
            if hasattr(user, 'perfil'):
                if user.perfil.rol == 'cliente':
                    return redirect('tienda')
                else:
                    return redirect('dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'core/login.html')


def register_view(request):
    """Vista de registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        rol = request.POST.get('rol', 'cliente')
        
        # Validaciones
        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'core/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El usuario ya existe')
            return render(request, 'core/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado')
            return render(request, 'core/register.html')
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Crear perfil
        Perfil.objects.create(usuario=user, rol=rol)
        
        messages.success(request, 'Cuenta creada exitosamente. Puedes iniciar sesión.')
        return redirect('login')
    
    return render(request, 'core/register.html')


def logout_view(request):
    """Cerrar sesión"""
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente')
    return redirect('login')


# ============ TIENDA PARA CLIENTES ============

@login_required
def tienda_view(request):
    """Tienda para clientes - Ver y comprar productos"""
    productos = Producto.objects.filter(activo=True, stock__gt=0).select_related('categoria')
    
    # Búsqueda
    q = request.GET.get('q')
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | 
            Q(descripcion__icontains=q)
        )
    
    # Filtro por categoría
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    categorias = Categoria.objects.all()
    
    # Carrito de compras (guardado en sesión)
    carrito = request.session.get('carrito', {})
    total_carrito = sum(float(item['subtotal']) for item in carrito.values())
    cantidad_items = sum(item['cantidad'] for item in carrito.values())
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'q': q,
        'categoria_id': categoria_id,
        'carrito': carrito,
        'total_carrito': total_carrito,
        'cantidad_items': cantidad_items,
    }
    
    return render(request, 'core/tienda.html', context)


@login_required
def agregar_al_carrito(request, producto_id):
    """Agregar producto al carrito"""
    producto = get_object_or_404(Producto, id=producto_id, activo=True)
    
    if producto.stock <= 0:
        messages.error(request, 'Producto sin stock disponible')
        return redirect('tienda')
    
    # Obtener carrito de la sesión
    carrito = request.session.get('carrito', {})
    producto_key = str(producto_id)
    
    if producto_key in carrito:
        # Incrementar cantidad si ya existe
        if carrito[producto_key]['cantidad'] < producto.stock:
            carrito[producto_key]['cantidad'] += 1
            carrito[producto_key]['subtotal'] = str(
                float(carrito[producto_key]['precio']) * carrito[producto_key]['cantidad']
            )
            messages.success(request, f'Cantidad actualizada: {producto.nombre}')
        else:
            messages.warning(request, 'No hay más stock disponible')
    else:
        # Agregar nuevo producto
        carrito[producto_key] = {
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': str(producto.precio),
            'cantidad': 1,
            'subtotal': str(producto.precio),
            'stock': producto.stock,
        }
        messages.success(request, f'Producto agregado: {producto.nombre}')
    
    request.session['carrito'] = carrito
    return redirect('tienda')


@login_required
def actualizar_carrito(request, producto_id):
    """Actualizar cantidad en carrito"""
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        carrito = request.session.get('carrito', {})
        producto_key = str(producto_id)
        
        if producto_key in carrito:
            producto = get_object_or_404(Producto, id=producto_id)
            
            if cantidad <= 0:
                del carrito[producto_key]
                messages.info(request, 'Producto eliminado del carrito')
            elif cantidad <= producto.stock:
                carrito[producto_key]['cantidad'] = cantidad
                carrito[producto_key]['subtotal'] = str(
                    float(carrito[producto_key]['precio']) * cantidad
                )
                messages.success(request, 'Carrito actualizado')
            else:
                messages.error(request, 'No hay suficiente stock')
        
        request.session['carrito'] = carrito
    
    return redirect('tienda')


@login_required
def eliminar_del_carrito(request, producto_id):
    """Eliminar producto del carrito"""
    carrito = request.session.get('carrito', {})
    producto_key = str(producto_id)
    
    if producto_key in carrito:
        del carrito[producto_key]
        request.session['carrito'] = carrito
        messages.success(request, 'Producto eliminado del carrito')
    
    return redirect('tienda')


@login_required
def finalizar_compra(request):
    """Finalizar compra del cliente"""
    if request.method == 'POST':
        carrito = request.session.get('carrito', {})
        
        if not carrito:
            messages.error(request, 'El carrito está vacío')
            return redirect('tienda')
        
        metodo_pago = request.POST.get('metodo_pago')
        
        # Calcular total
        total = Decimal('0.00')
        items_data = []
        
        for producto_key, item in carrito.items():
            producto = Producto.objects.get(id=item['id'])
            cantidad = item['cantidad']
            
            if producto.stock < cantidad:
                messages.error(request, f'Stock insuficiente para {producto.nombre}')
                return redirect('tienda')
            
            subtotal = Decimal(str(item['subtotal']))
            total += subtotal
            
            items_data.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal,
            })
        
        # Crear venta
        venta = Venta.objects.create(
            usuario=request.user,
            total=total,
            metodo_pago=metodo_pago
        )
        
        # Crear items y actualizar stock
        for item_data in items_data:
            ItemVenta.objects.create(
                venta=venta,
                producto=item_data['producto'],
                nombre_producto=item_data['producto'].nombre,
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['producto'].precio,
                subtotal=item_data['subtotal']
            )
            
            # Actualizar stock
            producto = item_data['producto']
            producto.stock -= item_data['cantidad']
            producto.save()
        
        # Limpiar carrito
        request.session['carrito'] = {}
        
        messages.success(request, f'¡Compra realizada exitosamente! Pedido #{venta.id}')
        return redirect('mis_pedidos')
    
    return redirect('tienda')


@login_required
def mis_pedidos_view(request):
    """Ver pedidos del cliente"""
    pedidos = Venta.objects.filter(
        usuario=request.user
    ).prefetch_related('items').order_by('-creado_en')
    
    context = {'pedidos': pedidos}
    return render(request, 'core/mis_pedidos.html', context)


# ============ DASHBOARD ADMINISTRATIVO ============

@login_required
def dashboard_view(request):
    """Dashboard principal con estadísticas (solo admin/cajero)"""
    
    # Verificar que sea admin o cajero
    if hasattr(request.user, 'perfil') and request.user.perfil.rol == 'cliente':
        return redirect('tienda')
    
    # Estadísticas generales
    total_productos = Producto.objects.filter(activo=True).count()
    productos_stock_bajo = Producto.objects.filter(activo=True, stock__lt=10).count()
    
    # Ventas de hoy
    hoy = timezone.now().date()
    ventas_hoy = Venta.objects.filter(
        creado_en__date=hoy,
        estado='completada'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Ventas del mes
    inicio_mes = timezone.now().replace(day=1)
    ventas_mes = Venta.objects.filter(
        creado_en__gte=inicio_mes,
        estado='completada'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Productos más vendidos (últimos 30 días)
    hace_30_dias = timezone.now() - timedelta(days=30)
    productos_top = ItemVenta.objects.filter(
        venta__creado_en__gte=hace_30_dias,
        venta__estado='completada'
    ).values('producto__nombre').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:5]
    
    # Últimas ventas
    ultimas_ventas = Venta.objects.filter(estado='completada').order_by('-creado_en')[:10]
    
    context = {
        'total_productos': total_productos,
        'productos_stock_bajo': productos_stock_bajo,
        'ventas_hoy': ventas_hoy,
        'ventas_mes': ventas_mes,
        'productos_top': productos_top,
        'ultimas_ventas': ultimas_ventas,
    }
    
    return render(request, 'core/dashboard.html', context)


# ============ PRODUCTOS ============

@login_required
def productos_lista_view(request):
    """Lista de productos con búsqueda y filtros"""
    productos = Producto.objects.filter(activo=True).select_related('categoria')
    
    # Búsqueda
    q = request.GET.get('q')
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | 
            Q(codigo_barras__icontains=q) |
            Q(descripcion__icontains=q)
        )
    
    # Filtro por categoría
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    categorias = Categoria.objects.all()
    
    context = {
        'productos': productos,
        'categorias': categorias,
        'q': q,
        'categoria_id': categoria_id,
    }
    
    return render(request, 'core/productos_lista.html', context)


@login_required
def producto_crear_view(request):
    """Crear nuevo producto (solo admins)"""
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol not in ['admin', 'cajero']:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('productos_lista')
    
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        categoria_id = request.POST.get('categoria')
        descripcion = request.POST.get('descripcion', '')
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')
        codigo_barras = request.POST.get('codigo_barras', '')
        
        Producto.objects.create(
            nombre=nombre,
            categoria_id=categoria_id,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            codigo_barras=codigo_barras if codigo_barras else None
        )
        
        messages.success(request, 'Producto creado exitosamente')
        return redirect('productos_lista')
    
    categorias = Categoria.objects.all()
    return render(request, 'core/producto_form.html', {'categorias': categorias})


@login_required
def producto_editar_view(request, pk):
    """Editar producto existente (solo admins)"""
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol not in ['admin', 'cajero']:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('productos_lista')
    
    producto = get_object_or_404(Producto, pk=pk)
    
    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre')
        producto.categoria_id = request.POST.get('categoria')
        producto.descripcion = request.POST.get('descripcion', '')
        producto.precio = request.POST.get('precio')
        producto.stock = request.POST.get('stock')
        producto.codigo_barras = request.POST.get('codigo_barras', '') or None
        producto.save()
        
        messages.success(request, 'Producto actualizado exitosamente')
        return redirect('productos_lista')
    
    categorias = Categoria.objects.all()
    context = {
        'producto': producto,
        'categorias': categorias,
        'editar': True,
    }
    return render(request, 'core/producto_form.html', context)


@login_required
def producto_eliminar_view(request, pk):
    """Eliminar producto (solo admins)"""
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol not in ['admin', 'cajero']:
        messages.error(request, 'No tienes permisos para realizar esta acción')
        return redirect('productos_lista')
    
    producto = get_object_or_404(Producto, pk=pk)
    producto.activo = False
    producto.save()
    
    messages.success(request, 'Producto eliminado exitosamente')
    return redirect('productos_lista')


# ============ VENTAS ============

@login_required
def ventas_lista_view(request):
    """Lista de ventas"""
    if hasattr(request.user, 'perfil') and request.user.perfil.rol == 'admin':
        ventas = Venta.objects.all()
    else:
        ventas = Venta.objects.filter(usuario=request.user)
    
    ventas = ventas.select_related('usuario').prefetch_related('items').order_by('-creado_en')
    
    context = {'ventas': ventas}
    return render(request, 'core/ventas_lista.html', context)


@login_required
def venta_crear_view(request):
    """Crear nueva venta (cajeros/admin)"""
    if hasattr(request.user, 'perfil') and request.user.perfil.rol == 'cliente':
        return redirect('tienda')
    
    if request.method == 'POST':
        metodo_pago = request.POST.get('metodo_pago')
        productos_ids = request.POST.getlist('producto_id')
        cantidades = request.POST.getlist('cantidad')
        
        if not productos_ids:
            messages.error(request, 'Debes agregar al menos un producto')
            return redirect('venta_crear')
        
        # Calcular total
        total = Decimal('0.00')
        items_data = []
        
        for i, producto_id in enumerate(productos_ids):
            producto = Producto.objects.get(id=producto_id)
            cantidad = int(cantidades[i])
            
            if producto.stock < cantidad:
                messages.error(request, f'Stock insuficiente para {producto.nombre}')
                return redirect('venta_crear')
            
            subtotal = producto.precio * cantidad
            total += subtotal
            
            items_data.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal,
            })
        
        # Crear venta
        venta = Venta.objects.create(
            usuario=request.user,
            total=total,
            metodo_pago=metodo_pago
        )
        
        # Crear items y actualizar stock
        for item_data in items_data:
            ItemVenta.objects.create(
                venta=venta,
                producto=item_data['producto'],
                nombre_producto=item_data['producto'].nombre,
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['producto'].precio,
                subtotal=item_data['subtotal']
            )
            
            # Actualizar stock
            producto = item_data['producto']
            producto.stock -= item_data['cantidad']
            producto.save()
        
        messages.success(request, f'Venta #{venta.id} creada exitosamente')
        return redirect('venta_detalle', pk=venta.id)
    
    productos = Producto.objects.filter(activo=True, stock__gt=0).select_related('categoria')
    categorias = Categoria.objects.all()
    
    context = {
        'productos': productos,
        'categorias': categorias,
    }
    return render(request, 'core/venta_form.html', context)


@login_required
def venta_detalle_view(request, pk):
    """Ver detalle de una venta"""
    venta = get_object_or_404(Venta, pk=pk)
    
    # Verificar permisos
    if hasattr(request.user, 'perfil') and request.user.perfil.rol not in ['admin', 'cajero']:
        if venta.usuario != request.user:
            messages.error(request, 'No tienes permisos para ver esta venta')
            return redirect('mis_pedidos')
    
    context = {'venta': venta}
    return render(request, 'core/venta_detalle.html', context)


# ============ REPORTES ============

@login_required
def reportes_view(request):
    """Reportes administrativos (solo admins)"""
    if not hasattr(request.user, 'perfil') or request.user.perfil.rol != 'admin':
        messages.error(request, 'No tienes permisos para acceder a reportes')
        return redirect('dashboard')
    
    # Rango de fechas
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)
    inicio_mes = timezone.now().replace(day=1).date()
    
    # Ventas por período
    ventas_hoy = Venta.objects.filter(
        creado_en__date=hoy,
        estado='completada'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    ventas_7_dias = Venta.objects.filter(
        creado_en__date__gte=hace_7_dias,
        estado='completada'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    ventas_mes = Venta.objects.filter(
        creado_en__date__gte=inicio_mes,
        estado='completada'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Productos más vendidos del mes
    productos_top = ItemVenta.objects.filter(
        venta__creado_en__date__gte=inicio_mes,
        venta__estado='completada'
    ).values('producto__nombre').annotate(
        total_vendido=Sum('cantidad'),
        ingresos=Sum('subtotal')
    ).order_by('-total_vendido')[:10]
    
    # Ventas por método de pago (mes actual)
    ventas_por_metodo = Venta.objects.filter(
        creado_en__date__gte=inicio_mes,
        estado='completada'
    ).values('metodo_pago').annotate(
        total=Sum('total'),
        cantidad=Count('id')
    ).order_by('-total')
    
    # Ventas diarias (últimos 30 días)
    ventas_diarias = Venta.objects.filter(
        creado_en__date__gte=hace_30_dias,
        estado='completada'
    ).extra(
        select={'fecha': 'date(creado_en)'}
    ).values('fecha').annotate(
        total=Sum('total'),
        cantidad=Count('id')
    ).order_by('-fecha')
    
    context = {
        'ventas_hoy': ventas_hoy,
        'ventas_7_dias': ventas_7_dias,
        'ventas_mes': ventas_mes,
        'productos_top': productos_top,
        'ventas_por_metodo': ventas_por_metodo,
        'ventas_diarias': ventas_diarias,
    }
    
    return render(request, 'core/reportes.html', context)
    
    return render(request, 'core/reportes.html', context)