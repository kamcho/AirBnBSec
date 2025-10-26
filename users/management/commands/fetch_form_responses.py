from django.core.management.base import BaseCommand
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from partners.models import Job, JobApplication, JobFormField
from django.utils import timezone
import json
import os
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Fetches responses from Google Forms for a specific job application'

    def add_arguments(self, parser):
        parser.add_argument('--job-id', type=str, required=True, help='Job ID to fetch responses for')

    def handle(self, *args, **kwargs):
        try:
            # Load credentials from service account file
            SCOPES = [
                'https://www.googleapis.com/auth/forms.responses.readonly',
                'https://www.googleapis.com/auth/drive.file'
            ]
            SERVICE_ACCOUNT_FILE = 'D:/Public001/stage-425316-253108ec4214.json'

            # Create credentials
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE,
                scopes=SCOPES
            )

            # Build the Forms API service
            forms_service = build('forms', 'v1', credentials=credentials)

            # Get the specific job
            job_id = kwargs.get('job_id')
            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Job with ID {job_id} does not exist'))
                self.stdout.write('0')  # Write count to stdout
                return

            if not job.google_form_id:
                self.stdout.write(self.style.ERROR(f'Job {job.title} has no associated Google Form'))
                self.stdout.write('0')  # Write count to stdout
                return

            self.stdout.write(f"Processing responses for job: {job.title}")
            
            try:
                # Get form responses
                responses = forms_service.forms().responses().list(
                    formId=job.google_form_id
                ).execute()

                new_responses_count = 0
                # Process each response
                for response in responses.get('responses', []):
                    # Check if this response has already been processed
                    response_id = response['responseId']
                    if JobApplication.objects.filter(response_id=response_id).exists():
                        continue

                    # Get form fields for this job to map question IDs
                    form_fields = job.form_fields.all()
                    # Create a mapping of Google Form question IDs to our JobFormField objects
                    question_id_map = {}
                    id_number_field = None
                    for field in form_fields:
                        if field.google_question_id:  # Only map fields that have a google_question_id
                            question_id_map[field.google_question_id] = field
                            if field.is_id_number:
                                id_number_field = field

                    if not id_number_field:
                        self.stdout.write(self.style.ERROR(f"No ID number field found for job {job.title}"))
                        continue

                    # Extract answers with question IDs as keys
                    answers = {}
                    for question_id, answer in response.get('answers', {}).items():
                        # Extract value based on answer type
                        if 'textAnswers' in answer:
                            if len(answer['textAnswers']['answers']) > 1:
                                # Handle multiple answers (like checkboxes)
                                value = [ans.get('value', '') for ans in answer['textAnswers']['answers']]
                            else:
                                # Handle single answer
                                value = answer['textAnswers']['answers'][0].get('value', '')
                        elif 'fileUploadAnswers' in answer:
                            file_answers = answer['fileUploadAnswers']['answers']
                            if file_answers:
                                value = file_answers[0].get('fileId', '')
                            else:
                                value = ''
                        else:
                            value = ''

                        # Use the google_question_id as the key in our answers dictionary
                        if question_id in question_id_map:
                            field = question_id_map[question_id]
                            answers[field.google_question_id] = value
                        else:
                            self.stdout.write(self.style.WARNING(f"Question ID {question_id} not found in form fields"))
                            answers[question_id] = value

                    # Get the ID number from the field marked as is_id_number
                    id_number = answers.get(id_number_field.google_question_id, '')
                    if not id_number:
                        self.stdout.write(self.style.WARNING(f"No ID number found in response {response_id}"))
                        continue

                    # Create job application
                    JobApplication.objects.create(
                        job=job,
                        id_number=id_number,
                        response_id=response_id,
                        submitted_by='GOOGLE_FORMS',
                        status='SUBMITTED',
                        data=answers
                    )

                    new_responses_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created application {id_number} for response {response_id}"))

                self.stdout.write(self.style.SUCCESS(f'Successfully processed {new_responses_count} new responses for job {job.title}'))
                self.stdout.write(str(new_responses_count))  # Write count to stdout
                return

            except HttpError as error:
                self.stdout.write(self.style.ERROR(f"Error processing form responses: {error}"))
                self.stdout.write('0')  # Write count to stdout
                return

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}')) 
            self.stdout.write('0')  # Write count to stdout
            return 