from django.contrib import admin
from .models import Publication, DeleteRequest, ActivityLog


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'year', 'department', 'status', 'owner', 'created_at']
    list_filter = ['status', 'department', 'year', 'result']
    search_fields = ['title', 'author', 'note']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = [
        ('Основная информация', {
            'fields': ['title', 'author', 'year', 'department', 'result']
        }),
        ('Дополнительные поля', {
            'fields': ['circulation', 'head', 'executors', 'location', 'event_name', 
                      'funding_source', 'volume', 'note', 'students_names',
                      'students_count', 'pages_count', 'entry_month', 'event_date']
        }),
        ('Системные поля', {
            'fields': ['owner', 'status', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(DeleteRequest)
class DeleteRequestAdmin(admin.ModelAdmin):
    list_display = ['publication', 'requester', 'status', 'reviewed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['publication__title', 'requester__username', 'reason']
    readonly_fields = ['created_at', 'reviewed_at']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'publication', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'publication__title']
    readonly_fields = ['user', 'action', 'publication', 'details', 'ip_address', 'timestamp']
