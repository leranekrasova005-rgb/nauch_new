#!/usr/bin/env python
import os
import sys
import django
import csv

sys.path.insert(0, '/home/nekrasova/nauch_new')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Publication
from users.models import User

PUBLICATION_TYPE_MAP = {
    'Статья': 'article',
    'Статья студента': 'student_article',
    'Монография': 'monograph',
    'Учебник': 'textbook',
    'Учебное пособие': 'tutorial',
    'Тезисы докладов': 'conference_paper',
    'Свидетельство ЭВМ': 'software_certificate',
    'Патенты на изобретения': 'patent',
    'НИРС': 'student_research',
    'Научная конференция': 'conference',
    'Научный форум': 'forum',
    'Научный конкурс': 'competition',
    'Выставка': 'exhibition',
    'Круглый стол': 'round_table',
    'Сборник трудов конференции': 'conference_collection',
}

AUTHOR_STATUS_MAP = {
    'штатный сотрудник': 'staff',
    'сотрудник': 'staff',
    'студент': 'student',
    'совместитель': 'compatibility',
    'внешний сотрудник': 'external',
}

CITATION_DB_MAP = {
    'РИНЦ': 'RINC',
    'ВАК': 'VAK',
    'WOS': 'WOS',
    'SCOPUS': 'SCOPUS',
    'Scopus': 'SCOPUS',
    'другие издания': 'OTHER_DB',
    'без индексации': 'NONE',
    'нет': 'NONE',
}

DEPARTMENT_MAP = {
    'УПиК': 'КТОиТК',
    'Управление': 'КУиЭТД',
    'ГПД': 'КГПД',
    'ГрПД': 'КГрПД',
    'УПД': 'КУПД',
    'Таможенное дело': 'КТиТЭ',
    'Товароведение': 'КТиТЭ',
    'ГД': 'КГД',
    'ИЯ': 'КИЯ',
    'ИиИТТ': 'КИиИТТ',
    'Физподготовка': 'КФП',
    'Экономика': 'КЭТиМЭО',
    'ЭТ': 'КЭТиМЭО',
}

def s(val):
    return val.strip() if val else ''

def main():
    csv_path = '/home/nekrasova/Desktops/Desktop1/Научные труды и публикации сотрудников-7703-records-20260515_0526-comma_separated.csv'
    
    admin = User.objects.filter(role='ADMIN').first()
    if not admin:
        print('No admin found!')
        return
    
    imported = 0
    errors = 0
    batch = []
    batch_size = 500
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            try:
                title = s(row.get('Название', ''))
                if not title:
                    continue
                
                pub = Publication(
                    title=title,
                    author=s(row.get('Автор', '')),
                    publication_type=PUBLICATION_TYPE_MAP.get(s(row.get('Тип научного труда', '')), 'article'),
                    author_status=AUTHOR_STATUS_MAP.get(s(row.get('Статус автора', '')).lower(), 'staff'),
                    year=int(row.get('Год издания', 2024) or 2024),
                    circulation=int(row.get('Тираж', 0) or 0),
                    citation_db=CITATION_DB_MAP.get(s(row.get('База данных и система цитирования', '')), 'NONE'),
                    head=s(row.get('Руководитель', '')),
                    executors=s(row.get('Исполнители', '')),
                    location=s(row.get('Место проведения', '')),
                    students_count=int(row.get('Количество студентов', 0) or 0),
                    students_names=s(row.get('Ф.И.О. студентов', '')),
                    event_name=s(row.get('Название мероприятия', '')),
                    pages_count=int(row.get('Количество страниц', 0) or 0),
                    funding_source=s(row.get('Источник финансирования', '')),
                    note=s(row.get('Примечание', '')),
                    volume=s(row.get('Объём (п.л.)', '')),
                    department=DEPARTMENT_MAP.get(s(row.get('Кафедра1', '')), 'КТОиТК'),
                    status='active',
                    moderation_status='approved',
                    owner=admin,
                    moderated_by=admin,
                )
                
                result_str = s(row.get('Призер, победитель', '')).lower()
                if 'победитель' in result_str:
                    pub.result = 'победитель'
                elif 'призер' in result_str or 'призёр' in result_str:
                    pub.result = 'призёр'
                
                presentation = s(row.get('Выступление с докладом', '')).lower()
                if presentation == 'да' and not pub.result:
                    pub.result = 'участник'
                
                period = s(row.get('Годовой отчет', ''))
                if '1 квартал' in period or '1 период' in period:
                    pub.reporting_period = '1_quarter'
                elif '2 квартал' in period or '2 период' in period:
                    pub.reporting_period = '2_quarter'
                elif '3 квартал' in period or '3 период' in period:
                    pub.reporting_period = '3_quarter'
                elif '4 квартал' in period or '4 период' in period:
                    pub.reporting_period = '4_quarter'
                elif 'годовой' in period.lower():
                    pub.reporting_period = 'annual'
                
                batch.append(pub)
                
                if len(batch) >= batch_size:
                    Publication.objects.bulk_create(batch)
                    imported += len(batch)
                    print(f'Импортировано: {imported}')
                    batch = []
                    
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f'Error: {e}')
        
        if batch:
            Publication.objects.bulk_create(batch)
            imported += len(batch)
    
    print(f'\nГотово! Импортировано: {imported}, ошибок: {errors}')
    print(f'Всего в базе: {Publication.objects.count()}')

if __name__ == '__main__':
    main()