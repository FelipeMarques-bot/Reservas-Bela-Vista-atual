from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def login_view(request):
    """View de login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"✅ Bem-vindo, {user.first_name or user.username}!")
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