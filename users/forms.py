from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model

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

class CombinedUserProfileForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=100, required=False)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], required=False)
    location = forms.CharField(max_length=255, required=False)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, user=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
        if profile:
            self.fields['phone'].initial = profile.phone
            self.fields['city'].initial = profile.city
            self.fields['gender'].initial = profile.gender
            self.fields['location'].initial = profile.location
            self.fields['date_of_birth'].initial = profile.date_of_birth
        self.user_instance = user
        self.profile_instance = profile

    def save(self):
        # Save to MyUser
        user = self.user_instance
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()
        # Save to PersonalProfile
        profile = self.profile_instance
        profile.phone = self.cleaned_data['phone']
        profile.city = self.cleaned_data['city']
        profile.gender = self.cleaned_data['gender']
        profile.location = self.cleaned_data['location']
        profile.date_of_birth = self.cleaned_data['date_of_birth']
        profile.save()
        return user, profile

