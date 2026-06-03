from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.exceptions import ValidationError


class CustomAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        print(f"\n--- DEBUG: Tentativa de login para o usuário: {username} ---")

        if username and password:
            user = authenticate(username=username, password=password)

            if user is None:
                try:
                    existing_user = User.objects.get(username=username)
                    if not existing_user.is_active:
                        print(f"--- DEBUG: Usuário inativo: {existing_user.username} ---")
                        raise ValidationError(
                            "Entre em contato com o administrador do condomínio.",
                            code='inactive'
                        )
                except User.DoesNotExist:
                    print(f"--- DEBUG: Usuário não encontrado no DB: {username} ---")
                    pass

            if user is not None:
                lote = getattr(user, 'lote', None)
                if lote and getattr(lote, 'bloqueado', False):
                    print(f"--- DEBUG: Usuário bloqueado no lote: {user.username} ---")
                    raise ValidationError(
                        "Entre em contato com o administrador do condomínio.",
                        code='blocked'
                    )

        print("--- DEBUG: Chamando super().clean() ---")
        return super().clean()


class CustomLoginView(LoginView):
    template_name = 'usuarios/login.html'
    authentication_form = CustomAuthenticationForm

    def form_invalid(self, form):
        print(f"--- DEBUG: form_invalid() chamado. Erros do formulário: {form.errors} ---") # DEBUG
        if form.errors.get('__all__') and any(e.code == 'inactive' for e in form.errors.get('__all__')):
            messages.error(self.request, "❌ Entre em contato com o administrador do condomínio.")
            print("--- DEBUG: Mensagem de usuário inativo adicionada. ---") # DEBUG
        else:
            messages.error(self.request, "❌ Usuário ou senha incorretos.")
            print("--- DEBUG: Mensagem de credenciais incorretas adicionada. ---") # DEBUG
        return super().form_invalid(form)


@login_required
def logout_view(request):
    """View de logout - ACEITA GET E POST"""
    logout(request)
    messages.success(request, "✅ Você saiu com sucesso!")
    return redirect('reservas_quiosques:lista_quiosques')