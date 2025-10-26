from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import MyUser, PublicParticipationTopic, UploadedPicture
from django.core.files import File
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Creates uploads for a user for a specific topic'

    def add_arguments(self, parser):
        parser.add_argument('user_id', type=int, help='ID of the user to create uploads for')
        parser.add_argument('topic_reference', type=str, help='Reference number of the topic')

    def handle(self, *args, **kwargs):
        user_id = kwargs['user_id']
        topic_reference = kwargs['topic_reference']

        # Get the user
        try:
            user = MyUser.objects.get(id=user_id)
        except MyUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User with ID {user_id} does not exist'))
            return

        # Get the topic
        try:
            topic = PublicParticipationTopic.objects.get(reference_number=topic_reference)
        except PublicParticipationTopic.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Topic with reference {topic_reference} does not exist'))
            return

        # Create sample uploads
        sample_images = [
            'sample1.jpg',
            'sample2.jpg',
            'sample3.jpg'
        ]

        # Create a directory for sample images if it doesn't exist
        sample_dir = os.path.join(settings.MEDIA_ROOT, 'sample_images')
        if not os.path.exists(sample_dir):
            os.makedirs(sample_dir)

        # Create uploads
        for image_name in sample_images:
            # Create a sample image file
            image_path = os.path.join(sample_dir, image_name)
            with open(image_path, 'w') as f:
                f.write('Sample image content')

            # Create the upload
            with open(image_path, 'rb') as f:
                upload = UploadedPicture.objects.create(
                    uploaded_by=user,
                    topic=topic,
                    description=f'Sample upload for {topic.title}',
                    status='pending'
                )
                upload.image.save(image_name, File(f), save=True)

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created upload {image_name} for user {user.get_full_name()} and topic {topic.title}')
            )

            # Clean up the sample image file
            os.remove(image_path)

        # Clean up the sample directory
        os.rmdir(sample_dir) 