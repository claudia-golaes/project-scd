from functools import wraps
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def get_user_roles(request):
    roles = request.session.get('user_roles', None)
    if roles is not None:
        return roles

    oidc_claims = request.session.get('oidc_id_token_claims', {})
    all_roles = set()

    direct_roles = oidc_claims.get('roles', [])
    if isinstance(direct_roles, list):
        all_roles.update(direct_roles)

    realm_access = oidc_claims.get('realm_access', {})
    realm_roles = realm_access.get('roles', [])
    all_roles.update(realm_roles)

    resource_access = oidc_claims.get('resource_access', {})
    for client_id, client_data in resource_access.items():
        client_roles = client_data.get('roles', [])
        all_roles.update(client_roles)

    return list(all_roles)


def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            roles = get_user_roles(request)

            if required_role in roles:
                return view_func(request, *args, **kwargs)

            return render(request, 'access_denied.html', {
                'required_role': required_role,
                'user_roles': roles
            })

        return wrapped_view
    return decorator


def any_role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            roles = get_user_roles(request)
            if 'admin' in roles:
                return view_func(request, *args, **kwargs)

            if any(role in roles for role in allowed_roles):
                return view_func(request, *args, **kwargs)

            return render(request, 'access_denied.html', {
                'required_roles': allowed_roles,
                'user_roles': roles
            })

        return wrapped_view
    return decorator
