from django.core.management.base import BaseCommand
from users.models import FormField, TopicFormField, PublicParticipationTopic

class Command(BaseCommand):
    help = 'Sets up form fields for topics'

    def handle(self, *args, **kwargs):
        # Create base form fields
        form_fields = {
            'location': FormField.objects.get_or_create(
                name='location',
                label='Location',
                field_type='text',
                help_text='Enter the location where the image was taken'
            )[0],
            'date_taken': FormField.objects.get_or_create(
                name='date_taken',
                label='Date Taken',
                field_type='date',
                help_text='When was this image taken?'
            )[0],
            'description': FormField.objects.get_or_create(
                name='description',
                label='Description',
                field_type='textarea',
                help_text='Provide a detailed description of what is shown in the image'
            )[0],
            'category': FormField.objects.get_or_create(
                name='category',
                label='Category',
                field_type='select',
                help_text='Select the category that best describes this image'
            )[0],
            'urgency': FormField.objects.get_or_create(
                name='urgency',
                label='Urgency Level',
                field_type='select',
                help_text='How urgent is this issue?'
            )[0],
            'impact': FormField.objects.get_or_create(
                name='impact',
                label='Impact',
                field_type='select',
                help_text='What is the potential impact of this issue?'
            )[0],
        }

        # Define options for select fields
        field_options = {
            'category': ['Infrastructure', 'Environment', 'Community', 'Other'],
            'urgency': ['Low', 'Medium', 'High', 'Critical'],
            'impact': ['Local', 'Neighborhood', 'City-wide', 'Regional']
        }

        # Set up form fields for each topic
        for topic in PublicParticipationTopic.objects.all():
            # Clear existing form fields
            TopicFormField.objects.filter(topic=topic).delete()

            # Add form fields based on topic category
            if topic.category == 'infrastructure':
                fields = ['location', 'date_taken', 'description', 'category', 'urgency', 'impact']
            elif topic.category == 'environment':
                fields = ['location', 'date_taken', 'description', 'category', 'impact']
            elif topic.category == 'community':
                fields = ['location', 'date_taken', 'description', 'category', 'impact']
            else:
                fields = ['location', 'date_taken', 'description', 'category']

            # Create topic form fields
            for order, field_name in enumerate(fields):
                field = form_fields[field_name]
                topic_field = TopicFormField.objects.create(
                    topic=topic,
                    field=field,
                    order=order,
                    required=(field_name != 'description')  # Make description optional
                )
                
                # Add options for select fields
                if field_name in field_options:
                    topic_field.options = field_options[field_name]
                    topic_field.save()

        self.stdout.write(self.style.SUCCESS('Successfully set up form fields for all topics')) 