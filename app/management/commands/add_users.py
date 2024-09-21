from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = "Добавляет пользователей в базу данных"

    def handle(self, *args, **kwargs):
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
        ]

        for user_data in users_data:
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            self.stdout.write(self.style.SUCCESS(f"Пользователь {user.username} успешно добавлен!"))

        self.stdout.write(self.style.SUCCESS("Все пользователи успешно добавлены!"))