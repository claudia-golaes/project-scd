from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from myapp.models import Activity, Animal
from myapp.serializers import (
    ActivityListSerializer, ActivityDetailSerializer,
    ActivityCreateSerializer, ActivityCompleteSerializer,
    ActivityAcceptSerializer
)
from myapp.decorators import get_user_roles


class ActivityViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        roles = get_user_roles(self.request)
        
        if 'admin' in roles:
            return Activity.objects.all().select_related(
                'animal', 'assigned_to', 'completed_by', 'created_by'
            )
        
        # volunteers see:
        # 1. activities assigned to them
        # 2. pending activities (unassigned) that they can take over
        if 'volunteer' in roles:
            return Activity.objects.filter(
                Q(assigned_to=user) | Q(status='PD')
            ).select_related('animal', 'assigned_to', 'completed_by')
        
        return Activity.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ActivityCreateSerializer
        elif self.action == 'list':
            return ActivityListSerializer
        return ActivityDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """GET /api/activities/ - list activities"""
        queryset = self.get_queryset()
        roles = get_user_roles(request)
        
        status_filter = request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        priority_filter = request.query_params.get('priority', None)
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)
        
        activity_type = request.query_params.get('type', None)
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        # only today's activities
        today = request.query_params.get('today', None)
        if today == 'true':
            from datetime import date
            queryset = queryset.filter(scheduled_time__date=date.today())
        
        # only upcoming activities
        upcoming = request.query_params.get('upcoming', None)
        if upcoming == 'true':
            queryset = queryset.filter(scheduled_time__gte=timezone.now())
        
        # only overdue activities
        overdue = request.query_params.get('overdue', None)
        if overdue == 'true':
            queryset = queryset.filter(
                status__in=['PD', 'AS', 'IP'],
                deadline__lt=timezone.now()
            )
        
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count(),
            'viewing_as': 'admin' if 'admin' in roles else 'volunteer'
        })
    
    def retrieve(self, request, *args, **kwargs):
        """GET /api/activities/{id}/ - activity details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """POST /api/activities/ - create activity (admin)"""
        roles = get_user_roles(request)
        
        if 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators can create activities',
                'required_role': 'admin',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            activity = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Activity created successfully',
                'data': ActivityDetailSerializer(activity, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """PUT /api/activities/{id}/ - update activity (admin)"""
        roles = get_user_roles(request)
        
        if 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators can update activities',
                'required_role': 'admin',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """DELETE /api/activities/{id}/ - delete activity (admin)"""
        roles = get_user_roles(request)
        
        if 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators can delete activities',
                'required_role': 'admin',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance = self.get_object()
        activity_title = instance.title
        instance.delete()
        
        return Response({
            'success': True,
            'message': f'Activity "{activity_title}" has been deleted'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """GET /api/activities/dashboard/ - daily task dashboard"""
        roles = get_user_roles(request)
        
        if 'volunteer' not in roles and 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only volunteers and admins have access to the dashboard',
                'required_roles': ['volunteer', 'admin'],
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        from datetime import date, timedelta
        today = date.today()
        
        if 'volunteer' in roles:
            today_activities = Activity.objects.filter(
                Q(assigned_to=request.user) | Q(status='PD'),
                scheduled_time__date=today
            ).select_related('animal')
        else:
            today_activities = Activity.objects.filter(
                scheduled_time__date=today
            ).select_related('animal', 'assigned_to')
        
        # stats
        pending = today_activities.filter(status='PD').count()
        in_progress = today_activities.filter(status='IP').count()
        completed = today_activities.filter(status='CM').count()
        overdue = today_activities.filter(
            status__in=['PD', 'AS', 'IP'],
            deadline__lt=timezone.now()
        ).count()
        
        # group by type
        by_type = {}
        for activity in today_activities:
            type_display = activity.get_activity_type_display()
            if type_display not in by_type:
                by_type[type_display] = {
                    'total': 0,
                    'completed': 0,
                    'pending': 0
                }
            by_type[type_display]['total'] += 1
            if activity.status == 'CM':
                by_type[type_display]['completed'] += 1
            elif activity.status in ['PD', 'AS']:
                by_type[type_display]['pending'] += 1
        
        serializer = ActivityListSerializer(today_activities, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'date': today.isoformat(),
            'summary': {
                'total': today_activities.count(),
                'pending': pending,
                'in_progress': in_progress,
                'completed': completed,
                'overdue': overdue,
                'by_type': by_type
            },
            'activities': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """GET /api/activities/pending/ - list pending activities"""
        roles = get_user_roles(request)
        
        if 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only administrators can view all pending activities',
                'required_role': 'admin',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        pending_activities = Activity.objects.filter(
            status__in=['PD', 'AS', 'IP']
        ).select_related('animal', 'assigned_to').order_by('deadline')
        
        serializer = ActivityListSerializer(pending_activities, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': pending_activities.count()
        })
    
    @action(detail=True, methods=['post'], url_path='accept')
    def accept(self, request, pk=None):
        """POST /api/activities/{id}/accept/ - accept task (Be My Eyes)"""
        roles = get_user_roles(request)
        
        if 'volunteer' not in roles:
            return Response({
                'success': False,
                'error': 'Only volunteers can accept tasks',
                'required_role': 'volunteer',
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        activity = self.get_object()
        
        if activity.status not in ['PD']:
            return Response({
                'success': False,
                'error': f'Activity is already {activity.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ActivityAcceptSerializer(data=request.data)
        if serializer.is_valid():
            activity.assigned_to = request.user
            activity.status = 'AS'
            activity.assigned_at = timezone.now()
            
            if serializer.validated_data.get('notes'):
                activity.description += f"\n\nVolunteer note: {serializer.validated_data['notes']}"
            
            activity.save()
            
            return Response({
                'success': True,
                'message': f'You have accepted the task: {activity.title}',
                'data': ActivityDetailSerializer(activity, context={'request': request}).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """POST /api/activities/{id}/complete/ - mark activity as completed"""
        roles = get_user_roles(request)
        activity = self.get_object()
        
        if 'volunteer' in roles and activity.assigned_to != request.user:
            return Response({
                'success': False,
                'error': 'You can only complete activities assigned to you'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if 'volunteer' not in roles and 'admin' not in roles:
            return Response({
                'success': False,
                'error': 'Only volunteers and admins can complete activities',
                'required_roles': ['volunteer', 'admin'],
                'user_roles': roles
            }, status=status.HTTP_403_FORBIDDEN)
        
        if activity.status == 'CM':
            return Response({
                'success': False,
                'error': 'Activity is already completed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ActivityCompleteSerializer(data=request.data)
        if serializer.is_valid():
            activity.status = 'CM'
            activity.completed_by = request.user
            activity.completed_at = timezone.now()
            activity.completion_notes = serializer.validated_data['completion_notes']
            
            if not activity.assigned_to:
                activity.assigned_to = request.user
                activity.assigned_at = timezone.now()
            
            activity.save()
            
            return Response({
                'success': True,
                'message': f'Activity "{activity.title}" has been marked as completed',
                'data': ActivityDetailSerializer(activity, context={'request': request}).data
            })
        
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='start')
    def start(self, request, pk=None):
        """POST /api/activities/{id}/start/ - start activity (change status to In Progress)"""
        roles = get_user_roles(request)
        activity = self.get_object()
        
        if 'volunteer' in roles and activity.assigned_to != request.user:
            return Response({
                'success': False,
                'error': 'You can only start activities assigned to you'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if activity.status not in ['PD', 'AS']:
            return Response({
                'success': False,
                'error': f'Activity is already {activity.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        activity.status = 'IP'
        if not activity.assigned_to:
            activity.assigned_to = request.user
            activity.assigned_at = timezone.now()
        
        activity.save()
        
        return Response({
            'success': True,
            'message': f'Ai început activitatea: {activity.title}',
            'data': ActivityDetailSerializer(activity, context={'request': request}).data
        })