from functools import wraps
from django.shortcuts import redirect

def login_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('user_login')  # Redirige vers ta page de login personnalisée
        # Tu peux ajouter d'autres vérifications ici si besoin
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required_custom(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_type = request.session.get('user_type')
        admin_id = request.session.get('admin_id')

        if user_type not in ('admin', 'super_admin') or admin_id is None:
            return redirect('user_login')

        return view_func(request, *args, **kwargs)

    return wrapper
