from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q, Count

from .models import User, Department
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer,
    DepartmentSerializer, DepartmentListSerializer, DepartmentUpdateSerializer
)
from core.permissions import IsAdminUser
from core.models import Publication

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                if not user.is_active:
                    return Response(
                        {'error': 'Аккаунт деактивирован'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                refresh = RefreshToken.for_user(user)
                return Response({
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }
                })
            return Response(
                {'error': 'Неверные учетные данные'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Успешный выход'})
        except Exception:
            return Response({'message': 'Выход выполнен'})
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Неверный текущий пароль'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Пароль успешно изменен'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            return Response({
                'access': str(token.access_token),
            })
        except Exception as e:
            return Response(
                {'error': 'Неверный токен'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    filter_fields = ['role', 'is_active', 'department']
    ordering_fields = ['username', 'date_joined']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return User.objects.all()
        return User.objects.filter(role='METHODIST')
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def set_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get('role')
        if new_role not in ['ADMIN', 'METHODIST']:
            return Response(
                {'error': 'Неверная роль'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.role = new_role
        user.save()
        return Response(UserSerializer(user).data)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'code'
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return DepartmentUpdateSerializer
        if self.action == 'list':
            return DepartmentListSerializer
        return DepartmentSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def check_department_access(self, department):
        user = self.request.user
        if user.is_admin:
            return True
        if user.department == department.code:
            return True
        return False
    
    def update(self, request, *args, **kwargs):
        department = self.get_object()
        if not self.check_department_access(department):
            return Response(
                {'error': 'У вас нет доступа к редактированию этой кафедры'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def publications(self, request, code=None):
        department = self.get_object()
        publications = Publication.objects.filter(department=code)
        from core.serializers import PublicationListSerializer
        serializer = PublicationListSerializer(publications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, code=None):
        department = self.get_object()
        publications = Publication.objects.filter(department=code)
        
        by_year = publications.values('year').annotate(count=models.Count('id')).order_by('-year')
        by_result = publications.values('result').annotate(count=models.Count('id'))
        
        return Response({
            'total': publications.count(),
            'by_year': list(by_year),
            'by_result': list(by_result),
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_department(self, request):
        user = request.user
        if not user.department:
            return Response(
                {'error': 'У вас не назначена кафедра'},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            department = Department.objects.get(code=user.department)
            return Response(DepartmentSerializer(department).data)
        except Department.DoesNotExist:
            return Response(
                {'error': 'Кафедра не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def can_edit(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'can_edit': False})
        user = request.user
        if user.is_admin:
            return Response({'can_edit': True})
        if user.department == code:
            return Response({'can_edit': True})
        return Response({'can_edit': False})
