from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Администратор'),
        ('METHODIST', 'Методист'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='METHODIST',
        verbose_name='Роль'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    department = models.CharField(max_length=100, blank=True, verbose_name='Кафедра')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.get_full_name() or self.username
    
    @property
    def is_admin(self):
        return self.role == 'ADMIN'
    
    @property
    def is_methodist(self):
        return self.role == 'METHODIST'


class Department(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name='Код кафедры')
    full_name = models.CharField(max_length=255, verbose_name='Полное название')
    short_name = models.CharField(max_length=50, verbose_name='Краткое название')
    description = models.TextField(blank=True, verbose_name='Описание')
    head = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='headed_departments',
        verbose_name='Заведующий кафедрой'
    )
    staff = models.ManyToManyField(
        User,
        related_name='department_staff',
        blank=True,
        verbose_name='Сотрудники кафедры'
    )
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    achievements = models.TextField(blank=True, verbose_name='Достижения')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Кафедра'
        verbose_name_plural = 'Кафедры'
        ordering = ['short_name']

    def __str__(self):
        return self.short_name

    def get_member_count(self):
        return self.staff.count()
    
    def get_publications_count(self):
        from core.models import Publication
        return Publication.objects.filter(department=self.code).count()
