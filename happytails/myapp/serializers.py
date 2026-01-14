from rest_framework import serializers
from .models import Animal, Adoption
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
            raise serializers.ValidationError("Acest animal nu este disponibil pentru adopție.")
        
        user = self.context['request'].user
        existing = Adoption.objects.filter(
            user=user,
            animal=value,
            status='PD'
        ).exists()
        
        if existing:
            raise serializers.ValidationError("Ai deja o aplicație în așteptare pentru acest animal.")
        
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