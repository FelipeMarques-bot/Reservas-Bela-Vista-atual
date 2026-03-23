from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic import CreateView
from django.contrib.auth.forms import UserCreationForm

app_name = 'usuarios'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='reservas_quiosques:lista_quiosques'), name='logout'),
    path('register/', CreateView.as_view(
        template_name='usuarios/register.html',
        form_class=UserCreationForm,
        success_url=reverse_lazy('reservas_quiosques:lista_quiosques')
    ), name='register'),
]