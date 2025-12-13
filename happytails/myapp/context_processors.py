from .decorators import get_user_roles

def user_roles_processor(request):
    if request.user.is_authenticated:
        return {
            'user_roles': get_user_roles(request)
        }
    return {
        'user_roles': []
    }
