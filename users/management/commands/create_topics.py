from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import PublicParticipationTopic, MyUser
from datetime import timedelta

class Command(BaseCommand):
    help = 'Creates initial public participation topics'

    def handle(self, *args, **kwargs):
        # Get or create a superuser for the created_by field
        admin_user = MyUser.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR('No superuser found. Please create a superuser first.'))
            return

        topics_data = [
            # Active Topics
            {
                'title': 'Housing Levy Collection',
                'description': 'Public participation on the implementation and collection of the housing levy. This includes discussion on collection methods, exemptions, and utilization of funds.',
                'category': 'policy',
                'reference_number': 'HL-2024-001',
                'department': 'Ministry of Housing',
                'contact_person': 'John Doe',
                'contact_email': 'housing.levy@gov.ke',
                'contact_phone': '+254700000001',
                'start_date': timezone.now() - timedelta(days=5),
                'end_date': timezone.now() + timedelta(days=25),
            },
            {
                'title': 'Urban Transport Master Plan',
                'description': 'Public participation on the proposed urban transport master plan. This includes discussion on new transport routes, infrastructure development, and sustainable mobility solutions.',
                'category': 'project',
                'reference_number': 'UTMP-2024-001',
                'department': 'Ministry of Transport',
                'contact_person': 'Sarah Johnson',
                'contact_email': 'transport.plan@gov.ke',
                'contact_phone': '+254700000002',
                'start_date': timezone.now() - timedelta(days=2),
                'end_date': timezone.now() + timedelta(days=28),
            },
            # Upcoming Topics
            {
                'title': 'Finance Bill 2025',
                'description': 'Public participation on the proposed Finance Bill 2025. This includes discussion on new tax measures, budget allocations, and economic policies.',
                'category': 'legislation',
                'reference_number': 'FB-2025-001',
                'department': 'National Treasury',
                'contact_person': 'Jane Smith',
                'contact_email': 'finance.bill@gov.ke',
                'contact_phone': '+254700000003',
                'start_date': timezone.now() + timedelta(days=15),
                'end_date': timezone.now() + timedelta(days=45),
            },
            {
                'title': 'Digital Services Tax',
                'description': 'Public participation on the proposed digital services tax framework. This includes discussion on tax rates, collection mechanisms, and impact assessment.',
                'category': 'policy',
                'reference_number': 'DST-2024-001',
                'department': 'Kenya Revenue Authority',
                'contact_person': 'Michael Brown',
                'contact_email': 'digital.tax@gov.ke',
                'contact_phone': '+254700000004',
                'start_date': timezone.now() + timedelta(days=30),
                'end_date': timezone.now() + timedelta(days=60),
            },
            # Closed Topics
            {
                'title': 'Road Damage Levy',
                'description': 'Public participation on the proposed road damage levy. This includes discussion on collection methods, rates, and fund utilization for road maintenance.',
                'category': 'policy',
                'reference_number': 'RDL-2023-001',
                'department': 'Ministry of Transport',
                'contact_person': 'Robert Johnson',
                'contact_email': 'road.levy@gov.ke',
                'contact_phone': '+254700000005',
                'start_date': timezone.now() - timedelta(days=60),
                'end_date': timezone.now() - timedelta(days=30),
            },
            {
                'title': 'Education Curriculum Review',
                'description': 'Public participation on the proposed changes to the national education curriculum. This includes discussion on subject content, teaching methods, and assessment criteria.',
                'category': 'policy',
                'reference_number': 'ECR-2023-001',
                'department': 'Ministry of Education',
                'contact_person': 'Elizabeth Wangari',
                'contact_email': 'curriculum.review@gov.ke',
                'contact_phone': '+254700000006',
                'start_date': timezone.now() - timedelta(days=90),
                'end_date': timezone.now() - timedelta(days=60),
            },
            {
                'title': 'Healthcare Insurance Reform',
                'description': 'Public participation on the proposed healthcare insurance reforms. This includes discussion on coverage, premiums, and service delivery improvements.',
                'category': 'policy',
                'reference_number': 'HIR-2023-001',
                'department': 'Ministry of Health',
                'contact_person': 'Dr. Peter Kamau',
                'contact_email': 'health.reform@gov.ke',
                'contact_phone': '+254700000007',
                'start_date': timezone.now() - timedelta(days=120),
                'end_date': timezone.now() - timedelta(days=90),
            }
        ]

        for topic_data in topics_data:
            # Create topic
            topic, created = PublicParticipationTopic.objects.get_or_create(
                reference_number=topic_data['reference_number'],
                defaults={
                    'title': topic_data['title'],
                    'description': topic_data['description'],
                    'category': topic_data['category'],
                    'department': topic_data['department'],
                    'contact_person': topic_data['contact_person'],
                    'contact_email': topic_data['contact_email'],
                    'contact_phone': topic_data['contact_phone'],
                    'start_date': topic_data['start_date'],
                    'end_date': topic_data['end_date'],
                    'status': 'published',
                    'published_at': topic_data['start_date'],
                    'created_by': admin_user
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created topic "{topic.title}"')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Topic "{topic.title}" already exists')
                ) 