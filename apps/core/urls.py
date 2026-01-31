from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Rota principal: dashboard do núcleo/core do sistema
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Exemplos para expansão futura:
    # path('login/', views.LoginView.as_view(), name='login'),
    # path('logout/', views.LogoutView.as_view(), name='logout'),
    # path('perfil/', views.ProfileView.as_view(), name='perfil'),
]