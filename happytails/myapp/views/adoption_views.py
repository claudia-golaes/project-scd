from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from myapp.models import Adoption, Animal
from myapp.serializers import (
    AdoptionListSerializer, AdoptionDetailSerializer,
    AdoptionCreateSerializer, AdoptionScheduleVisitSerializer,
    AdoptionReviewSerializer
)
from myapp.decorators import get_user_roles


class AdoptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        roles = get_user_roles(self.request)
        
        if 'admin' in roles:
            return Adoption.objects.all().select_related('user', 'animal', 'reviewed_by')
        
        return Adoption.objects.filter(user=user).select_related('animal')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AdoptionCreateSerializer
        elif self.action in ['list']:
            return AdoptionListSerializer
        return AdoptionDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """GET /adoptions/ - applications (personal or all the applications for an admin)"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        roles = get_user_roles(request)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count(),
            'viewing_as': 'admin' if 'admin' in roles else 'client'
        })
    
    def retrieve(self, request, *args, **kwargs):
        """GET /adoptions/{id}/ - adoption details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """POST /adoptions/ - create new adoption (client)"""
        roles = get_user_roles(request)
        
        if 'client' not in roles:
            return Response({
                'success': False,
                'error': 'Doar clienții pot aplica pentru adopție',
                'required_role': 'client',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            adoption = serializer.save()
                        
            return Response({
                'success': True,
                'message': 'Aplicația ta de adopție a fost trimisă cu succes!',
                'data': AdoptionDetailSerializer(adoption, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='schedule-visit')
    def schedule_visit(self, request, pk=None):
        """POST /adoptions/{id}/schedule-visit/"""
        roles = get_user_roles(request)
        adoption = self.get_object()
        
        if 'admin' not in roles and adoption.user != request.user:
            return Response({
                'success': False,
                'error': 'Only administrators can schedule visits.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if adoption.status != 'AP':
            return Response({
                'success': False,
                'error': 'The visit can only be scheduled for approved applications.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = AdoptionScheduleVisitSerializer(data=request.data)
        if serializer.is_valid():
            adoption.visit_scheduled = True
            adoption.visit_date = serializer.validated_data['visit_date']
            adoption.visit_notes = serializer.validated_data.get('visit_notes', '')
            adoption.save()
            
            
            return Response({
                'success': True,
                'message': 'Your visit has been scheduled successfully.',
                'data': {
                    'visit_date': adoption.visit_date,
                    'visit_notes': adoption.visit_notes
                }
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['put'], url_path='approve')
    def approve(self, request, pk=None):
        """PUT /adoptions/{id}/approve/ - approve adoption (admin)"""
        roles = get_user_roles(request)
        
        if 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators can approve applications',
                'required_role': 'admin',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        adoption = self.get_object()
        
        if adoption.status != 'PD':
            return Response({
                'success': False,
                'error': f'The application is already {adoption.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        adoption.status = 'AP'
        adoption.reviewed_by = request.user
        adoption.reviewed_at = timezone.now()
        adoption.save()
        
        adoption.animal.status = 'PD'  
        adoption.animal.save()
        
        
        return Response({
            'success': True,
            'message': f'The application for {adoption.animal.name} has been approved',
            'data': AdoptionDetailSerializer(adoption, context={'request': request}).data
        })
    
    @action(detail=True, methods=['put'], url_path='reject')
    def reject(self, request, pk=None):
        """PUT /adoptions/{id}/reject/ - reject adoption (admin)"""
        roles = get_user_roles(request)
        
        if 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators can reject applications',
                'required_role': 'admin',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        adoption = self.get_object()
        
        if adoption.status != 'PD':
            return Response({
                'success': False,
                'error': f'The application is already {adoption.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = AdoptionReviewSerializer(data=request.data)
        if serializer.is_valid():
            adoption.status = 'RJ'
            adoption.reviewed_by = request.user
            adoption.reviewed_at = timezone.now()
            adoption.rejection_reason = serializer.validated_data.get('rejection_reason', '')
            adoption.save()
            
            
            return Response({
                'success': True,
                'message': f'The application for {adoption.animal.name} has been rejected',
                'data': AdoptionDetailSerializer(adoption, context={'request': request}).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='finalize')
    def finalize(self, request, pk=None):
        """POST /adoptions/{id}/finalize/ - finalize adoption (admin)"""
        roles = get_user_roles(request)
        
        if 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators can finalize adoptions',
                'required_role': 'admin',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        adoption = self.get_object()
        
        if adoption.status != 'AP':
            return Response({
                'success': False,
                'error': 'Only approved applications can be finalized'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        adoption.status = 'FN'
        adoption.finalized_at = timezone.now()
        adoption.save()
        
        adoption.animal.status = 'AD'
        adoption.animal.save()
        
        
        return Response({
            'success': True,
            'message': f'{adoption.animal.name} has been successfully adopted by {adoption.user.username}!',
            'data': AdoptionDetailSerializer(adoption, context={'request': request}).data
        })