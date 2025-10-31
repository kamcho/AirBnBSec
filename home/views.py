import re
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.conf import settings
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.db import models, transaction
from django.db.models import Q, Count, F, ExpressionWrapper, fields, IntegerField, Avg
from django.db.models.functions import TruncMonth, TruncDay, ExtractWeekDay
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from users.models import Client, NameAlias
from core.utils import verify_kra_details

from .models import SecurityIncident, IncidentUpdate, IncidentEvidence, Comment, ExplainerVideo
from users.models import Client, ClientContact
from .forms import (
    SecurityIncidentForm, IncidentUpdateForm, SecurityIncidentSearchForm,
    SecurityIncidentStatusUpdateForm, IncidentStep1Form, IncidentStep2Form,
    IncidentStep3Form, IncidentStep4Form, IncidentEvidenceForm, CommentForm, ExplainerVideoForm
)

# Create your views here.
class LandingPageView(TemplateView):
    template_name = 'home/landing.html'

class PrivacyPolicyView(TemplateView):
    template_name = 'home/privacy_policy.html'

def verify_client(request, verification_token=None):
    """
    View to verify client's KRA details using ID number
    """
    import os
    from django.conf import settings
    
    # Load environment variables directly
    from dotenv import load_dotenv
    import os
    
    # Load .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(dotenv_path=env_path, override=True)
    
    # Get values directly from environment
    api_key = os.getenv('GAVACONNECT_API_KEY')
    api_secret = os.getenv('GAVACONNECT_API_SECRET')
    
    # Debug: Print environment variables to console
    print("\n=== Environment Variables (Direct from .env) ===")
    print(f"GAVACONNECT_API_KEY: {'*' * 10}{api_key[-4:] if api_key else 'Not found'}")
    print(f"GAVACONNECT_API_SECRET: {'*' * 10}{api_secret[-4:] if api_secret else 'Not found'}")
    print("===========================================\n")
    
    context = {
        'debug': settings.DEBUG,
        'debug_info': {
            'api_key_exists': bool(api_key),
            'api_secret_exists': bool(api_secret),
        }
    }
    
    # Handle form submission with ID number
    if request.method == 'POST' and 'id_number' in request.POST:
        id_number = request.POST.get('id_number', '').strip()
        user_type = request.POST.get('user_type', 'citizen').lower()
        
        # Validate ID based on user type without length restrictions
        is_valid = False
        if user_type == 'citizen':
            is_valid = id_number.isdigit()
            error_msg = 'Please enter a valid National ID number (digits only)'
        elif user_type == 'alien':
            is_valid = bool(re.match(r'^[0-9A-Za-z]+$', id_number))
            error_msg = 'Please enter a valid Alien ID (alphanumeric)'
        elif user_type == 'kra':
            is_valid = bool(re.match(r'^[A-Za-z]\d+[A-Za-z]?$', id_number, re.IGNORECASE))
            error_msg = 'Please enter a valid KRA PIN (must start with a letter)'
            
        if id_number and is_valid:
            # Import the KRA verification function
            from core.utils import verify_kra_details
            
            # Call the KRA verification function with the ID number
            kra_result = verify_kra_details(id_number)
            
            if kra_result['success']:
                context.update({
                    'verification_success': True,
                    'kra_data': kra_result.get('data', {}),
                    'id_number': id_number,
                    'verification_error': False
                })
                messages.success(request, 'KRA verification successful!')
            else:
                context.update({
                    'verification_error': True,
                    'error_message': kra_result.get('message', 'KRA verification failed. Please try again.'),
                    'id_number': id_number,
                    'verification_success': False
                })
                messages.error(request, kra_result.get('message', 'KRA verification failed. Please try again.'))
        else:
            error_msg = error_msg if 'error_msg' in locals() else 'Please enter a valid ID number'
            context.update({
                'verification_error': True,
                'error_message': error_msg,
                'verification_success': False,
                'id_number': id_number,
                'user_type': user_type
            })
            messages.error(request, error_msg)
    
    # Handle direct token verification (from email link) - keeping this for backward compatibility
    if verification_token:
        context.update({
            'verification_success': True,
            'verification_token': verification_token
        })
    
    return render(request, 'home/verify_client.html', context)


# Security Incident CRUD Views

class SecurityIncidentListView(ListView):
    """List all security incidents with search and filtering"""
    model = SecurityIncident
    template_name = 'home/incident_list.html'
    context_object_name = 'incidents'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SecurityIncident.objects.all()
        
        # Apply search and filters
        search_form = SecurityIncidentSearchForm(self.request.GET)
        if search_form.is_valid():
            search = search_form.cleaned_data.get('search')
            incident_type = search_form.cleaned_data.get('incident_type')
            severity = search_form.cleaned_data.get('severity')
            status = search_form.cleaned_data.get('status')
            date_from = search_form.cleaned_data.get('date_from')
            date_to = search_form.cleaned_data.get('date_to')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(incident_id__icontains=search) |
                    Q(client__first_name__icontains=search) |
                    Q(client__last_name__icontains=search) |
                    Q(client__id_number__icontains=search)
                )
            
            if incident_type:
                queryset = queryset.filter(incident_type=incident_type)
            
            if severity:
                queryset = queryset.filter(severity=severity)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if date_from:
                queryset = queryset.filter(incident_date__date__gte=date_from)
            
            if date_to:
                queryset = queryset.filter(incident_date__date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SecurityIncidentSearchForm(self.request.GET)
        return context


class AddOffenderView(LoginRequiredMixin, UpdateView):
    model = SecurityIncident
    template_name = 'home/add_offender.html'
    fields = []  # We'll handle the form manually
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        incident = self.get_object()
        context['incident'] = incident
        
        # Initialize form data with client info if it exists
        if incident.client:
            context['client'] = incident.client
            # Get email and phone from contacts
            email = incident.client.contacts.filter(contact_type='email').first()
            phone = incident.client.contacts.filter(contact_type='phone').first()
            address = incident.client.contacts.filter(contact_type='address').first()
            
            context['form_data'] = {
                'first_name': incident.client.first_name or '',
                'last_name': incident.client.last_name or '',
                'surname': incident.client.surname or '',
                'id_number': incident.client.id_number or '',
                'email': email.contact if email else '',
                'phone': phone.contact if phone else '',
                'address': address.contact if address else ''
            }
        else:
            context['form_data'] = {
                'first_name': '',
                'last_name': '',
                'surname': '',
                'id_number': '',
                'email': '',
                'phone': '',
                'address': ''
            }
            
        return context
    
    def form_valid(self, form):
        incident = self.get_object()
        
        # Check permissions
        if not (self.request.user.is_staff or self.request.user == incident.reported_by):
            return HttpResponseForbidden("You don't have permission to add offenders to this incident.")
        
        try:
            offender_type = self.request.POST.get('offender_type')
            
            if offender_type == 'citizen':
                # Handle Kenyan citizen
                first_name = self.request.POST.get('first_name', '').strip()
                last_name = self.request.POST.get('last_name', '').strip()
                id_number = self.request.POST.get('id_number', '').strip() or None
                email = self.request.POST.get('email', '').strip()
                phone = self.request.POST.get('phone', '').strip()
            else:
                # Handle foreign national
                first_name = self.request.POST.get('foreigner_first_name', '').strip()
                last_name = self.request.POST.get('foreigner_last_name', '').strip()
                id_number = self.request.POST.get('foreigner_id', '').strip() or None
                email = self.request.POST.get('foreigner_email', '').strip()
                phone = self.request.POST.get('foreigner_phone', '').strip()
                country_code = self.request.POST.get('country_code', '254')  # Default to Kenya
                
                # Format phone number with country code if not already included
                if phone and not phone.startswith('+'):
                    phone = f"+{country_code}{phone}"
            
            # Try to find existing client by ID number if provided
            client = None
            if id_number:
                client = Client.objects.filter(id_number=id_number).first()
            
            # If client not found by ID, try to find by name and phone/email
            if not client and first_name:
                # Try to find by name and phone or email
                client_query = Client.objects.filter(first_name__iexact=first_name)
                if last_name:
                    client_query = client_query.filter(last_name__iexact=last_name)
                
                # If we have contact info, try to match that as well
                if phone or email:
                    contact_query = Q()
                    if phone:
                        contact_query |= Q(contacts__contact_type='phone', contacts__contact__icontains=phone)
                    if email:
                        contact_query |= Q(contacts__contact_type='email', contacts__contact__iexact=email)
                    
                    client_query = client_query.filter(contact_query).distinct()
                
                client = client_query.first()
            
            # Create new client if not found
            if not client:
                client = Client.objects.create(
                    first_name=first_name,
                    last_name=last_name or None,  # Make last_name optional
                    id_number=id_number
                )
                
                # Add contact information if provided
                if email:
                    ClientContact.objects.create(
                        client=client,
                        contact_type='email',
                        contact=email
                    )
                
                if phone:
                    ClientContact.objects.create(
                        client=client,
                        contact_type='phone',
                        contact=phone
                    )
            
            # Update incident with the client
            incident.client = client
            incident.save()
            
            # Create an update about this change
            IncidentUpdate.objects.create(
                incident=incident,
                update_type='status_change',
                description=f'Client/offender {client.get_full_name()} added to the incident.'
            )
            
            messages.success(self.request, 'Client/offender added successfully.')
            return redirect('home:incident_detail', pk=incident.pk)
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())  # Log the full traceback for debugging
            messages.error(self.request, f'Error adding client/offender: {str(e)}')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('home:incident_detail', kwargs={'pk': self.object.pk})


class SecurityIncidentDetailView(DetailView):
    """View details of a specific security incident"""
    model = SecurityIncident
    template_name = 'home/incident_detail_new.html'
    context_object_name = 'incident'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Initialize the update form with a default update_type
        context['update_form'] = IncidentUpdateForm(initial={'update_type': 'comment'})
        context['status_form'] = SecurityIncidentStatusUpdateForm(instance=self.object)
        
        # Get comments ordered by creation date (newest first)
        context['comments'] = self.object.comments.all().order_by('-created_at')
        
        # Add video form and check if video exists
        context['video_form'] = ExplainerVideoForm()
        try:
            context['explainer_video'] = self.object.explainer_video
        except ExplainerVideo.DoesNotExist:
            context['explainer_video'] = None
        
        # Add any form errors to messages if this is a redirect from a failed form submission
        if 'update_form' in self.request.session:
            form_data = self.request.session.pop('update_form')
            context['update_form'] = IncidentUpdateForm(data=form_data)
        
        # Add evidence to context
        context['evidence'] = self.object.evidence.all().order_by('-uploaded_at')
            
        return context


class SecurityIncidentCreateView(CreateView):
    """Create a new security incident"""
    model = SecurityIncident
    form_class = SecurityIncidentForm
    template_name = 'home/incident_form.html'
    success_url = reverse_lazy('home:incident_list')
    
    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        messages.success(self.request, 'Security incident created successfully.')
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class SecurityIncidentUpdateView(UpdateView):
    """Update an existing security incident"""
    model = SecurityIncident
    form_class = SecurityIncidentForm
    template_name = 'home/incident_form.html'
    success_url = reverse_lazy('home:incident_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Security incident updated successfully.')
        return super().form_valid(form)


class SecurityIncidentDeleteView(DeleteView):
    """Delete a security incident"""
    model = SecurityIncident
    template_name = 'home/incident_confirm_delete.html'
    success_url = reverse_lazy('home:incident_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Security incident deleted successfully.')
        return super().delete(request, *args, **kwargs)


@login_required
def add_incident_update(request, pk):
    """Add an update to a security incident"""
    incident = get_object_or_404(SecurityIncident, pk=pk)
    
    if request.method == 'POST':
        form = IncidentUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.incident = incident
            update.save()
            messages.success(request, 'Update added successfully.')
            return redirect('home:incident_detail', pk=pk)
        else:
            # Store the form data in the session to repopulate the form after redirect
            request.session['update_form'] = request.POST
            # Add error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    
    # Redirect back to the incident detail page
    return redirect('home:incident_detail', pk=pk)


@login_required
def update_incident_status(request, pk):
    """Update the status of a security incident"""
    incident = get_object_or_404(SecurityIncident, pk=pk)
    
    if request.method == 'POST':
        form = SecurityIncidentStatusUpdateForm(request.POST, instance=incident)
        if form.is_valid():
            form.save()
            messages.success(request, 'Incident status updated successfully.')
            return redirect('home:incident_detail', pk=pk)
    else:
        form = SecurityIncidentStatusUpdateForm(instance=incident)
    
    return render(request, 'home/incident_detail.html', {
        'incident': incident,
        'update_form': IncidentUpdateForm(),
        'status_form': form
    })

@login_required
def incident_dashboard(request):
    """Dashboard view with incident statistics and visualizations"""
    incidents = SecurityIncident.objects.all()
    
    # Basic statistics
    total_incidents = incidents.count()
    open_incidents = incidents.filter(status__in=['reported', 'investigating']).count()
    resolved_incidents = incidents.filter(status__in=['resolved', 'closed']).count()
    
    # Calculate resolution rate (avoid division by zero)
    resolution_rate = 0
    if total_incidents > 0:
        resolution_rate = round((resolved_incidents / total_incidents) * 100, 1)
    
    # Calculate average resolution time
    resolved_incidents_with_duration = incidents.filter(
        status__in=['resolved', 'closed'],
        resolved_date__isnull=False
    ).annotate(
        duration=ExpressionWrapper(
            F('resolved_date') - F('reported_date'),
            output_field=fields.DurationField()
        )
    )
    
    avg_resolution_days = 0
    if resolved_incidents_with_duration.exists():
        avg_seconds = resolved_incidents_with_duration.aggregate(
            avg_duration=Avg('duration')
        )['avg_duration'].total_seconds()
        avg_resolution_days = round(avg_seconds / (24 * 3600), 1)
    
    # Incidents by type
    incidents_by_type = dict(incidents.values_list('incident_type').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # Incidents by severity
    incidents_by_severity = dict(incidents.values_list('severity').annotate(
        count=Count('id')
    ).order_by('severity'))
    
    # Monthly trend data (last 6 months)
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_trends = incidents.filter(
        reported_date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('reported_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    # Prepare data for charts
    months = [entry['month'].strftime('%b %Y') for entry in monthly_trends]
    monthly_counts = [entry['count'] for entry in monthly_trends]
    
    # Get status distribution
    status_distribution = dict(incidents.values_list('status').annotate(
        count=Count('id')
    ))
    
    # Recent incidents
    recent_incidents = incidents.order_by('-reported_date')[:5]
    
    # Incidents by day of week
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Initialize weekday counts with zeros
    weekday_data = [0] * 7
    
    # Get incident counts by day of week
    if incidents.exists():
        # Get counts for each day of the week (1=Sunday, 2=Monday, ..., 7=Saturday)
        weekday_counts = dict(incidents.annotate(
            day_of_week=ExtractWeekDay('reported_date')
        ).values('day_of_week').annotate(
            count=Count('id')
        ).values_list('day_of_week', 'count'))
        
        # Convert to our format (0=Monday, 1=Tuesday, ..., 6=Sunday)
        for day, count in weekday_counts.items():
            # Convert from 1=Sunday, 2=Monday, ... to 0=Monday, 6=Sunday
            adjusted_day = (day - 2) % 7
            weekday_data[adjusted_day] = count
    
    context = {
        'stats': {
            'total_incidents': total_incidents,
            'open_incidents': open_incidents,
            'resolved_incidents': resolved_incidents,
            'resolution_rate': resolution_rate,
            'avg_resolution_time': avg_resolution_days,
            'incidents_this_month': incidents.filter(
                reported_date__month=datetime.now().month,
                reported_date__year=datetime.now().year
            ).count(),
        },
        'chart_data': {
            'months': months,
            'monthly_counts': monthly_counts,
            'incident_types': list(incidents_by_type.keys()),
            'incident_type_counts': list(incidents_by_type.values()),
            'severity_levels': list(incidents_by_severity.keys()),
            'severity_counts': list(incidents_by_severity.values()),
            'status_distribution': status_distribution,
            'weekday_data': weekday_data,
            'weekday_labels': day_names,
        },
        'recent_incidents': recent_incidents,
    }
    
    return render(request, 'home/incident_dashboard.html', context)


# Multi-step incident creation views
class IncidentCreateStep1View(LoginRequiredMixin, View):
    """Step 1: Incident Information and Description"""
    template_name = 'home/incident_create_step1.html'
    login_url = '/accounts/login/'
    redirect_field_name = 'next'
    
    def get(self, request):
        form = IncidentStep1Form()
        return render(request, self.template_name, {'form': form, 'step': 1})
    
    def post(self, request):
        form = IncidentStep1Form(request.POST)
        if form.is_valid():
            # Store step 1 data in session
            request.session['incident_step1'] = form.cleaned_data
            return redirect('home:incident_create_step2')
        return render(request, self.template_name, {'form': form, 'step': 1})


class IncidentCreateStep2View(LoginRequiredMixin, View):
    """Step 2: Date and Time Information"""
    template_name = 'home/incident_create_step2.html'
    login_url = '/accounts/login/'
    redirect_field_name = 'next'
    
    def get(self, request):
        # Check if step 1 data exists
        if 'incident_step1' not in request.session:
            return redirect('home:incident_create_step1')
        
        form = IncidentStep2Form()
        return render(request, self.template_name, {
            'form': form, 
            'step': 2,
            'step1_data': request.session['incident_step1'],
            'incident_types': SecurityIncident.INCIDENT_TYPES,
            'severity_levels': SecurityIncident.SEVERITY_LEVELS
        })
    
    def post(self, request):
        form = IncidentStep2Form(request.POST)
        if form.is_valid():
            # Store step 2 data in session (convert datetime to string for JSON serialization)
            step2_data = form.cleaned_data.copy()
            step2_data['incident_date'] = step2_data['incident_date'].isoformat()
            request.session['incident_step2'] = step2_data
            return redirect('home:incident_create_step3')
        return render(request, self.template_name, {
            'form': form, 
            'step': 2,
            'step1_data': request.session.get('incident_step1', {})
        })


class IncidentCreateStep3View(LoginRequiredMixin, View):
    """Step 3: Additional Details and Final Submission"""
    template_name = 'home/incident_create_step3.html'
    login_url = '/accounts/login/'
    redirect_field_name = 'next'
    
    def get(self, request):
        # Check if previous steps data exists
        if 'incident_step1' not in request.session or 'incident_step2' not in request.session:
            return redirect('home:incident_create_step1')
        
        # Convert datetime string back to datetime object for template display
        step2_data = request.session['incident_step2'].copy()
        step2_data['incident_date'] = datetime.fromisoformat(step2_data['incident_date'])
        
        form = IncidentStep3Form()
        return render(request, self.template_name, {
            'form': form, 
            'step': 3,
            'step1_data': request.session['incident_step1'],
            'step2_data': step2_data,
            'incident_types': SecurityIncident.INCIDENT_TYPES,
            'severity_levels': SecurityIncident.SEVERITY_LEVELS
        })
    
    def post(self, request):
        form = IncidentStep3Form(request.POST)
        if form.is_valid():
            # Get all step data
            step1_data = request.session.get('incident_step1', {})
            step2_data = request.session.get('incident_step2', {})
            step3_data = form.cleaned_data.copy()
            
            # Convert datetime string back to datetime object
            incident_date = datetime.fromisoformat(step2_data['incident_date'])
            
            # Convert string back to Decimal for estimated_damage_cost if it exists
            estimated_damage_cost = None
            if step3_data.get('estimated_damage_cost'):
                estimated_damage_cost = step3_data['estimated_damage_cost']
            
            # Create the incident
            incident = SecurityIncident.objects.create(
                title=step1_data['title'],
                description=step1_data['description'],
                incident_type=step1_data['incident_type'],
                severity=step1_data['severity'],
                incident_date=incident_date,
                location_description=step3_data.get('location_description'),
                estimated_damage_cost=estimated_damage_cost,
                police_report_number=step3_data.get('police_report_number'),
                resolution_notes=step3_data.get('resolution_notes'),
                reported_by=request.user,
                status='reported'
            )
            
            # Clear session data
            request.session.pop('incident_step1', None)
            request.session.pop('incident_step2', None)
            
            messages.success(request, f'Security incident {incident.incident_id} created successfully. Please add the offender details.')
            return redirect('home:add_offender', pk=incident.pk)
            
        return render(request, self.template_name, {
            'form': form, 
            'step': 3,
            'step1_data': request.session.get('incident_step1', {}),
            'step2_data': request.session.get('incident_step2', {})
        })


class VerifyClientView(LoginRequiredMixin, View):
    """Handle client verification against local database"""
    
    def post(self, request):
        # Only allow AJAX requests
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'This endpoint only accepts AJAX requests',
                'error': 'invalid_request'
            }, status=400, content_type='application/json')
            
        id_number = request.POST.get('id_number')
        
        if not id_number:
            return JsonResponse({
                'success': False,
                'message': 'ID number is required',
                'error': 'missing_id_number'
            }, status=400, content_type='application/json')
        
        try:
            # Check if client exists in our database
            try:
                client = Client.objects.get(id_number=id_number)
                # Get client's contacts (phone and email)
                contacts = {}
                for contact in client.contacts.all():
                    if contact.contact_type in ['phone', 'email']:
                        contacts[contact.contact_type] = contact.contact
                
                return JsonResponse({
                    'success': True,
                    'exists': True,
                    'first_name': client.first_name or '',
                    'last_name': client.last_name or '',
                    'surname': client.surname or '',
                    'phone': contacts.get('phone', ''),
                    'email': contacts.get('email', ''),
                    'message': 'Client found in database'
                }, content_type='application/json')
                
            except Client.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'exists': False,
                    'message': 'Client not found in our database',
                    'error': 'client_not_found'
                }, status=404, content_type='application/json')
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'Error processing your request. Please try again.',
                'error': 'server_error',
                'debug': str(e) if settings.DEBUG else None
                }, status=500)


class AddClientToIncidentView(View):
    template_name = 'home/add_client_to_incident.html'
    
    def get(self, request, incident_id):
        incident = get_object_or_404(SecurityIncident, pk=incident_id)
        return render(request, self.template_name, {
            'incident': incident,
            'result': None,
        })
    
    def post(self, request, incident_id):
        incident = get_object_or_404(SecurityIncident, pk=incident_id)
        id_number = request.POST.get('id_number', '').strip()
        user_type = request.POST.get('user_type', '').strip()
        action = request.POST.get('action')
        result = {
            'found': False,
            'message': 'Offender not found in our database.',
        }
        client = None
        contacts = {}
        if id_number:
            try:
                client = Client.objects.get(id_number=id_number)
                # Handle confirm/alias actions when client exists
                if action == 'confirm_yes':
                    incident.client = client
                    incident.save()
                    messages.success(request, f'Client {client.get_full_name()} linked to incident.')
                    return redirect('home:incident_detail', pk=incident.pk)
                if action == 'confirm_no':
                    # Show alias form
                    for contact in client.contacts.all():
                        if contact.contact_type in ['phone', 'email']:
                            contacts[contact.contact_type] = contact.contact
                    result = {
                        'found': True,
                        'name': client.get_full_name(),
                        'phone': contacts.get('phone', ''),
                        'email': contacts.get('email', ''),
                        'id_number': client.id_number,
                    }
                    return render(request, self.template_name, {
                        'incident': incident,
                        'result': result,
                        'id_number': id_number,
                        'user_type': user_type,
                        'alias_mode': True,
                    })
                if action == 'alias_submit':
                    alias_first = request.POST.get('alias_first_name', '').strip()
                    alias_last = request.POST.get('alias_last_name', '').strip()
                    alias_phone = request.POST.get('alias_phone', '').strip()
                    alias_email = request.POST.get('alias_email', '').strip()
                    if not alias_first:
                        messages.error(request, 'Alias first name is required.')
                        return render(request, self.template_name, {
                            'incident': incident,
                            'result': {
                                'found': True,
                                'name': client.get_full_name(),
                                'phone': contacts.get('phone', ''),
                                'email': contacts.get('email', ''),
                                'id_number': client.id_number,
                            },
                            'id_number': id_number,
                            'user_type': user_type,
                            'alias_mode': True,
                        })
                    
                    NameAlias.objects.create(client=client, first_name=alias_first, last_name=alias_last or None)
                    # Save provided contact details to ClientContact
                    if alias_phone:
                        ClientContact.objects.update_or_create(
                            client=client,
                            contact_type='phone',
                            contact=alias_phone,
                            defaults={'contact': alias_phone}
                        )
                    if alias_email:
                        ClientContact.objects.update_or_create(
                            client=client,
                            contact_type='email',
                            contact=alias_email,
                            defaults={'contact': alias_email}
                        )
                    # Link client after alias capture
                    incident.client = client
                    incident.save()
                    messages.success(request, 'Alias saved and client linked to incident.')
                    return redirect('home:incident_detail', pk=incident.pk)
                    messages.success(request, 'Alias saved and client linked to incident.')
                    return redirect('home:incident_detail', pk=incident.pk)

                # Default: just show found result (no action yet)
                for contact in client.contacts.all():
                    if contact.contact_type in ['phone', 'email']:
                        contacts[contact.contact_type] = contact.contact
                result = {
                    'found': True,
                    'name': client.get_full_name(),
                    'phone': contacts.get('phone', ''),
                    'email': contacts.get('email', ''),
                    'id_number': client.id_number,
                }
            except Client.DoesNotExist:
                # Handle flows when client not in DB
                # 1) Actions coming from KRA flows
                if action == 'kra_confirm_yes':
                    kra_first = request.POST.get('kra_first_name', '').strip()
                    kra_last = request.POST.get('kra_last_name', '').strip()
                    kra_surname = request.POST.get('kra_surname', '').strip()
                    # Create new client with KRA-provided names
                    client = Client.objects.create(
                        id_number=id_number,
                        first_name=kra_first,
                        last_name=kra_last,
                        surname=kra_surname or None,
                    )
                    incident.client = client
                    incident.save()
                    messages.success(request, f'Client {client.get_full_name()} created from KRA data and linked to incident.')
                    return redirect('home:incident_detail', pk=incident.pk)
                
                if action == 'kra_confirm_no':
                    # Show manual entry form
                    return render(request, self.template_name, {
                        'incident': incident,
                        'result': result,
                        'id_number': id_number,
                        'user_type': user_type,
                        'manual_mode': True,
                    })
                
                if action == 'manual_submit':
                    manual_first = request.POST.get('manual_first_name', '').strip()
                    manual_last = request.POST.get('manual_last_name', '').strip()
                    manual_surname = request.POST.get('manual_surname', '').strip()
                    manual_phone = request.POST.get('manual_phone', '').strip()
                    manual_email = request.POST.get('manual_email', '').strip()
                    
                    if not manual_first and not manual_last:
                        messages.error(request, 'Please provide at least a first or last name.')
                        return render(request, self.template_name, {
                            'incident': incident,
                            'result': result,
                            'id_number': id_number,
                            'user_type': user_type,
                            'manual_mode': True,
                        })
                    
                    # Create the client
                    client = Client.objects.create(
                        id_number=id_number,
                        first_name=manual_first or None,
                        last_name=manual_last or None,
                        surname=manual_surname or None,
                    )
                    
                    # Add phone contact if provided
                    if manual_phone:
                        ClientContact.objects.update_or_create(
                            client=client,
                            contact_type='phone',
                            contact=manual_phone,
                            defaults={'contact': manual_phone}
                        )
                    
                    # Add email contact if provided
                    if manual_email:
                        ClientContact.objects.update_or_create(
                            client=client,
                            contact_type='email',
                            contact=manual_email,
                            defaults={'contact': manual_email}
                        )
                    # Link client to incident and show success message
                    incident.client = client
                    incident.save()
                    messages.success(request, f'Client {client.get_full_name()} created and linked to incident.')
                    return redirect('home:incident_detail', pk=incident.pk)
            
            # 2) Initial attempt: verify via KRA for citizen type
            if user_type == 'citizen':
                try:
                    kra = verify_kra_details(id_number)
                except Exception:
                    kra = {'success': False}
                
                if kra.get('success'):
                    kra_data = kra.get('data', {})
                    # Parse TaxpayerName into components if present
                    full_name = kra_data.get('name') or kra_data.get('TaxpayerName') or ''
                    parts = [p for p in full_name.strip().split() if p]
                    
                    if not parts:
                        # No valid name returned; show manual entry with a clear message
                        return render(request, self.template_name, {
                            'incident': incident,
                            'result': {
                                'found': False,
                                'message': 'There is no person with such an ID number in Kenya. Please enter the offender\'s details.'
                            },
                            'id_number': id_number,
                            'user_type': user_type,
                            'manual_mode': True,
                            'manual_message': 'There is no person with such an ID number in Kenya. Please enter the offender\'s details.'
                        })
                        kra_first = parts[0] if len(parts) >= 1 else ''
                        kra_last = parts[1] if len(parts) >= 2 else ''
                        kra_surname = " ".join(parts[2:]) if len(parts) >= 3 else ''
                        return render(request, self.template_name, {
                            'incident': incident,
                            'result': {
                                'found': False,
                                'kra': True,
                                'kra_first_name': kra_first,
                                'kra_last_name': kra_last,
                                'kra_surname': kra_surname,
                                'id_number': id_number,
                                'message': 'Verified via KRA. Are these the correct details?'
                            },
                            'id_number': id_number,
                            'user_type': user_type,
                            'kra_mode': True,
                        })
                # 3) KRA not found or not citizen: request manual entry
                return render(request, self.template_name, {
                    'incident': incident,
                    'result': result,
                    'id_number': id_number,
                    'user_type': user_type,
                    'manual_mode': True,
                })
        return render(request, self.template_name, {
            'incident': incident,
            'result': result,
            'id_number': id_number,
            'user_type': user_type,
        })


class AddClientAliasView(LoginRequiredMixin, View):
    template_name = 'home/add_client_alias.html'
    login_url = '/accounts/login/'

    def get(self, request, incident_id):
        incident = get_object_or_404(SecurityIncident, pk=incident_id)
        id_number = request.GET.get('id_number', '').strip()
        api_name = request.GET.get('api_name', '').strip()

        # Parse API name into first/last (simple split)
        api_first = ''
        api_last = ''
        if api_name:
            parts = [p for p in api_name.split(' ') if p]
            if parts:
                api_first = ' '.join(parts[:-1]) if len(parts) > 1 else parts[0]
                api_last = parts[-1] if len(parts) > 1 else ''

        return render(request, self.template_name, {
            'incident': incident,
            'id_number': id_number,
            'api_first_name': api_first,
            'api_last_name': api_last,
            'api_full_name': api_name,
        })

    def post(self, request, incident_id):
        incident = get_object_or_404(SecurityIncident, pk=incident_id)

        # Hidden fields carrying API names
        api_first = request.POST.get('api_first_name', '').strip()
        api_last = request.POST.get('api_last_name', '').strip()
        id_number = request.POST.get('id_number', '').strip() or None

        # Alias fields from user
        alias_first = request.POST.get('alias_first_name', '').strip()
        alias_last = request.POST.get('alias_last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()

        if not alias_first:
            messages.error(request, 'First name is required for alias.')
            return render(request, self.template_name, {
                'incident': incident,
                'id_number': id_number or '',
                'api_first_name': api_first,
                'api_last_name': api_last,
                'api_full_name': (api_first + ' ' + api_last).strip(),
            })

        if not phone:
            messages.error(request, 'Phone number is required.')
            return render(request, self.template_name, {
                'incident': incident,
                'id_number': id_number or '',
                'api_first_name': api_first,
                'api_last_name': api_last,
                'api_full_name': (api_first + ' ' + api_last).strip(),
            })

        # Create or reuse a client based on ID number if provided
        client = None
        if id_number:
            client = Client.objects.filter(id_number=id_number).first()

        if not client:
            client = Client.objects.create(
                id_number=id_number,
                first_name=api_first or None,
                last_name=api_last or None,
            )

        # Save alias from user input
        NameAlias.objects.create(
            client=client,
            first_name=alias_first,
            last_name=alias_last or None,
        )

        # Save contacts
        if phone:
            ClientContact.objects.update_or_create(
                client=client,
                contact_type='phone',
                contact=phone,
                defaults={'contact': phone}
            )
        if email:
            ClientContact.objects.update_or_create(
                client=client,
                contact_type='email',
                contact=email,
                defaults={'contact': email}
            )

        # Link client to incident
        incident.client = client
        incident.save()

        messages.success(request, 'Client created from API names and alias saved. Linked to incident.')
        return redirect('home:incident_detail', pk=incident.pk)

class AddEvidenceView(View):
    """View for adding evidence to an incident"""
    template_name = 'home/add_evidence.html'
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request, incident_id):
        incident = get_object_or_404(SecurityIncident, pk=incident_id)
        form = IncidentEvidenceForm()
        
        # Get existing evidence for this incident
        evidence_list = incident.evidence.all().order_by('-uploaded_at')
        
        return render(request, self.template_name, {
            'incident': incident,
            'form': form,
            'evidence_list': evidence_list
        })
        
    def post(self, request, incident_id):
        incident = get_object_or_404(SecurityIncident, pk=incident_id)
        form = IncidentEvidenceForm(request.POST, request.FILES)
        
        if form.is_valid():
            evidence = form.save(commit=False)
            evidence.incident = incident
            evidence.uploaded_by = request.user
            
            # Determine file type
            file = request.FILES.get('file')
            if file:
                content_type = file.content_type
                if content_type.startswith('image/'):
                    evidence.file_type = 'image'
                elif content_type.startswith('video/'):
                    evidence.file_type = 'video'
                elif content_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                    evidence.file_type = 'document'
                else:
                    evidence.file_type = 'other'
            
            evidence.save()
            
            # Create an update about this change
            IncidentUpdate.objects.create(
                incident=incident,
                update_type='evidence_added',
                description=f'New evidence added: {evidence.description or "No description"}'
            )
            
            messages.success(request, 'Evidence added successfully.')
            return redirect('home:add_evidence', incident_id=incident.id)
            
        # If form is not valid, show errors
        evidence_list = incident.evidence.all().order_by('-uploaded_at')
        return render(request, self.template_name, {
            'incident': incident,
            'form': form,
            'evidence_list': evidence_list
        })


@login_required
def add_client_contact(request, incident_id):
    """Add a contact (phone/email) to the incident's client."""
    incident = get_object_or_404(SecurityIncident, pk=incident_id)
    if request.user != incident.reported_by and not request.user.is_superuser:
        return HttpResponseForbidden("You don't have permission to add contacts for this incident.")
    if not incident.client:
        messages.error(request, 'No client linked to this incident to add contact for.')
        return redirect('home:incident_detail', pk=incident_id)
    if request.method == 'POST':
        contact_type = request.POST.get('contact_type')
        contact_value = request.POST.get('contact')
        if contact_type not in ['phone', 'email'] or not contact_value:
            messages.error(request, 'Please provide a valid contact type and value.')
            return redirect('home:incident_detail', pk=incident_id)
        ClientContact.objects.update_or_create(
            client=incident.client,
            contact_type=contact_type,
            contact=contact_value,
            defaults={'contact': contact_value}
        )
        messages.success(request, 'Contact added successfully.')
    return redirect('home:incident_detail', pk=incident_id)
    
    def post(self, request, incident_id):
        incident = get_object_or_404(SecurityIncident, pk=incident_id)
        form = IncidentEvidenceForm(request.POST, request.FILES, incident=incident, user=request.user)
        
        if form.is_valid():
            try:
                # Save will handle all files in the form
                evidence = form.save(commit=True)
                
                if evidence:
                    # Create an update about the new evidence
                    files = request.FILES.getlist('file')
                    file_names = ", ".join([f.name for f in files])
                    
                    IncidentUpdate.objects.create(
                        incident=incident,
                        update_type='evidence_added',
                        description=f'New evidence added: {file_names}'
                    )
                    
                    messages.success(request, f'Successfully uploaded {len(files)} file(s).')
                    return redirect('home:add_evidence', incident_id=incident.id)
                else:
                    messages.error(request, 'Failed to save evidence. Please try again.')
                
            except Exception as e:
                # Log the full error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error uploading files: {str(e)}", exc_info=True)
                
                messages.error(request, f'Error uploading files: {str(e)}')
        else:
            # Display form errors
            for field, errors in form.errors.items():
                field_name = field.replace('_', ' ').title()
                for error in errors:
                    messages.error(request, f"{field_name}: {error}")
        
        # Get existing evidence for this incident
        evidence_list = incident.evidence.all().order_by('-uploaded_at')
        
        return render(request, self.template_name, {
            'incident': incident,
            'form': form,
            'evidence_list': evidence_list
        })


def delete_evidence(request, evidence_id):
    """
    View to delete evidence
    """
    evidence = get_object_or_404(IncidentEvidence, id=evidence_id)
    incident_id = evidence.incident.id
    
    # Check if user has permission to delete (only the uploader or superuser)
    if request.user != evidence.uploaded_by and not request.user.is_superuser:
        messages.error(request, "You don't have permission to delete this evidence.")
        return redirect('home:incident_detail', pk=incident_id)
    
    # Delete the evidence file and record
    evidence.delete()
    
    messages.success(request, 'Evidence has been deleted successfully.')
    return redirect('home:incident_detail', pk=incident_id)


@login_required
def add_comment(request, incident_id):
    """
    View to add a new comment to an incident
    """
    incident = get_object_or_404(SecurityIncident, id=incident_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user, incident=incident)
        if form.is_valid():
            comment = form.save()
            messages.success(request, 'Your comment has been added successfully.')
            
            # If this is an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment_id': comment.id,
                    'user_name': comment.user.get_full_name() or comment.user.username,
                    'user_avatar': comment.user_avatar_url(),
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%B %d, %Y %I:%M %p'),
                    'can_delete': True  # User can delete their own comments
                })
            return redirect('home:incident_detail', pk=incident_id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = CommentForm()
    
    return redirect('home:incident_detail', pk=incident_id)


@login_required
def delete_comment(request, comment_id):
    """
    View to delete a comment
    """
    comment = get_object_or_404(Comment, id=comment_id)
    incident_id = comment.incident.id
    
    # Check if user has permission to delete (only comment owner, incident reporter, or superuser)
    if (request.user != comment.user and 
        request.user != comment.incident.reported_by and 
        not request.user.is_superuser):
        messages.error(request, "You don't have permission to delete this comment.")
        return redirect('home:incident_detail', pk=incident_id)
    
    # Delete the comment
    comment.delete()
    
    messages.success(request, 'Comment has been deleted successfully.')
    return redirect('home:incident_detail', pk=incident_id)


@login_required
def upload_explainer_video(request, incident_id):
    """
    View to handle video upload for an incident
    """
    incident = get_object_or_404(SecurityIncident, id=incident_id)
    
    # Check if video already exists for this incident
    video_exists = ExplainerVideo.objects.filter(incident=incident).exists()
    
    if request.method == 'POST':
        if video_exists:
            # Update existing video
            video = ExplainerVideo.objects.get(incident=incident)
            form = ExplainerVideoForm(
                request.POST, 
                request.FILES, 
                instance=video,
                user=request.user,
                incident=incident
            )
            action = 'updated'
        else:
            # Create new video
            form = ExplainerVideoForm(
                request.POST, 
                request.FILES,
                user=request.user,
                incident=incident
            )
            action = 'uploaded'
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Video {action} successfully.')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Video {action} successfully.',
                    'video_title': form.instance.title,
                    'video_description': form.instance.description or '',
                    'video_url': form.instance.video.url,
                    'uploaded_at': form.instance.created_at.strftime('%B %d, %Y %I:%M %p'),
                    'uploaded_by': form.instance.uploaded_by.get_full_name() or form.instance.uploaded_by.username
                })
            return redirect('home:incident_detail', pk=incident_id)
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
    else:
        form = ExplainerVideoForm()
    
    return redirect('home:incident_detail', pk=incident_id)


@login_required
def delete_explainer_video(request, video_id):
    """
    View to delete an explainer video
    """
    video = get_object_or_404(ExplainerVideo, id=video_id)
    incident_id = video.incident.id
    
    # Check permissions (only incident reporter, video uploader, or superuser can delete)
    if (request.user != video.uploaded_by and 
        request.user != video.incident.reported_by and 
        not request.user.is_superuser):
        messages.error(request, "You don't have permission to delete this video.")
        return redirect('home:incident_detail', pk=incident_id)
    
    # Delete the video file and record
    video.video.delete()  # This deletes the file from storage
    video.delete()
    
    messages.success(request, 'Video has been deleted successfully.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Video deleted successfully.'
        })
        
    return redirect('home:incident_detail', pk=incident_id)
# home/views.py
from django.http import HttpResponse

def test_view(request):
    return HttpResponse("Hello World")
