from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden, JsonResponse
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator
from .models import SecurityIncident, IncidentUpdate
from .forms import SecurityIncidentForm, IncidentUpdateForm, SecurityIncidentSearchForm, SecurityIncidentStatusUpdateForm

# Create your views here.
class LandingPageView(TemplateView):
    template_name = 'home/landing.html'
def verify_client(request, verification_token=None):
    """
    View to verify client's account using a verification code
    """
    context = {}
    
    # Handle form submission with verification code
    if request.method == 'POST' and 'verification_code' in request.POST:
        verification_code = request.POST.get('verification_code')
        
        # Here you would typically verify the code against your database
        # For example:
        # if is_valid_verification_code(verification_code):
        #     user = get_user_from_verification_code(verification_code)
        #     user.is_verified = True
        #     user.save()
        #     context['verification_success'] = True
        #     return render(request, 'home/verify_client.html', context)
        # else:
        #     messages.error(request, 'Invalid verification code. Please try again.')
        
        # For now, we'll just show a success message if the code is 6 digits
        if verification_code and len(verification_code) == 6 and verification_code.isdigit():
            context.update({
                'verification_success': True,
                'verification_token': verification_code  # In a real app, this would be a token from your verification system
            })
            return render(request, 'home/verify_client.html', context)
        else:
            messages.error(request, 'Please enter a valid 6-digit verification code.')
    
    # Handle direct token verification (from email link)
    if verification_token:
        # Here you would verify the token against your database
        # For now, we'll just show a success message
        context.update({
            'verification_success': True,
            'verification_token': verification_token
        })
        return render(request, 'home/verify_client.html', context)
    
    # Show the verification code input form
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
                    Q(guest_name__icontains=search)
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


class SecurityIncidentDetailView(DetailView):
    """View details of a specific security incident"""
    model = SecurityIncident
    template_name = 'home/incident_detail.html'
    context_object_name = 'incident'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update_form'] = IncidentUpdateForm()
        context['status_form'] = SecurityIncidentStatusUpdateForm(instance=self.object)
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
        form = IncidentUpdateForm()
    
    return render(request, 'home/incident_detail.html', {
        'incident': incident,
        'update_form': form,
        'status_form': SecurityIncidentStatusUpdateForm(instance=incident)
    })


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
    """Dashboard view with incident statistics"""
    incidents = SecurityIncident.objects.all()
    
    # Statistics
    total_incidents = incidents.count()
    open_incidents = incidents.filter(status__in=['reported', 'investigating']).count()
    resolved_incidents = incidents.filter(status__in=['resolved', 'closed']).count()
    
    # Incidents by type
    incidents_by_type = {}
    for incident_type, _ in SecurityIncident.INCIDENT_TYPES:
        count = incidents.filter(incident_type=incident_type).count()
        if count > 0:
            incidents_by_type[incident_type] = count
    
    # Incidents by severity
    incidents_by_severity = {}
    for severity, _ in SecurityIncident.SEVERITY_LEVELS:
        count = incidents.filter(severity=severity).count()
        if count > 0:
            incidents_by_severity[severity] = count
    
    # Recent incidents
    recent_incidents = incidents[:5]
    
    context = {
        'total_incidents': total_incidents,
        'open_incidents': open_incidents,
        'resolved_incidents': resolved_incidents,
        'incidents_by_type': incidents_by_type,
        'incidents_by_severity': incidents_by_severity,
        'recent_incidents': recent_incidents,
    }
    
    return render(request, 'home/incident_dashboard.html', context)
