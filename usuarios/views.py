from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.exceptions import ValidationError


class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'inactive': 'Entre em contato com o adminsitrador do condomínio',
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = None

            if user and not user.is_active and user.check_password(password):
                raise ValidationError(self.error_messages['inactive'], code='inactive')

        return super().clean()


class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    authentication_form = CustomAuthenticationForm

def login_view(request):
    """View de login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user and not user.is_active and user.check_password(password):
            messages.error(request, "❌ Entre em contato com o administrador do condomínio")
            return render(request, 'usuarios/login.html')

        authenticated_user = authenticate(request, username=username, password=password)

        if authenticated_user is not None:
            login(request, authenticated_user)
            messages.success(request, f"✅ Bem-vindo, {authenticated_user.first_name or authenticated_user.username}!")
            return redirect('reservas_quiosques:lista_quiosques')
        else:
            messages.error(request, "❌ Usuário ou senha incorretos.")

    return render(request, 'usuarios/login.html')


@login_required
def logout_view(request):
    """View de logout - ACEITA GET E POST"""
    logout(request)
    messages.success(request, "✅ Você saiu com sucesso!")
    return redirect('reservas_quiosques:lista_quiosques')