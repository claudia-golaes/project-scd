from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from django.conf import settings
from urllib.parse import urlencode
from .models import Animal
from .serializers import AnimalSerializer, AnimalCreateUpdateSerializer, UserSerializer
from .decorators import get_user_roles
import secrets


class AnimalViewSet(viewsets.ModelViewSet):
    """    
    list: Get all animals (all roles)
    retrieve: Get specific animal details (all roles)
    create: Add new animal (admin only)
    update: Update animal (admin, volunteer)
    partial_update: Partial update animal (admin, volunteer)
    destroy: Delete animal (admin only)
    """
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        roles = get_user_roles(self.request)
        
        if self.action == 'retrieve':
            return Animal.objects.all()
        
        if 'admin' in roles:
            show_adopted = self.request.query_params.get('show_adopted', 'false')
            if show_adopted.lower() == 'true':
                return Animal.objects.all()
            return Animal.objects.exclude(status='AD')
        
        return Animal.objects.filter(status__in=['AV', 'PD'])
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AnimalCreateUpdateSerializer
        return AnimalSerializer
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count()
        })
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        roles = get_user_roles(request)
        if 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators can add animals',
                'required_role': 'admin',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Animal added successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        roles = get_user_roles(request)
        if 'admin' not in roles and 'volunteer' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators and volunteers can edit animals',
                'required_roles': ['admin', 'volunteer'],
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Animal updated successfully',
                'data': serializer.data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        if 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators can delete animals',
                'required_role': 'admin',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance = self.get_object()
        animal_name = instance.name
        instance.delete()
        
        return Response({
            'success': True,
            'message': f'Animal "{animal_name}" deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'], url_path='toggle-favorite')
    def toggle_favorite(self, request, pk=None):
        roles = get_user_roles(request)
        if 'client' not in roles:
            return Response({
                'success': False,
                'error': 'Only clients can manage favorites',
                'required_role': 'client',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        animal = self.get_object()
        
        if animal.favorites.filter(id=request.user.id).exists():
            animal.favorites.remove(request.user)
            is_favorite = False
            message = f'{animal.name} removed from favorites'
        else:
            animal.favorites.add(request.user)
            is_favorite = True
            message = f'{animal.name} added to favorites'
        
        return Response({
            'success': True,
            'message': message,
            'is_favorite': is_favorite
        })
    
    @action(detail=False, methods=['get'], url_path='favorites')
    def favorites(self, request):
        roles = get_user_roles(request)
        if 'client' not in roles:
            return Response({
                'success': False,
                'error': 'Only clients can view favorites',
                'required_role': 'client',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        favorite_animals = request.user.favorite_animals.all()
        serializer = self.get_serializer(favorite_animals, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': favorite_animals.count()
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def home(request):
    context = {
        'success': True,
        'message': 'HappyTails API',
        'version': '1.0',
        'authenticated': request.user.is_authenticated
    }
    
    if request.user.is_authenticated:
        roles = get_user_roles(request)
        oidc_claims = request.session.get('oidc_id_token_claims', {})
        
        context['user'] = {
            'username': request.user.username,
            'email': oidc_claims.get('email', request.user.email),
            'roles': roles
        }
    
    return Response(context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    serializer = UserSerializer(request.user, context={'request': request})
    
    oidc_claims = request.session.get('oidc_id_token_claims', {})
    
    return Response({
        'success': True,
        'data': {
            **serializer.data,
            'oidc_claims': oidc_claims
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
    
    return Response({
        'success': True,
        'data': user_data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
    
    return Response({
        'success': True,
        'message': 'Logged out successfully',
        'keycloak_logout_url': full_logout_url
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def register_view(request):
    request.session['oidc_login_next'] = '/'
    
    base_url = settings.OIDC_OP_AUTHORIZATION_ENDPOINT
    
    from django.urls import reverse
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
        'kc_action': 'REGISTER',
    }
    
    if getattr(settings, 'OIDC_USE_NONCE', True):
        nonce = secrets.token_urlsafe(32)
        request.session['oidc_states'][state]['nonce'] = nonce
        params['nonce'] = nonce
    
    request.session.modified = True
    
    auth_url = f"{base_url}?{urlencode(params)}"
    
    return Response({
        'success': True,
        'message': 'Redirect to Keycloak registration',
        'registration_url': auth_url
    })
