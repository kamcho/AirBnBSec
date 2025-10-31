from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model
from .models import PersonalProfile
User = get_user_model()


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='ID Number or Email',
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-700 border-gray-600 text-white placeholder-gray-400',
            'placeholder': 'Enter your ID Number or Email',
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-700 border-gray-600 text-white placeholder-gray-400',
            'placeholder': 'Enter your password',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'ID Number or Email'

class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
        })
    )

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class CombinedUserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = PersonalProfile
        fields = ['first_name', 'last_name', 'phone', 'city', 'gender', 'location']

    def __init__(self, *args, **kwargs):
        # Get user and profile from kwargs before passing to parent
        self.user = kwargs.pop('user', None)
        profile = kwargs.pop('profile', None)
        
        # If we have an instance but no profile, use the instance
        instance = kwargs.get('instance')
        if instance and not profile:
            profile = instance
            kwargs['instance'] = instance
        
        # If we have a profile but no instance, set the instance
        if profile and not instance:
            kwargs['instance'] = profile
            
        super().__init__(*args, **kwargs)
        
        # If we have a user, set initial values
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name

    def save(self, commit=True):
        # Get the profile instance from the form
        profile = super().save(commit=False)
        
        # Update user fields if we have a user
        if hasattr(self, 'user') and self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            if commit:
                self.user.save()
        
        # Save the profile if commit is True
        if commit:
            profile.save()
            
        return profile

    def clean_phone(self):
        phone = self.cleaned_data.get('phone') or ''
        normalized = self._normalize_phone(phone)
        if not normalized:
            return phone
        # Enforce uniqueness against other users' profiles
        qs = PersonalProfile.objects.filter(phone=normalized)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This phone number is already in use.')
        return normalized

    @staticmethod
    def _normalize_phone(value: str) -> str:
        v = (value or '').strip()
        if not v:
            return ''
        # Remove spaces and dashes
        for ch in [' ', '-', '(', ')']:
            v = v.replace(ch, '')
        # Remove leading '+' for storage
        v_no_plus = v[1:] if v.startswith('+') else v
        # If starts with 07..., convert to 2547...
        if v_no_plus.startswith('07'):
            return '254' + v_no_plus[1:]
        # If already 2547..., keep as is
        return v_no_plus

