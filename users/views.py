from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, UpdateView, ListView, DetailView, FormView
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse_lazy
from .models import MyUser, PersonalProfile, Notification
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
import random
import string
from datetime import datetime, timedelta
import json
from django import forms
from django.utils import timezone
from django.db import models
from django.core.paginator import Paginator
from django.views import View
import os
from django.core.files.base import File
from django.conf import settings
from .forms import UserRegistrationForm, CombinedUserProfileForm
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Create your views here.

class UserRegistrationView(FormView):
    template_name = 'users/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('profile_complete')

    def form_valid(self, form):
        # Create the user account
        user = form.save(commit=False)
        user.username = form.cleaned_data['email']  # Use email as username
        user.save()
        
        # Log the user in
        user = authenticate(
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1']
        )
        
        if user is not None:
            login(self.request, user)
            messages.success(self.request, 'Account created successfully! Please complete your profile.')
            return super().form_valid(form)
        
        messages.error(self.request, 'Error creating your account. Please try again.')
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('profile_complete')


class ProfileCompleteView(LoginRequiredMixin, UpdateView):
    model = PersonalProfile
    form_class = CombinedUserProfileForm
    template_name = 'users/profile_complete.html'
    success_url = reverse_lazy('home:incident_dashboard')  # Redirect to incident dashboard

    def get_object(self, queryset=None):
        # Get or create the user's profile
        profile, created = PersonalProfile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        # Get or create the profile if it doesn't exist
        if not hasattr(self, 'object'):
            self.object = self.get_object()
        return kwargs



def mask_email(email):
    if not email or '@' not in email:
        return email
    name, domain = email.split('@')
    # Mask 70% of characters before @
    mask_length = int(len(name) * 0.7)
    masked = '*' * mask_length + name[mask_length:]
    return masked + '@' + domain

def mask_phone(phone):
    if not phone or len(phone) < 4:
        return phone
    # Remove any non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) < 4:
        return phone
    # Show only last 3 digits
    masked = '*' * (len(digits)-3) + digits[-3:]
    return masked

class UserLoginView(TemplateView):
    template_name = 'users/login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home:incident_dashboard')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Please enter both email and password.'
                })
            return render(request, self.template_name, {
                'error_message': 'Please enter both email and password.'
            })

        # Normalize email to ensure case-insensitive matching
        email = email.lower().strip()
        
        # Authenticate using email as username
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect': '/incidents/dashboard/'
                })
            return redirect('incident_dashboard')
        else:
            error_msg = 'Invalid email or password.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': error_msg
                })
            return render(request, self.template_name, {
                'error_message': error_msg
            })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        show_delivery_method_modal = self.request.session.pop('show_delivery_method_modal', False)
        show_otp_modal = self.request.session.pop('show_otp_modal', False)
        email = self.request.session.pop('email', '')
        phone = self.request.session.pop('phone', '')
        context['show_delivery_method_modal'] = show_delivery_method_modal
        context['show_otp_modal'] = show_otp_modal
        context['email'] = email
        context['phone'] = phone
        return context

class UserLogoutView(TemplateView):
    template_name = 'home/landing.html'
    next_page = reverse_lazy('home:landing')

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(self.next_page)

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp(request):
    """Handle OTP delivery method selection and sending"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            delivery_method = data.get('delivery_method')
            
            if not delivery_method or delivery_method not in ['email', 'phone']:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid delivery method'
                })
            
            # Get pending user info from session
            user_id = request.session.get('pending_user_id')
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Session expired. Please login again.'
                })
            
            try:
                user = MyUser.objects.get(id=user_id)
                profile = user.profile
            except (MyUser.DoesNotExist, PersonalProfile.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': 'User profile not found'
                })
            
            # Generate OTP
            otp = generate_otp()
            
            # Store OTP in session with expiration
            request.session['otp'] = {
                'code': otp,
                'expires_at': (datetime.now() + timedelta(minutes=2)).isoformat(),
                'delivery_method': delivery_method
            }
            
            # TODO: Implement actual OTP sending via email/SMS
            # For development, print the OTP to console
            print(f"OTP for {user.id_number} (email: {user.email}): {otp}")
            
            # Set session variable to show OTP input modal
            request.session['show_otp_modal'] = True
            
            return JsonResponse({
                'success': True,
                'message': f'OTP sent to your {delivery_method}',
                'show_otp_modal': True
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid request data'
            })
        except Exception as e:
            print(f"Error sending OTP: {str(e)}")  # For debugging
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while sending OTP'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

def verify_otp(request):
    """Verify the OTP entered by the user"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            entered_otp = data.get('otp')
            
            # Get stored OTP from session
            stored_otp_data = request.session.get('otp')
            
            if not stored_otp_data:
                return JsonResponse({
                    'success': False,
                    'error': 'No OTP found. Please request a new one.'
                })
            
            # Check if OTP has expired
            expires_at = datetime.fromisoformat(stored_otp_data['expires_at'])
            if datetime.now() > expires_at:
                return JsonResponse({
                    'success': False,
                    'error': 'OTP has expired. Please request a new one.'
                })
            
            # Verify OTP
            if entered_otp == stored_otp_data['code']:
                # Get pending user from session
                user_id = request.session.get('pending_user_id')
                if not user_id:
                    return JsonResponse({
                        'success': False,
                        'error': 'Session expired. Please login again.'
                    })
                
                # Get user and log them in
                try:
                    user = MyUser.objects.get(id=user_id)
                    login(request, user, backend='users.auth_backend.EmailOrIDBackend')
                    
                    # Clear session data
                    del request.session['otp']
                    del request.session['pending_user_id']
                    del request.session['pending_user_email']
                    del request.session['pending_user_phone']
                    
                    # Return success response with redirect URL
                    response = JsonResponse({
                        'success': True,
                        'message': 'OTP verified successfully',
                        'redirect_url': '/dashboard/',  # Updated URL
                    })
                    print("Sending response:", response.content)  # Debug log
                    return response
                except MyUser.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'User not found. Please login again.'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid OTP'
                })
                
        except Exception as e:
            print(f"Error verifying OTP: {str(e)}")  # For debugging
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while verifying OTP'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = PersonalProfile
        fields = [ 'city', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            profile = user.profile
        except PersonalProfile.DoesNotExist:
            profile = None
        context['profile'] = profile
        context['first_name'] = profile.first_name if profile and profile.first_name else user.first_name
        context['last_name'] = profile.last_name if profile and profile.last_name else user.last_name
        return context

class UserProfileEditView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('profile')

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = user.profile
        except PersonalProfile.DoesNotExist:
            profile = PersonalProfile.objects.create(user=user)
        form = CombinedUserProfileForm(user=user, profile=profile)
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = user.profile
        except PersonalProfile.DoesNotExist:
            profile = PersonalProfile.objects.create(user=user)
        form = CombinedUserProfileForm(request.POST, user=user, profile=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect(self.success_url)
        return self.render_to_response({'form': form})

class UserSettingsForm(forms.ModelForm):
    current_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    new_password = forms.CharField(widget=forms.PasswordInput(), required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = MyUser
        fields = ['first_name', 'last_name']

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if any([current_password, new_password, confirm_password]):
            if not all([current_password, new_password, confirm_password]):
                raise forms.ValidationError("All password fields are required when changing password.")
            
            if not self.instance.check_password(current_password):
                raise forms.ValidationError("Current password is incorrect.")
            
            if new_password != confirm_password:
                raise forms.ValidationError("New passwords don't match.")
            
            if len(new_password) < 8:
                raise forms.ValidationError("New password must be at least 8 characters long.")

        return cleaned_data

class UserSettingsView(LoginRequiredMixin, UpdateView):
    model = MyUser
    form_class = UserSettingsForm
    template_name = 'users/settings.html'
    success_url = reverse_lazy('settings')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        if form.cleaned_data.get('new_password'):
            self.object.set_password(form.cleaned_data['new_password'])
        return super().form_valid(form)


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'users/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        # Get linked learners
        try:
            linked = LinkedLearners.objects.get(user=user)
            learner_ids = list(linked.learners.values_list('id', flat=True))
        except LinkedLearners.DoesNotExist:
            learner_ids = []
        # Search
        query = self.request.GET.get('q', '')
        learner_filter = self.request.GET.get('learner', '')
        date_filter = self.request.GET.get('date', '')
        type_filter = self.request.GET.get('type', '')
        qs = Notification.objects.filter(
            Q(recipient_user=user) |
            Q(recipient_learner__in=learner_ids)
        )
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(message__icontains=query))
        if learner_filter:
            qs = qs.filter(recipient_learner_id=learner_filter)
        if date_filter:
            qs = qs.filter(created_at__date=date_filter)
        if type_filter:
            qs = qs.filter(notification_type=type_filter)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        try:
            linked = LinkedLearners.objects.get(user=user)
            learners = linked.learners.all()
        except LinkedLearners.DoesNotExist:
            learners = []
        context['search_query'] = self.request.GET.get('q', '')
        context['learners'] = learners
        context['selected_learner'] = self.request.GET.get('learner', '')
        context['selected_date'] = self.request.GET.get('date', '')
        context['selected_type'] = self.request.GET.get('type', '')
        context['type_choices'] = Notification.NOTIFICATION_TYPE_CHOICES
        return context

class NotificationDetailView(LoginRequiredMixin, DetailView):
    model = Notification
    template_name = 'users/notification_detail.html'
    context_object_name = 'notification'

    def get_queryset(self):
        user = self.request.user
        try:
            linked = LinkedLearners.objects.get(user=user)
            learner_ids = linked.learners.values_list('id', flat=True)
        except LinkedLearners.DoesNotExist:
            learner_ids = []
        return Notification.objects.filter(
            Q(recipient_user=user) |
            Q(recipient_learner__in=learner_ids)
        )

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        notification = self.get_object()
        if not notification.read:
            notification.read = True
            notification.save()
        return response

@method_decorator(csrf_exempt, name='dispatch')
def mark_notification_read(request, pk):
    from .models import Notification
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            notification = Notification.objects.get(pk=pk)
            # Only allow if user is recipient or linked learner
            is_recipient = False
            if notification.recipient_user and notification.recipient_user == request.user:
                is_recipient = True
            if notification.recipient_learner:
                linked = getattr(request.user, 'linkedlearners', None)
                if linked and notification.recipient_learner in linked.learners.all():
                    is_recipient = True
            if not is_recipient:
                return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)
            notification.read = True
            notification.save()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found.'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request.'}, status=400)


