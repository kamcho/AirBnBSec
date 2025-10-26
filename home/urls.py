from django.urls import path
from . import views
app_name = 'home'

urlpatterns = [
    path('', views.LandingPageView.as_view(), name='landing'),
    path('verify-client/', views.verify_client, name='verify_client'),
    path('verify-client/<str:verification_token>/', views.verify_client, name='verify_client_token'),
    
    # Security Incident CRUD URLs
    path('incidents/', views.SecurityIncidentListView.as_view(), name='incident_list'),
    path('incidents/dashboard/', views.incident_dashboard, name='incident_dashboard'),
    path('incidents/create/', views.SecurityIncidentCreateView.as_view(), name='incident_create'),
    path('incidents/<int:pk>/', views.SecurityIncidentDetailView.as_view(), name='incident_detail'),
    path('incidents/<int:pk>/edit/', views.SecurityIncidentUpdateView.as_view(), name='incident_update'),
    path('incidents/<int:pk>/delete/', views.SecurityIncidentDeleteView.as_view(), name='incident_delete'),
    path('incidents/<int:pk>/add-update/', views.add_incident_update, name='add_incident_update'),
    path('incidents/<int:pk>/update-status/', views.update_incident_status, name='update_incident_status'),
]
