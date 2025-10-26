from django.core.management.base import BaseCommand
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from users.models import PublicParticipationTopic, FormField, FormSubmission, FormResponse
import json
from datetime import datetime

class Command(BaseCommand):
    help = 'Fetches responses from Google Forms and stores them in the database'

    def add_arguments(self, parser):
        parser.add_argument('--topic-id', type=str, help='Topic ID to fetch responses for')

    def handle(self, *args, **kwargs):
        try:
            # Load credentials from service account file
            SCOPES = ['https://www.googleapis.com/auth/forms.responses.readonly']
            SERVICE_ACCOUNT_FILE = 'D:/Public001/stage-425316-253108ec4214.json'

            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES)

            # Build the Forms API service
            forms_service = build('forms', 'v1', credentials=credentials)

            # Get topic ID from arguments
            topic_id = kwargs.get('topic-id')
            if not topic_id:
                self.stdout.write(self.style.ERROR('Topic ID is required'))
                return

            # Get the topic
            try:
                topic = PublicParticipationTopic.objects.get(id=topic_id)
            except PublicParticipationTopic.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Topic with ID {topic_id} does not exist'))
                return

            if not topic.google_form_id:
                self.stdout.write(self.style.ERROR(f'No Google Form ID found for topic {topic_id}'))
                return

            # Get form structure
            form = forms_service.forms().get(formId=topic.google_form_id).execute()
            self.stdout.write("Form structure:")
            self.stdout.write(json.dumps(form, indent=2))

            # Create mapping of question IDs to FormFields
            question_mapping = {}
            for item in form.get('items', []):
                if 'questionItem' in item:
                    item_id = item['itemId']
                    try:
                        # First try to find the field by google_question_id
                        field = FormField.objects.filter(google_question_id=item_id).first()
                        if field:
                            question_mapping[item_id] = field
                            self.stdout.write(f"Mapped question {item_id} ({item['title']}) to FormField {field.id} ({field.name})")
                        else:
                            # Fallback to finding by label
                            field = FormField.objects.get(label=item['title'])
                            question_mapping[item_id] = field
                            self.stdout.write(f"Mapped question {item_id} ({item['title']}) to FormField {field.id} ({field.name})")
                    except FormField.DoesNotExist:
                        self.stdout.write(f"No FormField found for question ID {item_id}")

            # Get responses
            responses = forms_service.forms().responses().list(formId=topic.google_form_id).execute()
            self.stdout.write(f"Found {len(responses.get('responses', []))} responses")

            # Process each response
            for response in responses.get('responses', []):
                self.stdout.write(f"Processing response {response['responseId']}:")
                self.stdout.write(json.dumps(response, indent=2))
                
                # Extract ID number from the response
                id_number = None
                if '00010101' in response['answers']:
                    id_number = response['answers']['00010101']['textAnswers']['answers'][0]['value']
                    if not id_number:
                        self.stdout.write(self.style.WARNING(f"Skipping response {response['responseId']} - Invalid ID number"))
                        continue
                else:
                    self.stdout.write(self.style.WARNING(f"Skipping response {response['responseId']} - No ID number provided"))
                    continue

                # Create form submission
                form_submission = FormSubmission.objects.create(
                    topic=topic,
                    id_number=id_number,
                    submission_date=datetime.fromisoformat(response['lastSubmittedTime'].replace('Z', '+00:00')),
                    status='submitted'
                )

                # Process each answer
                for item_id, answer in response['answers'].items():
                    # Skip the ID number field as it's already processed
                    if item_id == '00010101':
                        continue
                    
                    if item_id in question_mapping:
                        field = question_mapping[item_id]
                        self.stdout.write(f"Processing answer for field {field.name} ({field.field_type})")
                        
                        # Extract value based on answer type
                        value = None
                        if 'textAnswers' in answer:
                            value = answer['textAnswers']['answers'][0]['value']
                        elif 'choiceAnswers' in answer:
                            value = answer['choiceAnswers']['answers'][0]['value']
                        
                        if value is None:
                            self.stdout.write(self.style.WARNING(f"Could not extract value for question {item_id}"))
                            continue
                            
                        # Create form response
                        FormResponse.objects.create(
                            submission=form_submission,
                            field=field,
                            value=value
                        )
                    else:
                        self.stdout.write(self.style.WARNING(f"No FormField mapping for question ID {item_id}"))

            self.stdout.write(self.style.SUCCESS(f"Successfully processed {len(responses.get('responses', []))} responses"))

        except HttpError as error:
            self.stdout.write(self.style.ERROR(f'An error occurred: {error}'))
            return None 