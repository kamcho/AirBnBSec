from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import PersonalProfile

MyUser = get_user_model()

class Command(BaseCommand):
    help = 'Creates dummy users with profiles'

    def handle(self, *args, **kwargs):
        # List of users to create
        users_data = [
            {
                'id_number': '36841711',
                'first_name': 'John',
                'last_name': 'Doe',
                'surname': 'Smith',
                'email': 'john.doe@example.com',
                'phone': '+1234567890',
                'location': 'New York',
                'gender': 'M'
            },
            {
                'id_number': '8811986',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'surname': 'Johnson',
                'email': 'jane.smith@example.com',
                'phone': '+1987654321',
                'location': 'Los Angeles',
                'gender': 'F'
            },
            {
                'id_number': '8511024',
                'first_name': 'Robert',
                'last_name': 'Brown',
                'surname': 'Wilson',
                'email': 'robert.brown@example.com',
                'phone': '+1122334455',
                'location': 'Chicago',
                'gender': 'M'
            }
        ]

        password = 'test456'

        for user_data in users_data:
            try:
                # Create user
                user = MyUser.objects.create_user(
                    id_number=user_data['id_number'],
                    password=password
                )
                
                # Create profile
                PersonalProfile.objects.create(
                    user=user,
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    surname=user_data['surname'],
                    email=user_data['email'],
                    phone=user_data['phone'],
                    location=user_data['location'],
                    gender=user_data['gender']
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created user {user_data["id_number"]}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating user {user_data["id_number"]}: {str(e)}')
                ) 