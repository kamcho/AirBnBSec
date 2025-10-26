from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('profile/complete/', views.ProfileCompleteView.as_view(), name='profile_complete'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/edit/', views.UserProfileEditView.as_view(), name='edit_profile'),
    path('settings/', views.UserSettingsView.as_view(), name='settings'),
    path('send-otp/', views.send_otp, name='send-otp'),
    path('verify-otp/', views.verify_otp, name='verify-otp'),
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('notifications/<int:pk>/mark-read/', views.mark_notification_read, name='notification_mark_read'),
]