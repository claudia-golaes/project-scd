from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from myapp.models import Visit, Adoption
from myapp.serializers import (
    VisitListSerializer, VisitDetailSerializer,
    VisitConfirmSerializer, VisitReportSerializer
)
from myapp.decorators import get_user_roles


class VisitViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        roles = get_user_roles(self.request)
        
        if 'admin' in roles:
            return Visit.objects.all().select_related('adoption', 'adoption__animal', 'adoption__user', 'volunteer', 'scheduled_by')
        
        if 'volunteer' in roles:
            from django.db.models import Q
            return Visit.objects.filter(
                Q(volunteer=user) | Q(volunteer__isnull=True, status='SC')
            ).select_related('adoption', 'adoption__animal', 'adoption__user', 'volunteer')
        
        return Visit.objects.none()
    
    def get_serializer_class(self):
        if self.action in ['list']:
            return VisitListSerializer
        return VisitDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """GET /visits/ - visit list (for volunteers and admins)"""
        queryset = self.get_queryset()
        
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        upcoming_only = request.query_params.get('upcoming', None)
        if upcoming_only == 'true':
            queryset = queryset.filter(scheduled_date__gte=timezone.now())
        
        serializer = self.get_serializer(queryset, many=True)
        roles = get_user_roles(request)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count(),
            'viewing_as': 'admin' if 'admin' in roles else 'volunteer'
        })
    
    def retrieve(self, request, *args, **kwargs):
        """GET /visits/{id}/ - visit details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """POST /visits/{id}/confirm/ - visit confirm (volunteer)"""
        roles = get_user_roles(request)
        
        if 'volunteer' not in roles and 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only volunteers can confirm visits',
                'required_role': 'volunteer',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        visit = self.get_object()
        
        if visit.status != 'SC':
            return Response({
                'success': False,
                'error': f'The visit is already {visit.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = VisitConfirmSerializer(data=request.data)
        if serializer.is_valid():
            visit.status = 'CF'
            visit.volunteer = request.user
            visit.confirmed_at = timezone.now()
            if serializer.validated_data.get('notes'):
                visit.notes = serializer.validated_data['notes']
            visit.save()
            
            
            return Response({
                'success': True,
                'message': f'You confirmed the visit for {visit.adoption.animal.name}',
                'data': VisitDetailSerializer(visit, context={'request': request}).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='report')
    def report(self, request, pk=None):
        """POST /visits/{id}/report/ - report (volunteer)"""
        roles = get_user_roles(request)
        
        if 'volunteer' not in roles and 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only volunteers can report visits',
                'required_role': 'volunteer',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        visit = self.get_object()
        
        if 'volunteer' in roles and visit.volunteer != request.user:
            return Response({
                'success': False,
                'error': 'You can only report your own visits'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if visit.status not in ['CF', 'SC']:
            return Response({
                'success': False,
                'error': f'The visit is already {visit.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = VisitReportSerializer(data=request.data)
        if serializer.is_valid():
            visit.status = 'CM'
            visit.completed_at = timezone.now()
            visit.report = serializer.validated_data['report']
            visit.animal_behavior = serializer.validated_data['animal_behavior']
            visit.client_interaction = serializer.validated_data['client_interaction']
            visit.recommendation = serializer.validated_data['recommendation']
            visit.notes = serializer.validated_data.get('notes', visit.notes)
            
            if not visit.volunteer:
                visit.volunteer = request.user
            
            visit.save()
            
            
            return Response({
                'success': True,
                'message': f'Report for the visit to {visit.adoption.animal.name} sent successfully',
                'data': VisitDetailSerializer(visit, context={'request': request}).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """POST /visits/{id}/cancel/ - cancel visit (admin or volunteer)"""
        roles = get_user_roles(request)
        visit = self.get_object()
        
        if 'admin' not in roles and visit.volunteer != request.user:
            return Response({
                'success': False,
                'error': 'You do not have permission to perform this action'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if visit.status == 'CM':
            return Response({
                'success': False,
                'error': 'You cannot cancel a completed visit'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        visit.status = 'CN'
        visit.save()
        
        return Response({
            'success': True,
            'message': 'Visit cancelled successfully',
            'data': VisitDetailSerializer(visit, context={'request': request}).data
        })