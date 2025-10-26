from django.core.management.base import BaseCommand
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from partners.models import Job, JobFormField
import json
import os
from datetime import datetime, timedelta

# Constant for the ID number question in Google Form

def create_google_form(job_id, email=None):
    """
    Creates a Google Form for a job based on its form fields.
    Returns the form URL if successful, None otherwise.
    """
    try:
        # Load credentials from service account file
        SCOPES = [
            'https://www.googleapis.com/auth/forms.body',
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
        drive_service = build('drive', 'v3', credentials=credentials)

        # Get the job
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            print(f'Job with ID {job_id} does not exist')
            return None

        # Create the form with just the title
        form = {
            'info': {
                'title': f'{job.title} - Application Form'
            }
        }

        # Create the form
        form = forms_service.forms().create(body=form).execute()
        form_id = form['formId']

        # Store the form ID in the job
        job.google_form_id = form_id
        job.save()

        # Define form items based on job fields
        items = []

        # Get all active form fields for the job
        job_fields = JobFormField.objects.filter(
            job=job,
            is_active=True
        ).order_by('order')

        # Add other form fields
        for job_field in job_fields:
            # Create base question item
            question_item = {
                'title': job_field.label,
                'questionItem': {
                    'question': {
                        'required': job_field.required,
                    }
                }
            }

            # Add field type specific configuration
            if job_field.field_type == 'text':
                question_item['questionItem']['question']['textQuestion'] = {
                    'paragraph': False
                }
            elif job_field.field_type == 'textarea':
                question_item['questionItem']['question']['textQuestion'] = {
                    'paragraph': True
                }
            elif job_field.field_type == 'number':
                question_item['questionItem']['question']['textQuestion'] = {
                    'paragraph': False
                }
            elif job_field.field_type in ['select', 'radio', 'checkbox']:
                # Get options from job field
                options = job_field.options or []
                if not options:
                    # Skip fields with no options
                    continue
                # Parse options if they're stored as a JSON string
                if isinstance(options, str):
                    try:
                        options = json.loads(options)
                    except json.JSONDecodeError:
                        options = []
                # Ensure options is a list
                if not isinstance(options, list):
                    options = [options]
                # Deduplicate options while preserving order
                unique_options = []
                seen = set()
                for option in options:
                    option = str(option).strip()
                    if option and option not in seen:
                        seen.add(option)
                        unique_options.append(option)
                question_item['questionItem']['question']['choiceQuestion'] = {
                    'type': 'DROP_DOWN' if job_field.field_type == 'select' else 'RADIO' if job_field.field_type == 'radio' else 'CHECKBOX',
                    'options': [{'value': option} for option in unique_options],
                    'shuffle': False
                }
            elif job_field.field_type == 'date':
                question_item['questionItem']['question']['dateQuestion'] = {
                    'includeTime': False,
                    'includeYear': True
                }
            elif job_field.field_type == 'email':
                question_item['questionItem']['question']['textQuestion'] = {
                    'paragraph': False
                }
            elif job_field.field_type == 'phone':
                question_item['questionItem']['question']['textQuestion'] = {
                    'paragraph': False
                }
            elif job_field.field_type == 'url':
                question_item['questionItem']['question']['textQuestion'] = {
                    'paragraph': False
                }
            elif job_field.field_type == 'file':
                question_item['questionItem']['question']['fileUploadQuestion'] = {
                    'maxFileSize': '10MB',
                    'maxFiles': 1
                }

            items.append(question_item)

        # Prepare batch update request
        requests = [
            # Update form description
            {
                'updateFormInfo': {
                    'info': {
                        'description': job.description
                    },
                    'updateMask': 'description'
                }
            },
            # Make form publicly accessible for responses
            {
                'updateSettings': {
                    'settings': {
                        'quizSettings': {
                            'isQuiz': False
                        }
                    },
                    'updateMask': 'quizSettings'
                }
            }
        ]

        # Add create item requests
        for i, item in enumerate(items):
            requests.append({
                'createItem': {
                    'item': item,
                    'location': {
                        'index': i
                    }
                }
            })

        # Execute batch update
        batch_update_request = {
            'requests': requests
        }
        
        response = forms_service.forms().batchUpdate(
            formId=form_id,
            body=batch_update_request
        ).execute()

        # Get the updated form to get the items with their titles and question IDs
        updated_form = forms_service.forms().get(formId=form_id).execute()
        
        # Create a mapping of item titles to their question IDs
        title_to_question_id = {}
        for item in updated_form.get('items', []):
            if 'questionItem' in item:
                question_id = item['questionItem']['question'].get('questionId')
                if question_id:
                    title_to_question_id[item['title']] = question_id

        # Update google_question_id for each field
        for job_field in job_fields:
            question_id = title_to_question_id.get(job_field.label)
            if question_id:
                job_field.google_question_id = question_id
                job_field.save()
                print(f"Updated google_question_id for field {job_field.label} to {question_id}")
            else:
                print(f"Could not find question ID for field {job_field.label}")

        # Share the form with the specified email
        if email:
            # Add writer permissions for the specified email
            permission = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': email
            }
            drive_service.permissions().create(
                fileId=form_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
            print(f'Form shared with {email} with writer permissions')

        # Get the form URL
        form_url = f"https://docs.google.com/forms/d/{form_id}/viewform"
        
        print(f'Successfully created Google Form: {form_url}')
        return form_url

    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

class Command(BaseCommand):
    help = 'Creates a Google Form for a job based on its form fields'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address to share the form with')
        parser.add_argument('--job-id', type=str, help='Job ID to create form for')

    def handle(self, *args, **kwargs):
        job_id = kwargs.get('job_id')
        email = kwargs.get('email')
        
        if not job_id:
            self.stdout.write(self.style.ERROR('Job ID is required'))
            return

        form_url = create_google_form(job_id, email)
        
        if form_url:
            self.stdout.write(self.style.SUCCESS(f'Successfully created Google Form: {form_url}'))
        else:
            self.stdout.write(self.style.ERROR('Failed to create Google Form')) 