from datetime import timezone
from rest_framework import serializers
from .models import Animal, Adoption, Visit, Activity
from django.contrib.auth.models import User


class AnimalSerializer(serializers.ModelSerializer):
    is_favorite = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Animal
        fields = ['id', 'name', 'breed', 'age', 'size', 'story', 'image', 'image_url', 'status', 'is_favorite']
        read_only_fields = ['id']
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorites.filter(id=request.user.id).exists()
        return False
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'roles']
        read_only_fields = ['id']
    
    def get_roles(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'session'):
            from .decorators import get_user_roles
            return get_user_roles(request)
        return []


class AnimalCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = ['name', 'breed', 'age', 'size', 'story', 'image', 'status']
    
    def validate_status(self, value):
        valid_statuses = [status[0] for status in Animal.ADOPTION_STATUSES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value
    
    def validate_size(self, value):
        valid_sizes = [size[0] for size in Animal.ANIMAL_SIZES]
        if value not in valid_sizes:
            raise serializers.ValidationError(f"Size must be one of: {', '.join(valid_sizes)}")
        return value


class AdoptionListSerializer(serializers.ModelSerializer):
    """adoption list serializer"""
    animal_name = serializers.CharField(source='animal.name', read_only=True)
    animal_breed = serializers.CharField(source='animal.breed', read_only=True)
    animal_image_url = serializers.SerializerMethodField()
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Adoption
        fields = [
            'id', 'animal', 'animal_name', 'animal_breed', 'animal_image_url',
            'user_name', 'status', 'status_display', 'application_date',
            'visit_scheduled', 'visit_date'
        ]
        read_only_fields = ['id', 'application_date']
    
    def get_animal_image_url(self, obj):
        request = self.context.get('request')
        if obj.animal.image and request:
            return request.build_absolute_uri(obj.animal.image.url)
        return None


class AdoptionDetailSerializer(serializers.ModelSerializer):
    """adoption detail serializer"""
    animal_details = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Adoption
        fields = '__all__'
        read_only_fields = ['id', 'application_date', 'reviewed_by', 'reviewed_at', 'finalized_at']
    
    def get_animal_details(self, obj):
        return AnimalSerializer(obj.animal, context=self.context).data
    
    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }


class AdoptionCreateSerializer(serializers.ModelSerializer):
    """creates an adoption application serializer"""
    class Meta:
        model = Adoption
        fields = ['animal', 'phone', 'address', 'reason', 'experience', 'living_situation']
    
    def validate_animal(self, value):
        if value.status != 'AV':
            raise serializers.ValidationError("This animal is not available for adoption.")
        
        user = self.context['request'].user
        existing = Adoption.objects.filter(
            user=user,
            animal=value,
            status='PD'
        ).exists()
        
        if existing:
            raise serializers.ValidationError("You already have a pending application for this animal.")
        
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AdoptionScheduleVisitSerializer(serializers.Serializer):
    """visit scheduling serializer"""
    visit_date = serializers.DateTimeField()
    visit_notes = serializers.CharField(required=False, allow_blank=True)


class AdoptionReviewSerializer(serializers.Serializer):
    """admin review serializer"""
    rejection_reason = serializers.CharField(required=False, allow_blank=True)



class VisitListSerializer(serializers.ModelSerializer):
    """visits list serializer"""
    animal_name = serializers.CharField(source='adoption.animal.name', read_only=True)
    animal_breed = serializers.CharField(source='adoption.animal.breed', read_only=True)
    client_name = serializers.CharField(source='adoption.user.username', read_only=True)
    client_email = serializers.CharField(source='adoption.user.email', read_only=True)
    volunteer_name = serializers.CharField(source='volunteer.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Visit
        fields = [
            'id', 'adoption', 'animal_name', 'animal_breed',
            'client_name', 'client_email', 'volunteer', 'volunteer_name',
            'scheduled_date', 'status', 'status_display', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class VisitDetailSerializer(serializers.ModelSerializer):
    """visit detail serializer"""
    animal_details = serializers.SerializerMethodField()
    adoption_details = serializers.SerializerMethodField()
    client_details = serializers.SerializerMethodField()
    volunteer_name = serializers.CharField(source='volunteer.username', read_only=True)
    scheduled_by_name = serializers.CharField(source='scheduled_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recommendation_display = serializers.CharField(source='get_recommendation_display', read_only=True)
    
    class Meta:
        model = Visit
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'confirmed_at', 'completed_at', 'scheduled_by']
    
    def get_animal_details(self, obj):
        from myapp.serializers import AnimalSerializer
        return AnimalSerializer(obj.adoption.animal, context=self.context).data
    
    def get_adoption_details(self, obj):
        return {
            'id': obj.adoption.id,
            'status': obj.adoption.status,
            'status_display': obj.adoption.get_status_display(),
            'application_date': obj.adoption.application_date,
            'phone': obj.adoption.phone,
            'address': obj.adoption.address,
        }
    
    def get_client_details(self, obj):
        return {
            'id': obj.adoption.user.id,
            'username': obj.adoption.user.username,
            'email': obj.adoption.user.email,
            'first_name': obj.adoption.user.first_name,
            'last_name': obj.adoption.user.last_name,
        }


class VisitConfirmSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)


class VisitReportSerializer(serializers.Serializer):
    """report serializer"""
    report = serializers.CharField()
    animal_behavior = serializers.CharField()
    client_interaction = serializers.CharField()
    recommendation = serializers.ChoiceField(
        choices=[('AP', 'Approve'), ('RJ', 'Reject'), ('PD', 'Pending')]
    )
    notes = serializers.CharField(required=False, allow_blank=True)

class ActivityListSerializer(serializers.ModelSerializer):
    """serializer for activity list"""
    animal_name = serializers.CharField(source='animal.name', read_only=True)
    animal_id = serializers.IntegerField(source='animal.id', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    is_overdue = serializers.SerializerMethodField()
    time_until_deadline = serializers.SerializerMethodField()
    
    class Meta:
        model = Activity
        fields = [
            'id', 'animal_id', 'animal_name', 'activity_type', 'activity_type_display',
            'title', 'scheduled_time', 'deadline', 'duration_minutes',
            'status', 'status_display', 'priority', 'priority_display',
            'assigned_to', 'assigned_to_name', 'is_overdue', 'time_until_deadline'
        ]
        read_only_fields = ['id']
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()
    
    def get_time_until_deadline(self, obj):
        """returns the time until the deadline in a hr format"""
        from django.utils import timezone
        if obj.deadline > timezone.now():
            delta = obj.deadline - timezone.now()
            hours = delta.total_seconds() / 3600
            if hours < 1:
                return f"{int(delta.total_seconds() / 60)} minute"
            elif hours < 24:
                return f"{int(hours)} ore"
            else:
                return f"{int(hours / 24)} zile"
        return "Expired"


class ActivityDetailSerializer(serializers.ModelSerializer):
    """serializer for detailed activity information"""
    animal_details = serializers.SerializerMethodField()
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    completed_by_name = serializers.CharField(source='completed_by.username', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'assigned_at', 'completed_at',
            'created_by', 'completed_by', 'notification_round'
        ]
    
    def get_animal_details(self, obj):
        return {
            'id': obj.animal.id,
            'name': obj.animal.name,
            'breed': obj.animal.breed,
            'age': obj.animal.age,
        }
    
    def get_is_overdue(self, obj):
        return obj.is_overdue()


class ActivityCreateSerializer(serializers.ModelSerializer):
    """serializer for creating activity (admin)"""
    class Meta:
        model = Activity
        fields = [
            'animal', 'activity_type', 'title', 'description',
            'scheduled_time', 'deadline', 'duration_minutes',
            'priority', 'assigned_to', 'is_recurring', 'recurrence_pattern'
        ]
    
    def validate(self, data):
        if data['deadline'] <= data['scheduled_time']:
            raise serializers.ValidationError("Deadline-ul trebuie să fie după timpul programat.")
        
        if data.get('is_recurring') and not data.get('recurrence_pattern'):
            raise serializers.ValidationError("Pentru activități recurente trebuie specificat pattern-ul.")
        
        return data
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        if validated_data.get('assigned_to'):
            validated_data['status'] = 'AS'
            validated_data['assigned_at'] = timezone.now()
        return super().create(validated_data)


class ActivityCompleteSerializer(serializers.Serializer):
    """activity completion serializer"""
    completion_notes = serializers.CharField(required=True)
    
    def validate_completion_notes(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Completion notes must be at least 10 characters long.")
        return value


class ActivityAcceptSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True)