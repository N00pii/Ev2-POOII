from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre

    @property
    def imagen_url(self):
        if self.imagen:
            try:
                return self.imagen.url
            except ValueError:
                return f'/static/img/{self.imagen.name}'
        return '/static/img/cat_videojuegos.png'

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, related_name='productos'
    )
    destacado = models.BooleanField(default=False)
    stock = models.IntegerField(default=0)
    fecha_agregado = models.DateField(auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-fecha_agregado']

    def __str__(self):
        return self.nombre

    def disponible(self):
        return self.stock > 0

    @property
    def imagen_url(self):
        if self.imagen:
            try:
                return self.imagen.url
            except ValueError:
                return f'/static/img/{self.imagen.name}'
        return '/static/img/prod_zelda.png'

class ListaDeseados(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deseados')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='deseado_por')
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Lista de deseados'
        verbose_name_plural = 'Listas de deseados'
        unique_together = ['usuario', 'producto']

    def __str__(self):
        return f'{self.usuario.username} — {self.producto.nombre}'

class Pedido(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pedidos')
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pagado')

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha']

    def __str__(self):
        return f'Pedido #{self.id} — {self.usuario.username}'

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    nombre_producto = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.cantidad} x {self.nombre_producto}'

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario
