from django.urls import path
from .views import LoginView, RegisterView, VerifyTokenView, LogoutView

urlpatterns = [
    path('login/',    LoginView.as_view(),       name='auth-login'),
    path('register/', RegisterView.as_view(),    name='auth-register'),
    path('verify/',   VerifyTokenView.as_view(), name='auth-verify'),
    path('logout/',   LogoutView.as_view(),      name='auth-logout'),
]