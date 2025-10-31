from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from . import api_views
from .whatsapp import whatsapp_webhook

urlpatterns = [
    # Password reset URLs
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
         
    # API endpoints
    path('clients/save-verified-client/', api_views.save_verified_client, name='save_verified_client'),
    path('incidents/<int:incident_id>/set-client/', api_views.set_incident_client, name='set_incident_client'),
    
    # Your existing URL patterns
    path('verify-kra/', views.verify_kra, name='verify_kra'),
    path('verify-kra/<str:id_number>/', views.verify_id_number, name='verify_id_number'),
    path('webhook/whatsapp/', whatsapp_webhook, name='whatsapp_webhook'),
]
