from django.db import models
from django.contrib.auth.models import User


class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    imagen = models.CharField(max_length=100, default='cat_videojuegos.png')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.CharField(max_length=200, default='prod_zelda.png')
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
