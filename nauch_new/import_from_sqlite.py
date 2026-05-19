#!/usr/bin/env python
"""
Скрипт для импорта данных из CSV файлов в PostgreSQL базу данных.
Данные находятся в папке resut/tables/
"""
import os
import sys
import csv
import django
from datetime import datetime

# Настройка Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['USE_SQLITE'] = 'False'  # Принудительно используем PostgreSQL

django.setup()

from django.db import connection, transaction
from users.models import User, Department
from core.models import Publication, Publisher, DeleteRequest, ActivityLog
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from django.contrib.admin.models import LogEntry


def parse_datetime(value):
    """Парсинг даты/времени из строки."""
    if not value or value == 'NULL':
        return None
    try:
        # Пробуем разные форматы
        for fmt in [
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ]:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def parse_boolean(value):
    """Парсинг булевого значения."""
    if value is None or value == '':
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('1', 'true', 'yes', 't')
    return bool(value)


def parse_int(value, default=None):
    """Парсинг целого числа."""
    if value is None or value == '' or value == 'NULL':
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_float(value, default=0.0):
    """Парсинг числа с плавающей точкой."""
    if value is None or value == '' or value == 'NULL':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def truncate_table(model):
    """Очистка таблицы перед импортом."""
    with connection.cursor() as cursor:
        table_name = model._meta.db_table
        cursor.execute(f'TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;')


def import_users():
    """Импорт пользователей из CSV."""
    print("Импорт пользователей...")
    csv_path = '/workspace/resut/tables/users_user.csv'
    
    if not os.path.exists(csv_path):
        print(f"Файл {csv_path} не найден")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            user_id = parse_int(row.get('id'))
            
            # Пропускаем ID, чтобы PostgreSQL использовал автоинкремент
            user, created = User.objects.update_or_create(
                username=row.get('username', ''),
                defaults={
                    'password': row.get('password', ''),
                    'last_login': parse_datetime(row.get('last_login')),
                    'is_superuser': parse_boolean(row.get('is_superuser')),
                    'first_name': row.get('first_name', ''),
                    'last_name': row.get('last_name', ''),
                    'email': row.get('email', ''),
                    'is_staff': parse_boolean(row.get('is_staff')),
                    'is_active': parse_boolean(row.get('is_active')),
                    'date_joined': parse_datetime(row.get('date_joined')),
                    'phone': row.get('phone', ''),
                    'department': row.get('department', ''),
                    'role': row.get('role', 'NIO_STAFF'),
                }
            )
            # Устанавливаем правильный ID
            if user_id and user.id != user_id:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT setval('users_user_id_seq', %s, true)",
                        [user_id]
                    )
            count += 1
            if count % 100 == 0:
                print(f"  Обработано {count} пользователей")
    
    print(f"Импортировано {count} пользователей")


def import_departments():
    """Импорт кафедр из CSV."""
    print("Импорт кафедр...")
    csv_path = '/workspace/resut/tables/users_department.csv'
    
    if not os.path.exists(csv_path):
        print(f"Файл {csv_path} не найден")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            dept_id = parse_int(row.get('id'))
            
            # Находим заведующего кафедрой
            head_id = parse_int(row.get('head_id'))
            head_user = None
            if head_id:
                try:
                    head_user = User.objects.get(id=head_id)
                except User.DoesNotExist:
                    pass
            
            department, created = Department.objects.update_or_create(
                code=row.get('code', ''),
                defaults={
                    'full_name': row.get('full_name', ''),
                    'short_name': row.get('short_name', ''),
                    'description': row.get('description', ''),
                    'head': head_user,
                    'email': row.get('email', ''),
                    'phone': row.get('phone', ''),
                    'achievements': row.get('achievements', ''),
                }
            )
            count += 1
    
    print(f"Импортировано {count} кафедр")


def import_department_staff():
    """Импорт связей кафедра-сотрудники."""
    print("Импорт связей кафедра-сотрудники...")
    csv_path = '/workspace/resut/tables/users_department_staff.csv'
    
    if not os.path.exists(csv_path):
        print(f"Файл {csv_path} не найден")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            dept_id = parse_int(row.get('department_id'))
            user_id = parse_int(row.get('user_id'))
            
            if dept_id and user_id:
                try:
                    dept = Department.objects.get(id=dept_id)
                    user = User.objects.get(id=user_id)
                    dept.staff.add(user)
                    count += 1
                except (Department.DoesNotExist, User.DoesNotExist):
                    pass
    
    print(f"Импортировано {count} связей")


def import_publishers():
    """Импорт издательств из CSV."""
    print("Импорт издательств...")
    csv_path = '/workspace/resut/tables/core_publisher.csv'
    
    if not os.path.exists(csv_path):
        print(f"Файл {csv_path} не найден")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            pub_id = parse_int(row.get('id'))
            
            publisher, created = Publisher.objects.update_or_create(
                name=row.get('name', 'Unknown'),
                defaults={
                    'city': row.get('city', ''),
                    'country': row.get('country', ''),
                    'website': row.get('website', ''),
                    'email': row.get('email', ''),
                    'phone': row.get('phone', ''),
                }
            )
            count += 1
    
    print(f"Импортировано {count} издательств")


def import_publications():
    """Импорт публикаций из CSV."""
    print("Импорт публикаций...")
    csv_path = '/workspace/resut/tables/core_publication.csv'
    
    if not os.path.exists(csv_path):
        print(f"Файл {csv_path} не найден")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        max_id = 0
        
        for row in reader:
            pub_id = parse_int(row.get('id'))
            if pub_id and pub_id > max_id:
                max_id = pub_id
            
            # Находим владельца и издательство
            owner_id = parse_int(row.get('owner_id'))
            publisher_id = parse_int(row.get('publisher_id'))
            
            owner = None
            if owner_id:
                try:
                    owner = User.objects.get(id=owner_id)
                except User.DoesNotExist:
                    pass
            
            publisher = None
            if publisher_id:
                try:
                    publisher = Publisher.objects.get(id=publisher_id)
                except Publisher.DoesNotExist:
                    pass
            
            moderated_by_id = parse_int(row.get('moderated_by_id'))
            moderated_by = None
            if moderated_by_id:
                try:
                    moderated_by = User.objects.get(id=moderated_by_id)
                except User.DoesNotExist:
                    pass
            
            publication, created = Publication.objects.update_or_create(
                id=pub_id,
                defaults={
                    'title': row.get('title', ''),
                    'author': row.get('author', ''),
                    'circulation': parse_int(row.get('circulation'), 0),
                    'head': row.get('head', ''),
                    'executors': row.get('executors', ''),
                    'location': row.get('location', ''),
                    'event_name': row.get('event_name', ''),
                    'funding_source': row.get('funding_source', ''),
                    'volume': row.get('volume', ''),
                    'note': row.get('note', ''),
                    'students_names': row.get('students_names', ''),
                    'year': parse_int(row.get('year'), datetime.now().year),
                    'students_count': parse_int(row.get('students_count'), 0),
                    'pages_count': parse_int(row.get('pages_count'), 0),
                    'result': row.get('result', ''),
                    'department': row.get('department', 'КТОиТК'),
                    'event_date': parse_datetime(row.get('event_date')),
                    'created_at': parse_datetime(row.get('created_at')) or datetime.now(),
                    'updated_at': parse_datetime(row.get('updated_at')),
                    'status': row.get('status', 'active'),
                    'owner': owner,
                    'keywords': row.get('keywords', ''),
                    'moderated_at': parse_datetime(row.get('moderated_at')),
                    'moderated_by': moderated_by,
                    'moderation_comment': row.get('moderation_comment', ''),
                    'moderation_status': row.get('moderation_status', 'pending'),
                    'citation_db': row.get('citation_db', ''),
                    'author_status': row.get('author_status', ''),
                    'doi': row.get('doi', ''),
                    'edn_code': row.get('edn_code', ''),
                    'elibrary_id': row.get('elibrary_id', ''),
                    'printed_sheets': parse_float(row.get('printed_sheets'), 0.0),
                    'publication_scope': row.get('publication_scope', ''),
                    'publication_type': row.get('publication_type', ''),
                    'reporting_period': row.get('reporting_period', ''),
                    'reporting_year': row.get('reporting_year', ''),
                    'publisher': publisher,
                    'is_archived': parse_boolean(row.get('is_archived')),
                    'entry_month': parse_int(row.get('entry_month'), datetime.now().month),
                }
            )
            count += 1
            if count % 500 == 0:
                print(f"  Обработано {count} публикаций")
        
        # Обновляем последовательность ID
        if max_id:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT setval('core_publication_id_seq', %s, true)",
                    [max_id]
                )
    
    print(f"Импортировано {count} публикаций")


def import_activity_logs():
    """Импорт журнала активности."""
    print("Импорт журнала активности...")
    csv_path = '/workspace/resut/tables/core_activitylog.csv'
    
    if not os.path.exists(csv_path):
        print(f"Файл {csv_path} не найден")
        return
    
    import json
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        
        for row in reader:
            user_id = parse_int(row.get('user_id'))
            publication_id = parse_int(row.get('publication_id'))
            
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass
            
            publication = None
            if publication_id:
                try:
                    publication = Publication.objects.get(id=publication_id)
                except Publication.DoesNotExist:
                    pass
            
            # Парсим JSON детали
            details = {}
            details_str = row.get('details', '{}')
            if details_str:
                try:
                    details = json.loads(details_str)
                except json.JSONDecodeError:
                    details = {'raw': details_str}
            
            activity_log = ActivityLog.objects.create(
                action=row.get('action', ''),
                user=user,
                publication=publication,
                details=details,
                ip_address=row.get('ip_address') if row.get('ip_address') else None,
                timestamp=parse_datetime(row.get('timestamp')),
            )
            count += 1
    
    print(f"Импортировано {count} записей журнала активности")


def import_delete_requests():
    """Импорт запросов на удаление."""
    print("Импорт запросов на удаление...")
    csv_path = '/workspace/resut/tables/core_deleterequest.csv'
    
    if not os.path.exists(csv_path):
        print(f"Файл {csv_path} не найден")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        
        for row in reader:
            requester_id = parse_int(row.get('requester_id'))
            reviewed_by_id = parse_int(row.get('reviewed_by_id'))
            publication_id = parse_int(row.get('publication_id'))
            
            requester = None
            if requester_id:
                try:
                    requester = User.objects.get(id=requester_id)
                except User.DoesNotExist:
                    pass
            
            reviewed_by = None
            if reviewed_by_id:
                try:
                    reviewed_by = User.objects.get(id=reviewed_by_id)
                except User.DoesNotExist:
                    pass
            
            publication = None
            if publication_id:
                try:
                    publication = Publication.objects.get(id=publication_id)
                except Publication.DoesNotExist:
                    pass
            
            delete_request = DeleteRequest.objects.create(
                publication=publication,
                requester=requester,
                reason=row.get('reason', ''),
                status=row.get('status', 'pending'),
                reviewed_by=reviewed_by,
                reviewed_at=parse_datetime(row.get('reviewed_at')),
                created_at=parse_datetime(row.get('created_at')),
            )
            count += 1
    
    print(f"Импортировано {count} запросов на удаление")


def import_django_tables():
    """Импорт системных таблиц Django."""
    print("Импорт системных таблиц Django...")
    
    # Content types
    csv_path = '/workspace/resut/tables/django_content_type.csv'
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                ContentType.objects.get_or_create(
                    id=parse_int(row.get('id')),
                    defaults={
                        'app_label': row.get('app_label', ''),
                        'model': row.get('model', ''),
                    }
                )
                count += 1
            print(f"  Импортировано {count} content types")
    
    # Permissions
    csv_path = '/workspace/resut/tables/auth_permission.csv'
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                Permission.objects.get_or_create(
                    id=parse_int(row.get('id')),
                    defaults={
                        'content_type_id': parse_int(row.get('content_type_id')),
                        'codename': row.get('codename', ''),
                        'name': row.get('name', ''),
                    }
                )
                count += 1
            print(f"  Импортировано {count} permissions")
    
    # Groups
    csv_path = '/workspace/resut/tables/auth_group.csv'
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                Group.objects.get_or_create(
                    id=parse_int(row.get('id')),
                    defaults={
                        'name': row.get('name', ''),
                    }
                )
                count += 1
            print(f"  Импортировано {count} групп")
    
    # Group permissions
    csv_path = '/workspace/resut/tables/auth_group_permissions.csv'
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                group_id = parse_int(row.get('group_id'))
                permission_id = parse_int(row.get('permission_id'))
                if group_id and permission_id:
                    try:
                        group = Group.objects.get(id=group_id)
                        perm = Permission.objects.get(id=permission_id)
                        group.permissions.add(perm)
                        count += 1
                    except (Group.DoesNotExist, Permission.DoesNotExist):
                        pass
            print(f"  Импортировано {count} связей групп и разрешений")
    
    # Admin log
    csv_path = '/workspace/resut/tables/django_admin_log.csv'
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                user_id = parse_int(row.get('user_id'))
                content_type_id = parse_int(row.get('content_type_id'))
                
                user = None
                if user_id:
                    try:
                        user = User.objects.get(id=user_id)
                    except User.DoesNotExist:
                        pass
                
                content_type = None
                if content_type_id:
                    try:
                        content_type = ContentType.objects.get(id=content_type_id)
                    except ContentType.DoesNotExist:
                        pass
                
                LogEntry.objects.create(
                    object_id=row.get('object_id', ''),
                    object_repr=row.get('object_repr', ''),
                    action_flag=row.get('action_flag', ''),
                    change_message=row.get('change_message', ''),
                    content_type=content_type,
                    user=user,
                    action_time=parse_datetime(row.get('action_time')),
                )
                count += 1
            print(f"  Импортировано {count} записей админ-лога")
    
    # Sessions (обычно не нужны для переноса)
    print("  Сессии пропускаются")


@transaction.atomic
def main():
    """Основная функция импорта."""
    print("=" * 60)
    print("Импорт данных из CSV файлов в PostgreSQL")
    print("=" * 60)
    
    # Проверяем подключение к БД
    try:
        connection.ensure_connection()
        print("Подключение к PostgreSQL успешно!")
    except Exception as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
        print("Убедитесь, что:")
        print("  1. PostgreSQL запущен")
        print("  2. Параметры подключения верны (POSTGRES_HOST, POSTGRES_USER, etc.)")
        print("  3. База данных создана")
        return
    
    # Порядок импорта важен из-за внешних ключей
    import_django_tables()
    import_users()
    import_departments()
    import_department_staff()
    import_publishers()
    import_publications()
    import_activity_logs()
    import_delete_requests()
    
    print("=" * 60)
    print("Импорт завершен успешно!")
    print("=" * 60)


if __name__ == '__main__':
    main()
