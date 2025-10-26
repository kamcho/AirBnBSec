from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from users.models import MyUser, PublicParticipationTopic, FormSubmission, FormField, TopicFormField
import random
from datetime import timedelta, datetime
import names
from faker import Faker

User = get_user_model()
fake = Faker('en_US')

class Command(BaseCommand):
    help = 'Generates 950 form submissions for housing levy collection topic'

    def handle(self, *args, **kwargs):
        # Get the housing levy topic
        try:
            topic = PublicParticipationTopic.objects.get(reference_number='HL-2024-001')
            FormSubmission.objects.all().delete()
        except PublicParticipationTopic.DoesNotExist:
            self.stdout.write(self.style.ERROR('Topic HL-2024-001 not found'))
            return

        # Create form fields if they don't exist
        form_fields = {
            'employment_status': FormField.objects.get_or_create(
                name='employment_status',
                label='Employment Status',
                field_type='select',
                help_text='What is your current employment status?'
            )[0],
            'income_range': FormField.objects.get_or_create(
                name='income_range',
                label='Monthly Income Range',
                field_type='select',
                help_text='What is your monthly income range?'
            )[0],
            'housing_type': FormField.objects.get_or_create(
                name='housing_type',
                label='Current Housing Type',
                field_type='select',
                help_text='What is your current housing type?'
            )[0],
            'levy_opinion': FormField.objects.get_or_create(
                name='levy_opinion',
                label='Opinion on Housing Levy',
                field_type='select',
                help_text='What is your opinion on the housing levy?'
            )[0],
            'payment_frequency': FormField.objects.get_or_create(
                name='payment_frequency',
                label='Preferred Payment Frequency',
                field_type='select',
                help_text='What is your preferred payment frequency for the levy?'
            )[0],
            'support_level': FormField.objects.get_or_create(
                name='support_level',
                label='Level of Support',
                field_type='select',
                help_text='How strongly do you support the housing levy?'
            )[0]
        }

        # Set up form fields for the topic
        field_options = {
            'employment_status': ['Employed', 'Self-employed', 'Unemployed', 'Retired'],
            'income_range': ['Below 50,000', '50,000-100,000', '100,000-200,000', 'Above 200,000'],
            'housing_type': ['Rental', 'Owned', 'Mortgage', 'Family Home'],
            'levy_opinion': ['Strongly Support', 'Support', 'Neutral', 'Oppose', 'Strongly Oppose'],
            'payment_frequency': ['Monthly', 'Quarterly', 'Annually'],
            'support_level': ['1', '2', '3', '4', '5']
        }

        # Clear existing form fields
        TopicFormField.objects.filter(topic=topic).delete()

        # Create topic form fields
        for order, (field_name, field) in enumerate(form_fields.items()):
            topic_field = TopicFormField.objects.create(
                topic=topic,
                field=field,
                order=order,
                required=True
            )
            topic_field.options = field_options[field_name]
            topic_field.save()

        all_users = MyUser.objects.all()
        
        # Calculate date range for submissions
        end_date = timezone.now()
        start_date = end_date - timedelta(days=45)
        
        # Generate submissions
        for i in range(1250):
            try:
                # Generate random submission date within the 45-day window
                random_days = random.randint(0, 45)
                random_hours = random.randint(0, 23)
                random_minutes = random.randint(0, 59)
                random_seconds = random.randint(0, 59)
                
                submission_date = start_date + timedelta(
                    days=random_days,
                    hours=random_hours,
                    minutes=random_minutes,
                    seconds=random_seconds
                )

                # Create form submission
                submission = FormSubmission.objects.create(
                    topic=topic,
                    submitted_by=random.choice(all_users),
                    submitted_by_type='Web Site',
                    data={
                        'employment_status': random.choice(field_options['employment_status']),
                        'income_range': random.choice(field_options['income_range']),
                        'housing_type': random.choice(field_options['housing_type']),
                        'levy_opinion': random.choice(field_options['levy_opinion']),
                        'payment_frequency': random.choice(field_options['payment_frequency']),
                        'support_level': random.choice(field_options['support_level']),
                        'additional_comments': fake.paragraph(nb_sentences=3) if random.random() > 0.7 else ''
                    },
                    status='approved',
                    created_at=submission_date
                )

                self.stdout.write(self.style.SUCCESS(f'Successfully created submission {i+1}/150: {submission.id}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating submission {i+1}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Successfully generated 150 housing levy submissions'))