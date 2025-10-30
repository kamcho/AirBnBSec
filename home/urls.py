from django.urls import path
from . import views
from home.views import test_view
from django.views.decorators.http import require_http_methods
app_name = 'home'

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('verify-client/', views.verify_client, name='verify_client'),
    path('verify-client/<str:verification_token>/', views.verify_client, name='verify_client_token'),
    
    # Security Incident CRUD URLs
    path('incidents/', views.SecurityIncidentListView.as_view(), name='incident_list'),
    path('incidents/dashboard/', views.incident_dashboard, name='incident_dashboard'),
    path('incidents/create/', views.SecurityIncidentCreateView.as_view(), name='incident_create'),
    
    # Multi-step incident creation URLs
    path('incidents/create/step1/', views.IncidentCreateStep1View.as_view(), name='incident_create_step1'),
    path('incidents/create/step2/', views.IncidentCreateStep2View.as_view(), name='incident_create_step2'),
    path('incidents/create/step3/', views.IncidentCreateStep3View.as_view(), name='incident_create_step3'),
    
    # Client management URLs
    path('incidents/<int:incident_id>/add-client/', views.AddClientToIncidentView.as_view(), name='add_client_to_incident'),
    path('incidents/<int:incident_id>/add-contact/', views.add_client_contact, name='add_client_contact'),
    
    path('incidents/<int:pk>/', views.SecurityIncidentDetailView.as_view(), name='incident_detail'),
    path('incidents/<int:pk>/edit/', views.SecurityIncidentUpdateView.as_view(), name='incident_update'),
    path('incidents/<int:pk>/delete/', views.SecurityIncidentDeleteView.as_view(), name='incident_delete'),
    path('incidents/<int:pk>/add-update/', views.add_incident_update, name='add_incident_update'),
    path('incidents/<int:pk>/update-status/', views.update_incident_status, name='update_incident_status'),
    
    # Evidence management URLs
    path('incidents/<int:incident_id>/evidence/', views.AddEvidenceView.as_view(), name='add_evidence'),
    path('evidence/<int:evidence_id>/delete/', require_http_methods(['POST'])(views.delete_evidence), name='delete_evidence'),
    
    # Comment management URLs
    path('incidents/<int:incident_id>/add-comment/', views.add_comment, name='add_comment'),
    path('comments/<int:comment_id>/delete/', require_http_methods(['POST'])(views.delete_comment), name='delete_comment'),
        path('test/', test_view),
    # Video management URLs
    path('incidents/<int:incident_id>/upload-video/', views.upload_explainer_video, name='upload_video'),
    path('videos/<int:video_id>/delete/', require_http_methods(['POST'])(views.delete_explainer_video), name='delete_video'),
]
