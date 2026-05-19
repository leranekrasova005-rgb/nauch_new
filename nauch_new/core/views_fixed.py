from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count, Sum, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.core.cache import cache
import re

from .models import Publication, DeleteRequest, ActivityLog
from .serializers import (
    PublicationListSerializer, PublicationDetailSerializer,
    PublicationCreateSerializer, PublicationUpdateSerializer,
    PublicationModerateSerializer,
    DeleteRequestSerializer, DeleteRequestCreateSerializer,
    ActivityLogSerializer
)
from .permissions import (
    CanCreatePublication, CanUpdateOwnPublication, CanDeletePublication,
    CanManageDeleteRequests, CanViewLogs, is_admin, is_methodist
)


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    permission_classes = [IsAuthenticated]
    filter_fields = ['year', 'department', 'moderation_status', 'status']
    ordering_fields = ['created_at', 'year', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PublicationListSerializer
        if self.action == 'retrieve':
            return PublicationDetailSerializer
        if self.action == 'create':
            return PublicationCreateSerializer
        if self.action in ['update', 'partial_update']:
            return PublicationUpdateSerializer
        return PublicationListSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'retrieve':
            return [AllowAny()]
        if self.action == 'create':
            return [CanCreatePublication()]
        if self.action in ['update', 'partial_update']:
            return [CanUpdateOwnPublication()]
        if self.action == 'destroy':
            return [CanDeletePublication()]
        if self.action in ['statistics', 'export']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        
        q = self.queryset
        
        include_archived = self.request.query_params.get('include_archived', 'false').lower() == 'true'
        
        if not user.is_authenticated:
            q = q.filter(moderation_status='approved', status='active', is_archived=False)
        elif not is_admin(user):
            if not include_archived:
                q = q.filter(
                    Q(moderation_status='approved') | Q(owner=user),
                    status='active',
                    is_archived=False
                )
            else:
                q = q.filter(
                    Q(moderation_status='approved') | Q(owner=user),
                    status='active'
                )
        
        citation_db = self.request.query_params.get('citation_database')
        if citation_db:
            q = q.filter(citation_db=citation_db)
        
        publication_type = self.request.query_params.get('publication_type')
        if publication_type:
            q = q.filter(publication_type=publication_type)
        
        reporting_period = self.request.query_params.get('reporting_period')
        if reporting_period:
            q = q.filter(reporting_period=reporting_period)
        
        year_from = self.request.query_params.get('year_from')
        if year_from:
            q = q.filter(year__gte=int(year_from))
        
        year_to = self.request.query_params.get('year_to')
        if year_to:
            q = q.filter(year__lte=int(year_to))
        
        publication_scope = self.request.query_params.get('publication_scope')
        if publication_scope:
            q = q.filter(publication_scope=publication_scope)
        
        sort_by = self.request.query_params.get('sort_by')
        if sort_by:
            if sort_by == 'year_desc':
                q = q.order_by('-year')
            elif sort_by == 'year_asc':
                q = q.order_by('year')
            elif sort_by == 'title':
                q = q.order_by('title')
            elif sort_by == 'created_desc':
                q = q.order_by('-created_at')
            elif sort_by == 'created_asc':
                q = q.order_by('created_at')
        
        return q

    def perform_create(self, serializer):
        publication = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action='create',
            publication=publication,
            details={'title': publication.title}
        )

    def perform_update(self, serializer):
        old_data = self.get_object()
        publication = serializer.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action='update',
            publication=publication,
            details={
                'title': publication.title,
                'changed_fields': list(serializer.validated_data.keys())
            }
        )

    def perform_destroy(self, instance):
        instance.status = 'archived'
        instance.save()
        ActivityLog.objects.create(
            user=self.request.user,
            action='soft_delete',
            publication=instance,
            details={'title': instance.title}
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def moderate(self, request, pk=None):
        publication = self.get_object()
        if not is_admin(request.user) and not is_methodist(request.user):
            return Response(
                {'error': 'У вас нет прав для модерации'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PublicationModerateSerializer(data=request.data)
        if serializer.is_valid():
            old_status = publication.moderation_status
            publication.moderation_status = serializer.validated_data['status']
            publication.moderated_by = request.user
            publication.moderated_at = timezone.now()
            publication.moderation_comment = serializer.validated_data.get('comment', '')
            publication.save()
            
            action = 'moderation_approved' if publication.moderation_status == 'approved' else 'moderation_rejected'
            ActivityLog.objects.create(
                user=request.user,
                action=action,
                publication=publication,
                details={
                    'old_status': old_status,
                    'new_status': publication.moderation_status,
                    'comment': publication.moderation_comment
                }
            )
            
            self._send_moderation_notification(publication)
            
            return Response(PublicationDetailSerializer(publication).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_archive(self, request, pk=None):
        publication = self.get_object()
        if not is_admin(request.user) and not is_methodist(request.user):
            return Response(
                {'error': 'У вас нет прав для архивирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        publication.is_archived = not publication.is_archived
        publication.save()
        
        return Response({
            'is_archived': publication.is_archived,
            'message': 'Публикация архивирована' if publication.is_archived else 'Публикация восстановлена из архива'
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def archive_old_publications(self, request):
        if not is_admin(request.user):
            return Response(
                {'error': 'Только администратор может архивировать старые публикации'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        year_limit = 2016
        updated_count = Publication.objects.filter(year__lte=year_limit, is_archived=False).update(is_archived=True)
        
        return Response({
            'message': f'Архивировано публикаций до {year_limit}: {updated_count}',
            'updated_count': updated_count
        })
    
    def _send_moderation_notification(self, publication):
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            if not publication.owner or not publication.owner.email:
                return
            
            if publication.moderation_status == 'approved':
                subject = 'Ваша публикация одобрена'
                message = f'Публикация "{publication.title}" была одобрена.'
            elif publication.moderation_status == 'rejected':
                subject = 'Ваша публикация отклонена'
                message = f'Публикация "{publication.title}" была отклонена.'
                if publication.moderation_comment:
                    message += f'\nКомментарий: {publication.moderation_comment}'
            else:
                return
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                recipient_list=[publication.owner.email],
                fail_silently=True,
            )
        except Exception:
            pass

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def stats(self, request):
        cache_key = 'publication_stats_' + '_'.join(
            f'{k}={v}' for k, v in sorted(request.query_params.items())
        )
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)
        
        queryset = self.get_queryset()
        
        total = queryset.count()
        
        by_department = queryset.values('department').annotate(
            count=Count('id')
        ).order_by('-count')
        
        by_year = queryset.values('year').annotate(
            count=Count('id')
        ).order_by('-year')
        
        by_moderation_status = queryset.values('moderation_status').annotate(
            count=Count('id')
        )
        
        by_publication_type = queryset.values('publication_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        by_citation_database = queryset.values('citation_db').annotate(
            count=Count('id')
        ).order_by('-count')
        
        by_publication_scope = queryset.values('publication_scope').annotate(
            count=Count('id')
        ).order_by('-count')
        
        by_reporting_period = queryset.values('reporting_period').annotate(
            count=Count('id'),
            total_printed_sheets=Sum('printed_sheets')
        ).order_by('-count')
        
        key_metrics = {
            'scopus_wos_count': queryset.filter(
                Q(citation_db='WOS') | Q(citation_db='SCOPUS')
            ).count(),
            'vak_count': queryset.filter(citation_db='VAK').count(),
            'rinc_count': queryset.filter(citation_db='RINC').count(),
            'student_count': queryset.filter(
                Q(students_count__gt=0) | Q(author__icontains='студент')
            ).count(),
            'total_printed_sheets': queryset.aggregate(
                total=Sum('printed_sheets')
            )['total'] or 0,
        }
        
        response_data = {
            'total': total,
            'by_department': list(by_department),
            'by_year': list(by_year),
            'by_moderation_status': list(by_moderation_status),
            'by_publication_type': list(by_publication_type),
            'by_citation_database': list(by_citation_database),
            'by_publication_scope': list(by_publication_scope),
            'by_reporting_period': list(by_reporting_period),
            'key_metrics': key_metrics,
        }
        
        cache.set(cache_key, response_data, 3600)
        
        return Response(response_data)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def export(self, request):
        format_type = request.query_params.get('format', 'csv')
        queryset = self.get_queryset()
        
        if format_type == 'csv':
            return self.export_csv(queryset)
        elif format_type == 'xlsx':
            return self.export_xlsx(queryset)
        elif format_type == 'xml':
            return self.export_xml(queryset)
        else:
            return Response(
                {'error': 'Неподдерживаемый формат'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def export_csv(self, queryset):
        import csv
        from django.http import HttpResponse
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'id', 'title', 'author', 'year', 'department',
            'publication_type', 'citation_db', 'result',
            'moderation_status', 'created_at'
        ])
        
        for p in queryset.values(
            'id', 'title', 'author', 'year', 'department',
            'publication_type', 'citation_db', 'result',
            'moderation_status', 'created_at'
        ):
            writer.writerow([
                p['id'], p['title'], p['author'], p['year'], p['department'],
                p['publication_type'], p['citation_db'], p['result'],
                p['moderation_status'], p['created_at']
            ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="publications.csv"'
        return response

    def export_xlsx(self, queryset):
        try:
            import openpyxl
        except ImportError:
            return Response(
                {'error': 'openpyxl не установлен'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        from django.http import HttpResponse
        from io import BytesIO
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Publications'
        
        headers = [
            'id', 'title', 'author', 'year', 'department',
            'publication_type', 'citation_db', 'result',
            'moderation_status', 'created_at'
        ]
        ws.append(headers)
        
        for p in queryset.values(
            'id', 'title', 'author', 'year', 'department',
            'publication_type', 'citation_db', 'result',
            'moderation_status', 'created_at'
        ):
            ws.append([
                p['id'], p['title'], p['author'], p['year'], p['department'],
                p['publication_type'], p['citation_db'], p['result'],
                p['moderation_status'], p['created_at']
            ])
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="publications.xlsx"'
        return response

    def export_xml(self, queryset):
        from django.http import HttpResponse
        import xml.etree.ElementTree as ET
        
        root = ET.Element('publications')
        
        for p in queryset:
            pub = ET.SubElement(root, 'publication')
            ET.SubElement(pub, 'id').text = str(p.id)
            ET.SubElement(pub, 'title').text = p.title
            ET.SubElement(pub, 'author').text = p.author
            ET.SubElement(pub, 'year').text = str(p.year)
            ET.SubElement(pub, 'department').text = p.department
            ET.SubElement(pub, 'publication_type').text = p.publication_type or ''
            ET.SubElement(pub, 'citation_db').text = p.citation_db or ''
            ET.SubElement(pub, 'result').text = p.result or ''
            ET.SubElement(pub, 'moderation_status').text = p.moderation_status
        
        xml_str = ET.tostring(root, encoding='unicode')
        response = HttpResponse(xml_str, content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename="publications.xml"'
        return response


class DeleteRequestViewSet(viewsets.ModelViewSet):
    queryset = DeleteRequest.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DeleteRequestCreateSerializer
        return DeleteRequestSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [CanManageDeleteRequests()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if is_admin(user):
            return DeleteRequest.objects.all()
        return DeleteRequest.objects.filter(requester=user)
    
    def perform_create(self, serializer):
        serializer.save()
    
    def perform_update(self, serializer):
        instance = serializer.save()
        instance.reviewed_by = self.request.user
        instance.reviewed_at = timezone.now()
        instance.save()
        
        action = 'delete_request_approved' if instance.status == 'approved' else 'delete_request_rejected'
        ActivityLog.objects.create(
            user=self.request.user,
            action=action,
            publication=instance.publication,
            details={'request_id': instance.id}
        )


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all()
    permission_classes = [CanViewLogs]
    serializer_class = ActivityLogSerializer
    filter_fields = ['action', 'user']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        user = self.request.user
        if is_admin(user):
            return ActivityLog.objects.all()
        return ActivityLog.objects.none()
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_publications(self, request):
        user = request.user
        queryset = Publication.objects.filter(owner=user, status='active')
        include_archived = request.query_params.get('include_archived', 'false').lower() == 'true'
        if not include_archived:
            queryset = queryset.filter(is_archived=False)
        queryset = queryset.order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PublicationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PublicationListSerializer(queryset, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def statistics(self, request):
        cache_key = 'publication_stats_' + '_'.join(
            f'{k}={v}' for k, v in sorted(request.query_params.items())
        )
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        queryset = self.get_queryset()
        total = queryset.count()
        by_department = queryset.values('department').annotate(count=Count('id')).order_by('-count')
        by_year = queryset.values('year').annotate(count=Count('id')).order_by('-year')
        by_moderation_status = queryset.values('moderation_status').annotate(count=Count('id'))
        by_publication_type = queryset.values('publication_type').annotate(count=Count('id')).order_by('-count')
        by_citation_database = queryset.values('citation_db').annotate(count=Count('id')).order_by('-count')
        by_publication_scope = queryset.values('publication_scope').annotate(count=Count('id')).order_by('-count')
        by_reporting_period = queryset.values('reporting_period').annotate(
            count=Count('id'), total_printed_sheets=Sum('printed_sheets')
        ).order_by('-count')
        key_metrics = {
            'scopus_wos_count': queryset.filter(Q(citation_db='WOS') | Q(citation_db='SCOPUS')).count(),
            'vak_count': queryset.filter(citation_db='VAK').count(),
            'rinc_count': queryset.filter(citation_db='RINC').count(),
            'student_count': queryset.filter(Q(students_count__gt=0) | Q(author__icontains='студент')).count(),
            'total_printed_sheets': queryset.aggregate(total=Sum('printed_sheets'))['total'] or 0,
        }
        response_data = {
            'total': total,
            'by_department': list(by_department),
            'by_year': list(by_year),
            'by_moderation_status': list(by_moderation_status),
            'by_publication_type': list(by_publication_type),
            'by_citation_database': list(by_citation_database),
            'by_publication_scope': list(by_publication_scope),
            'by_reporting_period': list(by_reporting_period),
            'key_metrics': key_metrics,
        }
        cache.set(cache_key, response_data, 3600)
        return Response(response_data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_publications(self, request):
        user = request.user
        queryset = Publication.objects.filter(owner=user, status='active')
        include_archived = request.query_params.get('include_archived', 'false').lower() == 'true'
        if not include_archived:
            queryset = queryset.filter(is_archived=False)
        queryset = queryset.order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PublicationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = PublicationListSerializer(queryset, many=True)
        return Response(serializer.data)
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def statistics(self, request):
        cache_key = 'publication_stats_' + '_'.join(
            f'{k}={v}' for k, v in sorted(request.query_params.items())
        )
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)
        queryset = self.get_queryset()
        total = queryset.count()
        by_department = queryset.values('department').annotate(count=Count('id')).order_by('-count')
        by_year = queryset.values('year').annotate(count=Count('id')).order_by('-year')
        by_moderation_status = queryset.values('moderation_status').annotate(count=Count('id'))
        by_publication_type = queryset.values('publication_type').annotate(count=Count('id')).order_by('-count')
        by_citation_database = queryset.values('citation_db').annotate(count=Count('id')).order_by('-count')
        by_publication_scope = queryset.values('publication_scope').annotate(count=Count('id')).order_by('-count')
        by_reporting_period = queryset.values('reporting_period').annotate(
            count=Count('id'), total_printed_sheets=Sum('printed_sheets')
        ).order_by('-count')
        key_metrics = {
            'scopus_wos_count': queryset.filter(Q(citation_db='WOS') | Q(citation_db='SCOPUS')).count(),
            'vak_count': queryset.filter(citation_db='VAK').count(),
            'rinc_count': queryset.filter(citation_db='RINC').count(),
            'student_count': queryset.filter(Q(students_count__gt=0) | Q(author__icontains='студент')).count(),
            'total_printed_sheets': queryset.aggregate(total=Sum('printed_sheets'))['total'] or 0,
        }
        response_data = {
            'total': total,
            'by_department': list(by_department),
            'by_year': list(by_year),
            'by_moderation_status': list(by_moderation_status),
            'by_publication_type': list(by_publication_type),
            'by_citation_database': list(by_citation_database),
            'by_publication_scope': list(by_publication_scope),
            'by_reporting_period': list(by_reporting_period),
            'key_metrics': key_metrics,
        }
        cache.set(cache_key, response_data, 3600)
        return Response(response_data)
