from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import MyUser, PublicParticipationTopic, UploadedPicture
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates 100 test uploaded pictures with specific requirements'

    def handle(self, *args, **kwargs):
        try:
            # Get the user and topic
            user = MyUser.objects.get(id_number='36841711')
            topic = PublicParticipationTopic.objects.get(id=1)
            
            # Define status distribution
            statuses = ['rejected'] * 2 + ['flagged'] * 3 + ['pending'] * 4 + ['approved'] * 91
            
            # Create 100 pictures
            for i in range(100):
                # Random date within 3-day window
                random_days = random.randint(0, 2)
                random_hours = random.randint(0, 23)
                random_minutes = random.randint(0, 59)
                uploaded_at = timezone.now() - timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
                
                # Get random status
                status = random.choice(statuses)
                
                # Set is_processed and status_boolean based on status
                is_processed = status != 'pending'
                status_boolean = status != 'pending'
                
                # Set active based on status
                active = status == 'approved'
                
                # Create the picture object
                picture = UploadedPicture.objects.create(
                    uploaded_by=user,
                    topic=topic,
                    description=f'Test picture {i+1}',
                    uploaded_at=uploaded_at,
                    status=status,
                    is_processed=is_processed,
                    status_boolean=status_boolean,
                    active=active
                )
                
                self.stdout.write(self.style.SUCCESS(f'Created picture {i+1} with status {status}'))
                
        except MyUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('User with ID number 36841711 not found'))
        except PublicParticipationTopic.DoesNotExist:
            self.stdout.write(self.style.ERROR('Topic with ID 1 not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}')) 