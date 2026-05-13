from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Producto, Categoria, ListaDeseados
from .forms import RegistroForm, LoginForm


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
        # Vista de administrador: estadísticas de la tienda
        context = {
            'es_admin': True,
            'categorias': Categoria.objects.all(),
            'total_productos': Producto.objects.count(),
        }
    else:
        # Vista de usuario normal: lista de deseados
        deseados = ListaDeseados.objects.filter(usuario=request.user).select_related('producto__categoria')
        context = {
            'es_admin': False,
            'deseados': deseados,
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
