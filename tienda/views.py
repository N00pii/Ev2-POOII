from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Producto, Categoria, ListaDeseados, Pedido, ItemPedido
from .forms import RegistroForm, LoginForm, ProductoForm


def admin_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'No tienes permisos de administrador para realizar esta acción.')
            return redirect('inicio')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Vistas públicas ────────────────────────────────────────────

def inicio(request):
    destacados = Producto.objects.filter(destacado=True)[:6]
    categorias = Categoria.objects.all()
    return render(request, 'tienda/inicio.html', {
        'destacados': destacados,
        'categorias': categorias,
    })


def catalogo(request):
    categoria_id = request.GET.get('categoria')
    busqueda = request.GET.get('q', '').strip()
    productos = Producto.objects.all()
    categorias = Categoria.objects.all()
    categoria_activa = None

    if categoria_id:
        productos = productos.filter(categoria__id=categoria_id)
        try:
            categoria_activa = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            pass

    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)

    return render(request, 'tienda/catalogo.html', {
        'productos': productos,
        'categorias': categorias,
        'categoria_activa': categoria_activa,
        'busqueda': busqueda,
    })


def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    relacionados = Producto.objects.filter(categoria=producto.categoria).exclude(pk=pk)[:4]

    # ¿Está en la lista de deseados del usuario actual?
    en_deseados = False
    if request.user.is_authenticated:
        en_deseados = ListaDeseados.objects.filter(usuario=request.user, producto=producto).exists()

    return render(request, 'tienda/detalle_producto.html', {
        'producto': producto,
        'relacionados': relacionados,
        'en_deseados': en_deseados,
    })


# ── Autenticación ─────────────────────────────────────────────

def registro(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenido, {user.first_name or user.username}. Tu cuenta fue creada.')
            return redirect('perfil')
    else:
        form = RegistroForm()
    return render(request, 'tienda/registro.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Hola de nuevo, {user.first_name or user.username}.')
            return redirect(request.GET.get('next', 'perfil'))
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm(request)
    return render(request, 'tienda/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('inicio')


# ── Área privada ──────────────────────────────────────────────

@login_required
def perfil(request):
    if request.user.is_staff:
        # Vista de administrador: estadísticas de la tienda + productos para gestión
        productos = Producto.objects.all()
        context = {
            'es_admin': True,
            'categorias': Categoria.objects.all(),
            'total_productos': Producto.objects.count(),
            'productos': productos,
        }
    else:
        # Vista de usuario normal: lista de deseados + compras/pedidos
        deseados = ListaDeseados.objects.filter(usuario=request.user).select_related('producto__categoria')
        pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related('items__producto')
        context = {
            'es_admin': False,
            'deseados': deseados,
            'pedidos': pedidos,
        }
    return render(request, 'tienda/perfil.html', context)


@login_required
def toggle_deseado(request, pk):
    """Agrega o quita un producto de la lista de deseados."""
    if request.method == 'POST':
        producto = get_object_or_404(Producto, pk=pk)
        obj, creado = ListaDeseados.objects.get_or_create(usuario=request.user, producto=producto)
        if creado:
            messages.success(request, f'"{producto.nombre}" agregado a tu lista de deseados.')
        else:
            obj.delete()
            messages.info(request, f'"{producto.nombre}" quitado de tu lista de deseados.')
        return redirect('detalle_producto', pk=pk)
    return redirect('inicio')


# ── CRUD de Productos ──────────────────────────────────────────

@admin_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('perfil')
    else:
        form = ProductoForm()
    return render(request, 'tienda/producto_form.html', {
        'form': form,
        'titulo': 'Crear Producto'
    })


@admin_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('perfil')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'tienda/producto_form.html', {
        'form': form,
        'titulo': 'Editar Producto',
        'producto': producto
    })


@admin_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado correctamente.')
        return redirect('perfil')
    return render(request, 'tienda/confirmar_eliminar.html', {
        'producto': producto
    })


# ── Carrito de Compras ────────────────────────────────────────

def ver_carrito(request):
    carrito = request.session.get('carrito', {})
    items = []
    total = 0
    for prod_id, cantidad in carrito.items():
        try:
            producto = Producto.objects.get(id=int(prod_id))
            subtotal = producto.precio * cantidad
            total += subtotal
            items.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal
            })
        except Producto.DoesNotExist:
            pass
    return render(request, 'tienda/carrito.html', {
        'items': items,
        'total': total
    })


def agregar_al_carrito(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 1))
        except ValueError:
            cantidad = 1

        if cantidad <= 0:
            messages.error(request, 'Cantidad no válida.')
            return redirect('detalle_producto', pk=pk)

        if producto.stock < cantidad:
            messages.error(request, f'No hay suficiente stock. Solo quedan {producto.stock} unidades.')
            return redirect('detalle_producto', pk=pk)

        carrito = request.session.get('carrito', {})
        prod_id_str = str(pk)
        total_solicitado = carrito.get(prod_id_str, 0) + cantidad

        if producto.stock < total_solicitado:
            messages.error(
                request,
                f'No puedes agregar más de este producto. Stock: {producto.stock}. Ya tienes {carrito.get(prod_id_str, 0)} en tu carrito.'
            )
            return redirect('detalle_producto', pk=pk)

        carrito[prod_id_str] = total_solicitado
        request.session['carrito'] = carrito
        messages.success(request, f'"{producto.nombre}" añadido al carrito.')
        return redirect('ver_carrito')
    return redirect('detalle_producto', pk=pk)


def actualizar_carrito(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        try:
            cantidad = int(request.POST.get('cantidad', 1))
        except ValueError:
            cantidad = 1

        carrito = request.session.get('carrito', {})
        prod_id_str = str(pk)

        if cantidad <= 0:
            if prod_id_str in carrito:
                del carrito[prod_id_str]
                messages.info(request, f'"{producto.nombre}" eliminado del carrito.')
        elif cantidad > producto.stock:
            messages.error(request, f'No hay suficiente stock disponible para {producto.nombre}. Stock: {producto.stock}.')
        else:
            carrito[prod_id_str] = cantidad

        request.session['carrito'] = carrito
    return redirect('ver_carrito')


def eliminar_del_carrito(request, pk):
    carrito = request.session.get('carrito', {})
    prod_id_str = str(pk)
    if prod_id_str in carrito:
        del carrito[prod_id_str]
        request.session['carrito'] = carrito
        messages.info(request, 'Producto eliminado del carrito.')
    return redirect('ver_carrito')


@login_required
def confirmar_compra(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect('catalogo')

    # Validar stock y existencia de productos
    items_a_comprar = []
    total = 0
    for prod_id, cantidad in carrito.items():
        try:
            producto = Producto.objects.get(id=int(prod_id))
            if producto.stock < cantidad:
                messages.error(
                    request,
                    f'No hay suficiente stock para "{producto.nombre}". Stock disponible: {producto.stock}. Modifica tu carrito.'
                )
                return redirect('ver_carrito')
            subtotal = producto.precio * cantidad
            total += subtotal
            items_a_comprar.append((producto, cantidad))
        except Producto.DoesNotExist:
            messages.error(request, 'Uno de los productos en tu carrito ya no está disponible.')
            return redirect('ver_carrito')

    # Procesar compra
    pedido = Pedido.objects.create(
        usuario=request.user,
        total=total,
        estado='pagado'
    )

    for producto, cantidad in items_a_comprar:
        ItemPedido.objects.create(
            pedido=pedido,
            producto=producto,
            nombre_producto=producto.nombre,
            cantidad=cantidad,
            precio_unitario=producto.precio
        )
        producto.stock -= cantidad
        producto.save()

    request.session['carrito'] = {}
    messages.success(request, '¡Compra realizada con éxito! Revisa tus pedidos aquí abajo.')
    return redirect('perfil')
