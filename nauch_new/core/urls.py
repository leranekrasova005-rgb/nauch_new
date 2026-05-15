from django.urls import path
from .views import PublicationViewSet, DeleteRequestViewSet, ActivityLogViewSet

publication_list = PublicationViewSet.as_view({'get': 'list', 'post': 'create'})
publication_detail = PublicationViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})
statistics_view = PublicationViewSet.as_view({'get': 'statistics'})
my_publications_view = PublicationViewSet.as_view({'get': 'my_publications'})
moderate_view = PublicationViewSet.as_view({'post': 'moderate'})
toggle_archive_view = PublicationViewSet.as_view({'post': 'toggle_archive'})
delete_request_list = DeleteRequestViewSet.as_view({'get': 'list', 'post': 'create'})
activity_log_list = ActivityLogViewSet.as_view({'get': 'list'})

urlpatterns = [
    path('publications/statistics/', statistics_view, name='publication-statistics'),
    path('publications/my_publications/', my_publications_view, name='publication-my-publications'),
    path('publications/', publication_list, name='publication-list'),
    path('publications/<pk>/', publication_detail, name='publication-detail'),
    path('publications/<pk>/moderate/', moderate_view),
    path('publications/<pk>/toggle_archive/', toggle_archive_view),
    path('delete-requests/', delete_request_list, name='delete-request-list'),
    path('activity-logs/', activity_log_list, name='activity-log-list'),
]