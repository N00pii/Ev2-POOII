def carrito(request):
    total_items = 0
    carrito_session = request.session.get('carrito', {})
    for qty in carrito_session.values():
        try:
            total_items += int(qty)
        except ValueError:
            pass
    return {'carrito_cantidad': total_items}
