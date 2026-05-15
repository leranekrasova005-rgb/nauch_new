from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Q
import re
from .models import Publication, DeleteRequest, ActivityLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'role_display', 'phone', 'department', 'date_joined', 'is_active']
        read_only_fields = ['id', 'date_joined']


class PublicationListSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    moderation_status_display = serializers.CharField(source='get_moderation_status_display', read_only=True)
    moderated_by_username = serializers.CharField(source='moderated_by.username', read_only=True)
    citation_db_display = serializers.CharField(source='get_citation_db_display', read_only=True)
    publication_type_display = serializers.CharField(source='get_publication_type_display', read_only=True)
    publication_scope_display = serializers.CharField(source='get_publication_scope_display', read_only=True)
    author_status_display = serializers.CharField(source='get_author_status_display', read_only=True)
    reporting_period_display = serializers.CharField(source='get_reporting_period_display', read_only=True)
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'author', 'year', 'department', 'department_display',
            'result', 'citation_db', 'citation_db_display',
            'publication_type', 'publication_type_display',
            'publication_scope', 'publication_scope_display',
            'author_status', 'author_status_display',
            'reporting_period', 'reporting_period_display',
            'status', 'status_display', 
            'moderation_status', 'moderation_status_display', 'moderated_by_username',
            'owner_username', 'created_at', 'is_archived'
        ]


class PublicationDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)
    moderation_status_display = serializers.CharField(source='get_moderation_status_display', read_only=True)
    moderated_by = UserSerializer(read_only=True)
    citation_db_display = serializers.CharField(source='get_citation_db_display', read_only=True)
    publication_type_display = serializers.CharField(source='get_publication_type_display', read_only=True)
    publication_scope_display = serializers.CharField(source='get_publication_scope_display', read_only=True)
    author_status_display = serializers.CharField(source='get_author_status_display', read_only=True)
    reporting_period_display = serializers.CharField(source='get_reporting_period_display', read_only=True)
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'author', 'head', 'executors',
            'location', 'event_name', 'funding_source', 'volume', 'note',
            'students_names', 'year', 'students_count', 'pages_count',
            'result', 'result_display', 'citation_db', 'citation_db_display',
            'department', 'department_display',
            'publication_type', 'publication_type_display',
            'publication_scope', 'publication_scope_display',
            'author_status', 'author_status_display',
            'pages_count', 'printed_sheets', 'circulation',
            'doi', 'edn_code', 'elibrary_id',
            'reporting_period', 'reporting_period_display', 'reporting_year',
            'entry_month', 'event_date', 'status', 'status_display',
            'moderation_status', 'moderation_status_display', 'moderated_by', 
            'moderated_at', 'moderation_comment', 'is_archived',
            'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'moderated_by', 'moderated_at']


class PublicationCreateSerializer(serializers.ModelSerializer):
    circulation = serializers.CharField(required=False, allow_blank=True, default='0')
    
    class Meta:
        model = Publication
        fields = [
            'title', 'author', 'head', 'executors',
            'location', 'event_name', 'funding_source', 'volume', 'note',
            'students_names', 'year', 'students_count', 'pages_count',
            'result', 'citation_db', 'department', 'entry_month', 'event_date',
            'publication_type', 'publication_scope', 'author_status',
            'publisher', 'printed_sheets', 'circulation',
            'doi', 'edn_code', 'elibrary_id',
            'reporting_period', 'reporting_year'
        ]
    
    def to_internal_value(self, data):
        # Convert circulation string to int before processing
        if 'circulation' in data and isinstance(data['circulation'], str):
            if data['circulation'] == '' or data['circulation'] == 'undefined' or data['circulation'] == 'null':
                data['circulation'] = 0
            else:
                try:
                    data['circulation'] = int(data['circulation'])
                except (ValueError, TypeError):
                    data['circulation'] = 0
        return super().to_internal_value(data)
    
    def validate_publication_type(self, value):
        if value is None or value == '':
            return value  # Allow empty
        if value not in [choice[0] for choice in Publication.PUBLICATION_TYPE_CHOICES]:
            raise serializers.ValidationError("Неверный тип публикации")
        return value
    
    def validate_citation_db(self, value):
        if value is None or value == '':
            return value  # Allow empty
        if value not in [choice[0] for choice in Publication.CITATION_DB_CHOICES]:
            raise serializers.ValidationError("Неверная база цитирования")
        return value
    
    def validate_edn_code(self, value):
        if value:
            if not re.match(r'^[A-Z0-9]{6}$', value.upper()):
                raise serializers.ValidationError("EDN код должен состоять из 6 заглавных букв или цифр")
        return value.upper() if value else value
    
    def validate_doi(self, value):
        if value:
            if not value.startswith('10.'):
                raise serializers.ValidationError("DOI должен начинаться с '10.'")
        return value
    
    def validate(self, attrs):
        publication_type = attrs.get('publication_type')
        author_status = attrs.get('author_status')
        head = attrs.get('head')
        
        # Handle integer fields that come as empty strings
        int_fields = ['students_count', 'pages_count', 'circulation']
        for field in int_fields:
            val = attrs.get(field)
            if val is None or val == '' or val == 'undefined' or val == 'null':
                attrs[field] = 0
            else:
                try:
                    attrs[field] = int(val)
                except (ValueError, TypeError):
                    attrs[field] = 0
        
        # Convert empty strings to None for choice fields (but set default for result)
        choice_fields = ['result', 'citation_db', 'publication_type', 
                         'publication_scope', 'reporting_period']
        for field in choice_fields:
            if field in attrs and attrs[field] == '':
                if field == 'result':
                    attrs[field] = ''  # Keep as empty string, not None
                else:
                    attrs[field] = None
        
        # author_status is NOT converted to None, it stays as-is
        # If it's empty, we just don't validate it
        
        if publication_type == 'student_article' and author_status == 'student':
            if not head:
                raise serializers.ValidationError({
                    'head': 'Для студенческой статьи требуется научный руководитель'
                })
        
        # Handle department - set default if empty
        if not attrs.get('department') or attrs.get('department') == '':
            attrs['department'] = 'КТОиТК'
        
        return super().validate(attrs)
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        user = self.context['request'].user
        if user.role == 'ADMIN':
            validated_data['status'] = 'active'
            validated_data['moderation_status'] = 'approved'
        else:
            validated_data['status'] = 'marked_for_deletion'
            validated_data['moderation_status'] = 'pending'
        return super().create(validated_data)


class PublicationUpdateSerializer(serializers.ModelSerializer):
    circulation = serializers.CharField(required=False, allow_blank=True, default='0')
    
    class Meta:
        model = Publication
        fields = [
            'title', 'author', 'head', 'executors',
            'location', 'event_name', 'funding_source', 'volume', 'note',
            'students_names', 'year', 'students_count', 'pages_count',
            'result', 'citation_db', 'department', 'entry_month', 'event_date',
            'publication_type', 'publication_scope', 'author_status',
            'publisher', 'printed_sheets', 'circulation',
            'doi', 'edn_code', 'elibrary_id',
            'reporting_period', 'reporting_year'
        ]
    
    def to_internal_value(self, data):
        if 'circulation' in data and isinstance(data['circulation'], str):
            if data['circulation'] == '' or data['circulation'] == 'undefined' or data['circulation'] == 'null':
                data['circulation'] = 0
            else:
                try:
                    data['circulation'] = int(data['circulation'])
                except (ValueError, TypeError):
                    data['circulation'] = 0
        return super().to_internal_value(data)
    
    def validate_edn_code(self, value):
        if value:
            if not re.match(r'^[A-Z0-9]{6}$', value.upper()):
                raise serializers.ValidationError("EDN код должен состоять из 6 заглавных букв или цифр")
        return value.upper() if value else value
    
    def validate_doi(self, value):
        if value:
            if not value.startswith('10.'):
                raise serializers.ValidationError("DOI должен начинаться с '10.'")
        return value
    
    def validate(self, attrs):
        int_fields = ['students_count', 'pages_count', 'circulation']
        for field in int_fields:
            val = attrs.get(field)
            if val is None or val == '' or val == 'undefined' or val == 'null':
                attrs[field] = 0
            else:
                try:
                    attrs[field] = int(val)
                except (ValueError, TypeError):
                    attrs[field] = 0
        
        choice_fields = ['result', 'citation_db', 'publication_type', 
                         'publication_scope', 'reporting_period']
        for field in choice_fields:
            if field in attrs and attrs[field] == '':
                if field == 'result':
                    attrs[field] = ''
                else:
                    attrs[field] = None
        
        return super().validate(attrs)


class PublicationModerateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    comment = serializers.CharField(required=False, allow_blank=True, default='')


class DeleteRequestSerializer(serializers.ModelSerializer):
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    publication_title = serializers.CharField(source='publication.title', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = DeleteRequest
        fields = [
            'id', 'publication', 'publication_title', 'requester', 'requester_username',
            'reason', 'status', 'status_display', 'reviewed_by', 'reviewed_by_username',
            'reviewed_at', 'created_at'
        ]
        read_only_fields = ['id', 'requester', 'status', 'reviewed_by', 'reviewed_at', 'created_at']


class DeleteRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeleteRequest
        fields = ['publication', 'reason']
    
    def create(self, validated_data):
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)


class DeleteRequestUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeleteRequest
        fields = ['status']
    
    def validate_status(self, value):
        if value not in ['approved', 'rejected']:
            raise serializers.ValidationError("Статус должен быть 'approved' или 'rejected'")
        return value
    
    def update(self, instance, validated_data):
        validated_data['reviewed_by'] = self.context['request'].user
        validated_data['reviewed_at'] = timezone.now()
        return super().update(instance, validated_data)


class ActivityLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    publication_title = serializers.CharField(source='publication.title', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_username', 'action', 'action_display',
            'publication', 'publication_title', 'details', 'ip_address', 'timestamp'
        ]


from django.utils import timezone
