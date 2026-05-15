from rest_framework import serializers, status
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import User, Department

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    publications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'phone', 'department',
            'is_active', 'date_joined', 'publications_count'
        ]
        read_only_fields = ['id', 'date_joined', 'publications_count']
    
    def get_publications_count(self, obj):
        return obj.publications.count()


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'role', 'phone', 'department']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Пароли не совпадают'})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role', 'phone', 'department', 'is_active']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Пароли не совпадают'})
        return attrs


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class DepartmentSerializer(serializers.ModelSerializer):
    head_name = serializers.CharField(source='head.get_full_name', read_only=True)
    staff_count = serializers.SerializerMethodField()
    publications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'code', 'full_name', 'short_name', 'description',
            'head', 'head_name', 'staff', 'staff_count',
            'email', 'phone', 'achievements',
            'publications_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_staff_count(self, obj):
        return obj.staff.count()
    
    def get_publications_count(self, obj):
        return obj.get_publications_count()


class DepartmentListSerializer(serializers.ModelSerializer):
    head_name = serializers.CharField(source='head.get_full_name', read_only=True)
    staff_count = serializers.SerializerMethodField()
    publications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'code', 'full_name', 'short_name',
            'head', 'head_name', 'staff_count', 'publications_count'
        ]
    
    def get_staff_count(self, obj):
        return obj.staff.count()
    
    def get_publications_count(self, obj):
        return obj.get_publications_count()


class DepartmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            'full_name', 'short_name', 'description',
            'head', 'staff', 'email', 'phone', 'achievements'
        ]
