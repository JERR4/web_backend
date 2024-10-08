import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import timedelta, datetime  # Добавлено для использования timedelta и datetime
from ...models import Part, Shipment, PartShipment

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        self.add_users()
        self.add_parts()
        self.add_shipments()

    def add_users(self):
        users_data = [
            {
                'username': 'alice',
                'email': 'alice@example.com',
                'password': 'password123',
                'first_name': 'Alice',
                'last_name': 'Smith'
            },
            {
                'username': 'bob',
                'email': 'bob@example.com',
                'password': 'password123',
                'first_name': 'Bob',
                'last_name': 'Johnson'
            },
            {
                'username': 'carol',
                'email': 'carol@example.com',
                'password': 'password123',
                'first_name': 'Carol',
                'last_name': 'Williams'
            },
            {
                'username': 'dave',
                'email': 'dave@example.com',
                'password': 'password123',
                'first_name': 'Dave',
                'last_name': 'Brown'
            },
            {
                'username': 'eve',
                'email': 'eve@example.com',
                'password': 'password123',
                'first_name': 'Eve',
                'last_name': 'Davis'
            },
            {
                'username': 'jerry',
                'email': 'jerry@example.com',
                'password': 'password123',
                'first_name': 'Jerry',
                'last_name': 'Lewis',
                'is_superuser': True,
                'is_staff': True
            },
        ]

        for user_data in users_data:
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            print(f"Пользователь {user.username} создан")

    def add_parts(self):
        parts_data = [
            {
                'part_name': 'БЛОК ДВИГАТЕЛЯ В СБОРЕ',
                'specification': 'V8 EFI БЕНЗИН',
                'oem_number': 'TF-EXH-2024-010',
                'status': True,
                'image': 'http://localhost:9000/web/parts/1.jpg',
                'short_description': 'Блок двигателя в сборе для V8 EFI БЕНЗИН.',
                'set_composition': '1. Блок двигателя в сборе',
                'dimensions': '90 см х 60 см х 70 см',
                'weight': 200,
            },
            {
                'part_name': 'ТРАНСМИССИОННЫЙ ТОРМОЗ',
                'specification': 'V8 EFI БЕНЗИН',
                'oem_number': 'QX-EXH-2024-005',
                'status': True,
                'image': 'http://localhost:9000/web/parts/2.jpg',
                'short_description': 'Трансмиссионный тормоз для V8 EFI БЕНЗИН.',
                'set_composition': '''1. Барабан - тормоз трансмиссии
2. Винт - крепление диска
3. Задняя пластина - сборка тормоза трансмиссии
4. Болт
5. Комплект - тормозные колодки трансмиссии
6. Комплект - удержание тормозных колодок трансмиссии
7. Комплект - регулятор тормозных колодок трансмиссии
8. Комплект - удержание тормозных колодок трансмиссии
9. Подпорка - тормоз трансмиссии
10. Рычаг - тормоз трансмиссии''',
                'dimensions': '80 см х 40 см х 30 см',
                'weight': 30,
            },
            {
                'part_name': 'ВЫХЛОПНАЯ ТРУБА',
                'specification': 'V8 EFI БЕНЗИН',
                'oem_number': 'ST-EXH-2024-004',
                'status': True,
                'image': 'http://localhost:9000/web/parts/3.jpg',
                'short_description': 'Выхлопная труба для V8 EFI БЕНЗИН.',
                'set_composition': '''1. Сборка выхлопной трубы
2. Теплоэкран - система выхлопа топливного бака — 10 штук
3. Накладка - декоративная накладка выхлопной трубы — 2 штуки
4. Гайка - шестигранная — 3 штуки
5. Теплоэкран - задняя часть пола системы выхлопа — 4 штуки
6. Шайба — 5 штук
7. Винт — 6 штук
8. Гайка - фланцевая — 7 штук
9. Крепление - резина системы выхлопа — 8 штук
10. Теплоэкран - запасное колесо системы выхлопа — 9 штук''',
                'dimensions': '120 см х 40 см х 50 см',
                'weight': 15,
            },
            {
                'part_name': 'ТОПЛИВНЫЙ БАК',
                'specification': '2.5L 6 CYL ДИЗЕЛЬ.',
                'oem_number': 'TF-EXH-2024-001',
                'status': True,
                'image': 'http://localhost:9000/web/parts/4.jpg',
                'short_description': 'Сборка топливного бака и сопутствующие детали для 2.5L 6 CYL ДИЗЕЛЬ.',
                'set_composition': '''1. Сборка топливного бака
2. Насос - топливный модуль в сборе с топливным баком
3. Уплотнение - топливный насос модуль бака
4. Кольцо - запорное топливного бака
5. Сборка шланга - вентиляция топлива
6. Зажим - шланг
7. Кронштейн - сборка топливного бака
8. Гайка - шестигранная
9. Шайба - простая
10. Винт - с фланцевой головкой
11. Теплоэкран - топливный бак и система выхлопа
12. Датчик - топливный бак в сборе
13. Винт - специальный, для крепления теплоэкрана к топливному баку
14. Вставка - поддержка шланга/трубки
15. Соединитель - топливные линии
16. Тройник - топливные линии''',
                'dimensions': '150 см х 60 см х 50 см',
                'weight': 40,
            },
            {
                'part_name': 'НАКЛАДКИ ПОРОГОВ',
                'specification': 'ЛЮБАЯ',
                'oem_number': 'TS-EXH-2024-003',
                'status': True,
                'image': 'http://localhost:9000/web/parts/5.jpg',
                'short_description': 'Накладки порогов для кузова любой конфигурации.',
                'set_composition': '''Состав комплекта:
1. Накладка - порог боковой части кузова
2. Пластина - передняя накладка порога пола
3. Пластина - задняя накладка порога пола
4. Капсак
5. Зажим
6. Заклепка - пластиковая, приводная
7. Винт
8. Закладная гайка - слепая''',
                'dimensions': '200 см х 30 см х 10 см',
                'weight': 10,
            }
        ]

        for part_data in parts_data:
            part = Part.objects.create(**part_data)
            print(f"Деталь {part.part_name} создана")

def random_date():
    return datetime.now() - timedelta(days=random.randint(1, 365))