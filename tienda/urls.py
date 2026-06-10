from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('deseado/<int:pk>/', views.toggle_deseado, name='toggle_deseado'),
    
    # Gestión de productos (admin)
    path('producto/crear/', views.crear_producto, name='crear_producto'),
    path('producto/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('producto/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    
    # Carrito de compras
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:pk>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/actualizar/<int:pk>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<int:pk>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/comprar/', views.confirmar_compra, name='confirmar_compra'),
]
