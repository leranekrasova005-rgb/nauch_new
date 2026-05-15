from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Publication, DeleteRequest
import random
from datetime import datetime, timedelta

User = get_user_model()

DEPARTMENTS = [
    'КТОиТК', 'КТиТЭ', 'КУиЭТД', 'КЭТиМЭО', 'КГПД',
    'КГрПД', 'КУПД', 'КГД', 'КИЯ', 'КИиИТТ', 'КФП'
]

RESULTS = ['участник', 'призёр', 'победитель']

TITLES = [
    'Инновационные подходы к таможенному регулированию',
    'Электронная коммерция и таможенные процедуры',
    'Анализ рисков в таможенном контроле',
    'Таможенная экспертиза товаров',
    'Международная торговля и таможенная политика',
    'Цифровизация таможенных процессов',
    'Таможенное администрирование в ЕАЭС',
    'Контроль качества таможенных услуг',
    'Таможенная логистика и цепочки поставок',
    'Правовые аспекты таможенного дела',
]

AUTHORS = [
    'Иванов А.С.', 'Петрова Е.М.', 'Сидоров В.К.', 'Козлова Н.П.',
    'Смирнов Д.Л.', 'Кузнецова О.И.', 'Васильев А.Н.', 'Попова М.С.',
    'Соколов И.Т.', 'Лебедева Р.Д.', 'Новиков П.К.', 'Морозова А.В.',
]

EVENTS = [
    'Международная конференция',
    'Всероссийский форум',
    'Научный семинар',
    'Олимпиада студентов',
    'Конкурс научных работ',
]


class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными'

    def handle(self, *args, **options):
        self.stdout.write('Создание пользователей...')
        
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан администратор: admin / admin123'))

        methodist, created = User.objects.get_or_create(
            username='methodist',
            defaults={
                'email': 'methodist@example.com',
                'first_name': 'Иван',
                'last_name': 'Петров',
                'role': 'METHODIST',
                'department': 'КТОиТК',
            }
        )
        if created:
            methodist.set_password('methodist123')
            methodist.save()
            self.stdout.write(self.style.SUCCESS(f'Создан методист: methodist / methodist123'))

        methodist2, created = User.objects.get_or_create(
            username='methodist2',
            defaults={
                'email': 'methodist2@example.com',
                'first_name': 'Мария',
                'last_name': 'Сидорова',
                'role': 'METHODIST',
                'department': 'КТиТЭ',
            }
        )
        if created:
            methodist2.set_password('methodist2123')
            methodist2.save()
            self.stdout.write(self.style.SUCCESS(f'Создан методист: methodist2 / methodist2123'))

        self.stdout.write('Создание публикаций...')
        
        publications = []
        for i in range(30):
            owner = random.choice([methodist, methodist2, None])
            pub = Publication(
                title=f"{random.choice(TITLES)} #{i+1}",
                author=random.choice(AUTHORS),
                year=random.randint(2020, 2025),
                department=random.choice(DEPARTMENTS),
                result=random.choice(RESULTS) if random.random() > 0.3 else '',
                circulation=str(random.randint(100, 1000)) if random.random() > 0.5 else '',
                location='Москва' if random.random() > 0.5 else 'Санкт-Петербург',
                event_name=random.choice(EVENTS) if random.random() > 0.5 else '',
                volume=f"{random.randint(1, 20)} п.л.",
                note='Тестовая публикация' if random.random() > 0.7 else '',
                students_count=random.randint(0, 5),
                pages_count=random.randint(5, 50),
                entry_month=random.randint(1, 12),
                event_date=datetime.now().date() - timedelta(days=random.randint(1, 365)),
                owner=owner,
                status='active' if random.random() > 0.1 else 'marked_for_deletion',
            )
            publications.append(pub)
        
        Publication.objects.bulk_create(publications)
        self.stdout.write(self.style.SUCCESS(f'Создано {len(publications)} публикаций'))

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
