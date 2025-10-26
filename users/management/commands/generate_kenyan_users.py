from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import MyUser, PersonalProfile
from django.utils import timezone
import random
from datetime import timedelta
import names
from faker import Faker

User = get_user_model()
fake = Faker('en_US')

class Command(BaseCommand):
    help = 'Generates 1000 Kenyan user profiles with realistic data'

    def generate_kenyan_id(self):
        return f"{random.randint(10000000, 99999999)}"

    def handle(self, *args, **kwargs):
        # Delete all users except the one with ID 36841711
        self.stdout.write('Deleting all users except ID 36841711...')
        MyUser.objects.exclude(id_number='36841711').delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted other users'))

        counties = [
            'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika', 'Nyeri',
            'Kakamega', 'Kisii', 'Meru', 'Machakos', 'Kiambu', 'Narok', 'Kerugoya',
            'Kitale', 'Malindi', 'Garissa', 'Lodwar', 'Wajir', 'Mandera', 'Marsabit',
            'Isiolo', 'Nanyuki', 'Embu', 'Kitui', 'Voi', 'Homa Bay', 'Bungoma',
            'Busia', 'Migori', 'Siaya', 'Bomet', 'Kericho', 'Kapenguria', 'Kapsabet',
            'Nyamira', 'Muranga', 'Nyahururu', 'Naivasha', 'Ruiru', 'Kikuyu', 'Limuru',
            'Thika', 'Rongai', 'Ongata Rongai', 'Karen', 'Westlands', 'Kilimani',
            'Lavington', 'Donholm'
        ]
        prefixes = ['070', '071', '072', '073', '074', '075', '076', '077', '078', '079', '011', '010']
        genders = ['M', 'F']
      
        for i in range(1000):
            try:
                first_name = names.get_first_name()
                last_name = names.get_last_name()
                email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,9999)}@gmail.com"
                id_number = self.generate_kenyan_id()
                password = 'Password123!'
                phone = f"{random.choice(prefixes)}{random.randint(1000000, 9999999)}"
                address = fake.street_address()
                city = random.choice(counties)
                state = city  # For Kenya, state can be same as county/city
                zip_code = f"{random.randint(10000, 99999)}"
                gender = random.choice(genders)
                location = city
                today = timezone.now().date()
                age = random.randint(18, 65)
                date_of_birth = today - timedelta(days=age*365 + random.randint(0, 364))

                # Create user with hashed password
                user = MyUser.objects.create_user(
                    id_number=id_number,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )

                # Create profile with all required fields
                profile = PersonalProfile.objects.create(
                    user=user,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    address=address,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    gender=gender,
                    location=location,
                    date_of_birth=date_of_birth
                )

                self.stdout.write(self.style.SUCCESS(f'Successfully created user {i+1}/1000: {id_number} {profile.first_name}'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating user {i+1}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully generated 1000 Kenyan user profiles')) 