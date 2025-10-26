from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser with email and password'

    def handle(self, *args, **options):
        User = get_user_model()
        
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS('Superuser already exists!'))
            return
            
        email = 'admin@example.com'  # Change this to your desired email
        password = 'admin123'        # Change this to a secure password
        
        try:
            user = User.objects.create_superuser(
                email=email,
                password=password,
                role='Admin'  # Make sure this matches your User model's role choices
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser with email: {email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))
