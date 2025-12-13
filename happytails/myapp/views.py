import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from .models import Animal
from mozilla_django_oidc.views import OIDCAuthenticationRequestView
from .decorators import any_role_required, role_required, get_user_roles
import urllib.parse
import json
from django.contrib.auth import logout
from urllib.parse import urlencode
from .forms import AnimalForm
from django.contrib import messages

def home(request):
    context = {}
    if request.user.is_authenticated:
        roles = get_user_roles(request)
        oidc_claims = request.session.get('oidc_id_token_claims', {})

        context['username'] = request.user.username
        context['user_roles'] = roles
        context['role_info'] = ", ".join(roles) if roles else "No roles"
        context['user_email'] = oidc_claims.get('email', request.user.email)

    return render(request, "home.html", context)

@login_required
def animals(request):
    items = Animal.objects.all()
    user_roles = get_user_roles(request)
    return render(request, "animals.html", {"animals": items, 'user_roles': user_roles})


@login_required
@role_required('client')
def toggle_favorite(request, animal_id):
    animal = get_object_or_404(Animal, pk=animal_id)
    if animal.favorites.filter(id=request.user.id).exists():
        animal.favorites.remove(request.user)
    else:
        animal.favorites.add(request.user)
    return redirect(request.META.get('HTTP_REFERER', 'animals'))

@login_required
@role_required('client')
def favorite_list(request):
    favorite_animals = request.user.favorite_animals.all()
    
    from .decorators import get_user_roles
    user_roles = get_user_roles(request)

    return render(request, 'favorites.html', {
        'animals': favorite_animals,
        'user_roles': user_roles
    })

@login_required
@role_required('admin') 
def add_animal(request):
    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES) 
        if form.is_valid():
            form.save()
            return redirect('animals')
    else:
        form = AnimalForm()

    return render(request, 'add_animal.html', {
        'form': form,
        'user_roles': get_user_roles(request)
    })

@login_required
@role_required('admin') 
def delete_animal(request, animal_id):
    animal = get_object_or_404(Animal, pk=animal_id)
    
    if request.method == 'POST':
        nume_animal = animal.name
        animal.delete()
        return redirect('animals')
    
    return redirect('animals')

@login_required
@any_role_required('volunteer', 'admin')
def edit_animal(request, animal_id):
    user_roles = get_user_roles(request)
    if 'volunteer' not in user_roles and 'admin' not in user_roles:
        return redirect('animals')

    animal = get_object_or_404(Animal, pk=animal_id)

    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES, instance=animal)
        if form.is_valid():
            form.save()
            return redirect('animals')
    else:
        form = AnimalForm(instance=animal)

    return render(request, 'edit_animal.html', {
        'form': form,
        'animal': animal,
        'user_roles': user_roles
    })

@login_required
def animal_info(request, animal_id):
    user_roles = get_user_roles(request)
    animal = get_object_or_404(Animal, pk=animal_id)
    
    return render(request, 'animal_info.html', {
        'animal': animal,
        'user_roles': user_roles
    })


def login_view(request):
    return redirect('home')

@login_required
def profile(request):
    return render(request, "profile.html", {
        'user': request.user
    })

def register_view(request):
    request.session['oidc_login_next'] = '/'

    base_url = settings.OIDC_OP_AUTHORIZATION_ENDPOINT

    redirect_uri = request.build_absolute_uri(reverse('oidc_authentication_callback'))

    state = secrets.token_urlsafe(32)

    if 'oidc_states' not in request.session:
        request.session['oidc_states'] = {}

    request.session['oidc_states'][state] = {
        'nonce': None,  
    }

    params = {
        'client_id': settings.OIDC_RP_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': settings.OIDC_RP_SCOPES,
        'state': state,
        'response_type': 'code',
        'kc_action': 'REGISTER',  #
    }

    if getattr(settings, 'OIDC_USE_NONCE', True):
        nonce = secrets.token_urlsafe(32)
        request.session['oidc_states'][state]['nonce'] = nonce
        params['nonce'] = nonce

    request.session.modified = True

    auth_url = f"{base_url}?{urlencode(params)}"

    return redirect(auth_url)

@login_required
@role_required('admin')
def admin_dashboard(request):
    roles = get_user_roles(request)
    context = {
        'username': request.user.username,
        'user_roles': roles,
    }
    return render(request, "admin_dashboard.html", context)

@login_required
@role_required('volunteer')
def volunteer_dashboard(request):
    roles = get_user_roles(request)
    context = {
        'username': request.user.username,
        'user_roles': roles,
    }
    return render(request, "volunteer_dashboard.html", context)

@login_required
def debug_view(request):
    oidc_claims = request.session.get('oidc_id_token_claims', {})
    access_token = request.session.get('oidc_access_token', '')
    id_token = request.session.get('oidc_id_token', '')

    user_data = {
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'is_authenticated': request.user.is_authenticated,
        'roles': get_user_roles(request),
        'oidc_claims': oidc_claims,
        'has_access_token': bool(access_token),
        'has_id_token': bool(id_token),
    }

    user_data_json = json.dumps(user_data, indent=2)

    context = {
        'user_data': user_data_json,
        'user_data_dict': user_data,
    }
    return render(request, "debug.html", context)


def custom_logout(request):
    id_token = request.session.get('oidc_id_token')

    logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT
    return_to = request.build_absolute_uri('/')

    logout(request)

    params = {
        'post_logout_redirect_uri': return_to,
    }

    if id_token:
        params['id_token_hint'] = id_token

    query = urlencode(params)
    full_logout_url = f'{logout_url}?{query}'

    return redirect(full_logout_url)