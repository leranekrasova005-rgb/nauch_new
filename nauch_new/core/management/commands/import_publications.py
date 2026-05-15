import csv
import logging
import re
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Publication, Publisher
from users.models import User

logger = logging.getLogger(__name__)

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
    'сб труд конф': 'conference_paper',
    'журнал': 'article',
    'монография': 'monograph',
    'учебник': 'textbook',
    'учебное пособие': 'tutorial',
}

CITATION_DB_MAP = {
    'РИНЦ': 'RINC',
    'ВАН': 'VAK',
    'ВАК': 'VAK',
    'WOS': 'WOS',
    'Scopus': 'SCOPUS',
    'SCOPUS': 'SCOPUS',
    'Другие издания': 'OTHER_DB',
    'Др издания': 'OTHER_DB',
    'НН': 'NONE',
    '': 'NONE',
    None: 'NONE',
}

AUTHOR_STATUS_MAP = {
    'штатный сотрудник': 'staff',
    'студент': 'student',
    'совместитель': 'compatibility',
    'внешний сотрудник': 'external',
    'совмест': 'compatibility',
}

PUBLICATION_SCOPE_MAP = {
    'Международное': 'international',
    'Всероссийское': 'all_russian',
    'Региональное': 'regional',
    'Межвузовское': 'interuniversity',
    'Внутривузовское': 'internal',
}

DEPARTMENT_MAP = {
    'УПиК': 'КУПД',
    'ГПД': 'КГПД',
    'ГрПД': 'КГрПД',
    'ЭТиМЭО': 'КЭТиМЭО',
    'ЭТиМО': 'КЭТиМЭО',
    'УиЭТД': 'КУиЭТД',
    'ТОиТК': 'КТОиТК',
    'ТиТЭ': 'КТиТЭ',
    'ИЯ': 'КИЯ',
    'ИиИТТ': 'КИиИТТ',
    'ФП': 'КФП',
    'ГД': 'КГД',
}

REPORTING_PERIOD_MAP = {
    '1 квартал': '1_quarter',
    '2 квартал': '2_quarter',
    '3 квартал': '3_quarter',
    '4 квартал': '4_quarter',
    '1 период': '1_period',
    '2 период': '2_period',
    '3 период': '3_period',
    '4 период': '4_period',
    'Годовой отчёт': 'annual',
    'годовой отчет': 'annual',
}


class Command(BaseCommand):
    help = 'Импорт публикаций из CSV файла'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Путь к CSV файлу')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Пробный запуск без сохранения в базу',
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Пропускать ошибочные записи',
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        skip_errors = options['skip_errors']

        if not csv_file:
            raise CommandError('Укажите путь к CSV файлу')

        self.stdout.write(f'Начало импорта из {csv_file}')

        imported = 0
        skipped = 0
        errors = []

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                rows = list(reader)
                total = len(rows)
                self.stdout.write(f'Всего записей: {total}')

                for idx, row in enumerate(rows, 1):
                    try:
                        with transaction.atomic():
                            publication = self._parse_row(row)
                            if not dry_run:
                                publication.save()
                                imported += 1
                            else:
                                imported += 1

                            if idx % 100 == 0:
                                self.stdout.write(f'Обработано: {idx}/{total}')

                    except Exception as e:
                        error_msg = f'Строка {idx}: {str(e)}'
                        logger.error(error_msg)
                        errors.append(error_msg)
                        
                        if skip_errors:
                            skipped += 1
                            continue
                        else:
                            raise CommandError(error_msg)

        except FileNotFoundError:
            raise CommandError(f'Файл не найден: {csv_file}')
        except Exception as e:
            raise CommandError(f'Ошибка при чтении файла: {str(e)}')

        self.stdout.write(self.style.SUCCESS(
            f'\nИмпорт завершён!'
        ))
        self.stdout.write(f'Импортировано: {imported}')
        self.stdout.write(f'Пропущено: {skipped}')
        
        if errors:
            self.stdout.write(self.style.ERROR(f'Ошибок: {len(errors)}'))
            for error in errors[:10]:
                self.stdout.write(f'  - {error}')
            if len(errors) > 10:
                self.stdout.write(f'  ... и ещё {len(errors) - 10} ошибок')

    def _parse_row(self, row):
        title = row.get('Название', '').strip()
        if not title:
            raise ValueError('Пустое название')

        author = row.get('Автор', '').strip()
        if not author:
            author = 'Неизвестный'

        pub_type_raw = row.get('Тип научного труда', '').strip()
        publication_type = PUBLICATION_TYPE_MAP.get(pub_type_raw, '')

        citation_db_raw = row.get('База данных и система цитирования', '')
        citation_db = CITATION_DB_MAP.get(citation_db_raw.strip(), 'NONE')

        author_status_raw = row.get('Статус автора', '').strip()
        author_status = AUTHOR_STATUS_MAP.get(author_status_raw, '')

        department_raw = row.get('Кафедра1', '').strip()
        department = DEPARTMENT_MAP.get(department_raw, department_raw)

        year_raw = row.get('Год издания', '')
        try:
            year = int(year_raw) if year_raw else 2016
        except ValueError:
            year = 2016

        publisher_name = row.get('Издательство', '').strip()
        publisher = None
        if publisher_name:
            publisher, _ = Publisher.objects.get_or_create(
                name=publisher_name,
                defaults={'name': publisher_name}
            )

        pages_count_raw = row.get('Количество страниц', '').strip()
        try:
            pages_count = int(pages_count_raw) if pages_count_raw else 0
        except ValueError:
            pages_count = 0

        printed_sheets_raw = row.get('Объём (п.л.)', '').strip()
        try:
            printed_sheets = float(printed_sheets_raw.replace(',', '.')) if printed_sheets_raw else 0
        except ValueError:
            printed_sheets = 0

        circulation_raw = row.get('Тираж', '').strip()
        try:
            circulation = int(circulation_raw) if circulation_raw else 0
        except ValueError:
            circulation = 0

        reporting_period_raw = row.get('Отчет за полугодие', '')
        if not reporting_period_raw:
            reporting_period_raw = row.get('4 квартал', '')
        
        # Map various values to standard periods
        if reporting_period_raw:
            rp_lower = reporting_period_raw.strip().lower()
            if '1' in rp_lower and ('полугод' in rp_lower or 'полгода' in rp_lower):
                reporting_period = '1_period'
            elif '2' in rp_lower and 'полугод' in rp_lower:
                reporting_period = '2_period'
            elif '1 квартал' in rp_lower or 'i квартал' in rp_lower:
                reporting_period = '1_quarter'
            elif '2 квартал' in rp_lower or 'ii квартал' in rp_lower:
                reporting_period = '2_quarter'
            elif '3 квартал' in rp_lower or 'iii квартал' in rp_lower:
                reporting_period = '3_quarter'
            elif '4 квартал' in rp_lower or 'iv квартал' in rp_lower:
                reporting_period = '4_quarter'
            elif 'год' in rp_lower:
                reporting_period = 'annual'
            else:
                reporting_period = ''
        else:
            reporting_period = ''

        reporting_year_raw = row.get('Годовой отчет', '').strip()
        if not reporting_year_raw:
            reporting_year_raw = str(year)
        reporting_year = reporting_year_raw

        location = row.get('Место проведения', '').strip()
        event_name = row.get('Название мероприятия', '').strip()
        
        head = row.get('Руководитель', '').strip()
        executors = row.get('Исполнители', '').strip()
        
        students_count_raw = row.get('Количество студентов', '').strip()
        try:
            students_count = int(students_count_raw) if students_count_raw else 0
        except ValueError:
            students_count = 0

        students_names = row.get('Ф.И.О. студентов', '').strip()
        
        result_raw = row.get('Призер, победитель', '').strip()
        if result_raw:
            if 'победитель' in result_raw.lower():
                result = 'победитель'
            elif 'призер' in result_raw.lower():
                result = 'призёр'
            else:
                result = 'участник'
        else:
            result = ''

        event_date_str = row.get('Дата проведения', '').strip()
        event_date = None
        if event_date_str:
            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        keywords = row.get('Рейтинг', '').strip()
        note = row.get('Примечание', '').strip()
        funding_source = row.get('Источник финансирования', '').strip()

        moderation_status = 'approved'
        if row.get('Одобрено', '').strip() in ('0', '', None):
            moderation_status = 'pending'

        entry_month_str = row.get('Месяц внесения', '').strip()
        if entry_month_str:
            month_map = {
                'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4,
                'май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
                'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12,
            }
            entry_month = month_map.get(entry_month_str.lower(), 3)
        else:
            entry_month = 3

        publication = Publication(
            title=title,
            author=author,
            publication_type=publication_type,
            citation_db=citation_db,
            author_status=author_status,
            department=department,
            year=year,
            publisher=publisher,
            pages_count=pages_count,
            printed_sheets=printed_sheets,
            circulation=circulation,
            reporting_period=reporting_period,
            reporting_year=reporting_year,
            location=location,
            event_name=event_name,
            head=head,
            executors=executors,
            students_count=students_count,
            students_names=students_names,
            result=result,
            event_date=event_date,
            keywords=keywords,
            note=note,
            funding_source=funding_source,
            moderation_status=moderation_status,
            entry_month=entry_month,
            status='active',
        )

        return publication
