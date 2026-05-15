from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
from django.conf import settings


def current_year():
    return datetime.date.today().year


class Publication(models.Model):
    RESULT_CHOICES = [
        ('участник', 'Участник'),
        ('призёр', 'Призёр'),
        ('победитель', 'Победитель'),
    ]

    DEPARTMENT_CHOICES = [
        ('КТОиТК', 'Кафедра таможенных операций и таможенного контроля'),
        ('КТиТЭ', 'Кафедра товароведения и таможенной экспертизы'),
        ('КУиЭТД', 'Кафедра управления и экономики таможенного дела'),
        ('КЭТиМЭО', 'Кафедра экономической теории и международных экономических отношений'),
        ('КГПД', 'Кафедра государственно-правовых дисциплин'),
        ('КГрПД', 'Кафедра гражданско-правовых дисциплин'),
        ('КУПД', 'Кафедра уголовно-правовых дисциплин'),
        ('КГД', 'Кафедра гуманитарных дисциплин'),
        ('КИЯ', 'Кафедра иностранных языков'),
        ('КИиИТТ', 'Кафедра информатики и информационных таможенных технологий'),
        ('КФП', 'Кафедра физической подготовки'),
    ]

    MONTH_CHOICES = [
        (1, 'Январь'), (2, 'Февраль'), (3, 'Март'), (4, 'Апрель'),
        (5, 'Май'), (6, 'Июнь'), (7, 'Июль'), (8, 'Август'),
        (9, 'Сентябрь'), (10, 'Октябрь'), (11, 'Ноябрь'), (12, 'Декабрь'),
    ]

    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('marked_for_deletion', 'Помечена на удаление'),
        ('archived', 'Архивирована'),
    ]

    MODERATION_STATUS = [
        ('pending', 'На модерации'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]

    CITATION_DB_CHOICES = [
        ('RINC', 'РИНЦ'),
        ('VAK', 'ВАК'),
        ('WOS', 'WOS'),
        ('SCOPUS', 'Scopus'),
        ('OTHER_DB', 'Другие издания'),
        ('NONE', 'Без индексации'),
    ]

    PUBLICATION_TYPE_CHOICES = [
        ('article', 'Статья'),
        ('student_article', 'Статья студента'),
        ('monograph', 'Монография'),
        ('textbook', 'Учебник'),
        ('tutorial', 'Учебное пособие'),
        ('conference_paper', 'Тезисы докладов'),
        ('software_certificate', 'Свидетельство ЭВМ'),
        ('patent', 'Патенты на изобретения'),
        ('student_research', 'НИРС'),
        ('conference', 'Научная конференция'),
        ('forum', 'Научный форум'),
        ('competition', 'Научный конкурс'),
        ('exhibition', 'Выставка'),
        ('round_table', 'Круглый стол'),
        ('conference_collection', 'Сборник трудов конференции'),
    ]

    PUBLICATION_SCOPE_CHOICES = [
        ('international', 'Международное'),
        ('all_russian', 'Всероссийское'),
        ('regional', 'Региональное'),
        ('interuniversity', 'Межвузовское'),
        ('internal', 'Внутривузовское'),
    ]

    AUTHOR_STATUS_CHOICES = [
        ('staff', 'Штатный сотрудник'),
        ('student', 'Студент'),
        ('compatibility', 'Совместитель'),
        ('external', 'Внешний сотрудник'),
    ]

    REPORTING_PERIOD_CHOICES = [
        ('1_quarter', '1 квартал'),
        ('2_quarter', '2 квартал'),
        ('3_quarter', '3 квартал'),
        ('4_quarter', '4 квартал'),
        ('1_period', '1 период'),
        ('2_period', '2 период'),
        ('3_period', '3 период'),
        ('4_period', '4 период'),
        ('annual', 'Годовой отчёт'),
    ]

    title = models.TextField(verbose_name='Название публикации/мероприятия')
    author = models.TextField(verbose_name='Автор(ы)')
    
    head = models.CharField(max_length=255, blank=True, verbose_name='Руководитель')
    executors = models.TextField(blank=True, verbose_name='Исполнители')
    location = models.CharField(max_length=255, blank=True, verbose_name='Место проведения')
    event_name = models.CharField(max_length=255, blank=True, verbose_name='Название мероприятия')
    funding_source = models.CharField(max_length=255, blank=True, verbose_name='Источник финансирования')
    volume = models.CharField(max_length=100, blank=True, verbose_name='Объём')
    note = models.TextField(blank=True, verbose_name='Примечание')
    keywords = models.CharField(max_length=255, blank=True, verbose_name='Ключевые слова')
    students_names = models.TextField(blank=True, verbose_name='ФИО студентов')

    year = models.IntegerField(
        verbose_name='Год издания',
        validators=[MinValueValidator(1900), MaxValueValidator(current_year)]
    )
    students_count = models.PositiveIntegerField(default=0, verbose_name='Количество студентов')
    pages_count = models.PositiveIntegerField(default=0, verbose_name='Количество страниц')

    result = models.CharField(max_length=20, choices=RESULT_CHOICES, blank=True, verbose_name='Результат')
    citation_db = models.CharField(max_length=50, choices=CITATION_DB_CHOICES, blank=True, verbose_name='База данных и система цитирования')
    
    publication_type = models.CharField(
        max_length=30,
        choices=PUBLICATION_TYPE_CHOICES,
        blank=True,
        verbose_name='Тип публикации'
    )
    publication_scope = models.CharField(
        max_length=20,
        choices=PUBLICATION_SCOPE_CHOICES,
        blank=True,
        verbose_name='Уровень публикации'
    )
    
    publisher = models.ForeignKey(
        'Publisher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='publications',
        verbose_name='Издательство'
    )
    printed_sheets = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name='Объём в печатных листах'
    )
    circulation = models.PositiveIntegerField(default=0, verbose_name='Тираж')
    
    doi = models.CharField(max_length=100, blank=True, verbose_name='DOI')
    edn_code = models.CharField(max_length=20, blank=True, verbose_name='EDN')
    elibrary_id = models.CharField(max_length=50, blank=True, verbose_name='ELibrary ID')
    
    reporting_period = models.CharField(
        max_length=20,
        choices=REPORTING_PERIOD_CHOICES,
        blank=True,
        verbose_name='Отчётный период'
    )
    reporting_year = models.CharField(max_length=10, blank=True, verbose_name='Отчётный год')
    
    author_status = models.CharField(
        max_length=20,
        choices=AUTHOR_STATUS_CHOICES,
        blank=True,
        verbose_name='Статус автора'
    )
    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, blank=True, default='КТОиТК', verbose_name='Кафедра')
    entry_month = models.IntegerField(choices=MONTH_CHOICES, default=datetime.date.today().month, verbose_name='Месяц внесения')
    event_date = models.DateField(null=True, blank=True, verbose_name='Дата проведения')

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='publications',
        verbose_name='Владелец записи'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус записи'
    )
    moderation_status = models.CharField(
        max_length=20,
        choices=MODERATION_STATUS,
        default='pending',
        verbose_name='Статус модерации'
    )
    is_archived = models.BooleanField(default=False, verbose_name='В архиве')
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_publications',
        verbose_name='Кем проверено'
    )
    moderated_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата проверки')
    moderation_comment = models.TextField(blank=True, verbose_name='Комментарий модератора')

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['department', 'year']),
            models.Index(fields=['title']),
            models.Index(fields=['publication_type']),
            models.Index(fields=['citation_db']),
            models.Index(fields=['reporting_period']),
            models.Index(fields=['is_archived', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.author})"


class Publisher(models.Model):
    name = models.TextField(unique=True, verbose_name='Название издательства')
    city = models.CharField(max_length=100, blank=True, verbose_name='Город')
    country = models.CharField(max_length=100, blank=True, verbose_name='Страна')
    website = models.URLField(blank=True, verbose_name='Сайт')
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Издательство'
        verbose_name_plural = 'Издательства'
        ordering = ['name']

    def __str__(self):
        return self.name


class DeleteRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]

    publication = models.ForeignKey(
        Publication,
        on_delete=models.CASCADE,
        related_name='delete_requests',
        verbose_name='Публикация'
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='delete_requests',
        verbose_name='Заявитель'
    )
    reason = models.TextField(verbose_name='Причина удаления')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_delete_requests',
        verbose_name='Кем рассмотрено'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата рассмотрения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Запрос на удаление'
        verbose_name_plural = 'Запросы на удаление'
        ordering = ['-created_at']

    def __str__(self):
        return f"Запрос на удаление #{self.id} - {self.publication.title}"


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Создание'),
        ('update', 'Обновление'),
        ('soft_delete', 'Мягкое удаление'),
        ('hard_delete', 'Физическое удаление'),
        ('restore', 'Восстановление'),
        ('delete_request', 'Запрос на удаление'),
        ('delete_request_approved', 'Одобрение запроса'),
        ('delete_request_rejected', 'Отклонение запроса'),
        ('moderation_approved', 'Публикация одобрена'),
        ('moderation_rejected', 'Публикация отклонена'),
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name='Пользователь'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, verbose_name='Действие')
    publication = models.ForeignKey(
        Publication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name='Публикация'
    )
    details = models.JSONField(default=dict, blank=True, verbose_name='Детали')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP-адрес')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Время')

    class Meta:
        verbose_name = 'Журнал активности'
        verbose_name_plural = 'Журнал активности'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} - {self.user} - {self.timestamp}"
