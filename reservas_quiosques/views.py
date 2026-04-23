from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Quiosque, Reserva, Lote
from .forms import ReservaForm, CriarSenhaForm
import cloudinary.uploader

def lista_quiosques(request):
    quiosques = Quiosque.objects.filter(disponivel=True).order_by('nome')
    context = {'quiosques': quiosques}
    return render(request, 'reservas_quiosques/lista_quiosques.html', context)

@login_required
def minhas_reservas(request):
    reservas = Reserva.objects.filter(responsavel=request.user).select_related('quiosque', 'lote').order_by('-data_reserva')
    context = {'reservas': reservas}
    return render(request, 'reservas_quiosques/minhas_reservas.html', context)

def reservar_quiosque(request, quiosque_id):
    quiosque = get_object_or_404(Quiosque, id=quiosque_id)

    if not request.user.is_authenticated:
        if request.method == 'POST' and 'numero_lote' in request.POST:
            numero_lote = request.POST.get('numero_lote').strip().upper()
            try:
                lote = Lote.objects.get(numero_lote=numero_lote)
                if lote.usuario:
                    messages.warning(request, f"O Lote {numero_lote} já possui um usuário cadastrado. Por favor, faça login.")
                    return redirect('usuarios:login')
                request.session['lote_id'] = lote.id
                request.session['quiosque_id'] = quiosque_id
                return redirect('reservas_quiosques:criar_senha')
            except Lote.DoesNotExist:
                messages.error(request, f"Lote {numero_lote} não encontrado. Entre em contato com o administrador.")

        context = {'quiosque': quiosque}
        return render(request, 'reservas_quiosques/verificar_lote.html', context)

    if request.method == 'POST':
        form = ReservaForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            try:
                lote_obj = form.cleaned_data['numero_lote_input']
                comprovante = request.FILES.get('comprovante_pagamento')

                if not comprovante:
                    messages.error(request, '❌ O comprovante de pagamento é obrigatório para salvar a reserva.')
                    context = {'form': form, 'quiosque': quiosque}
                    return render(request, 'reservas_quiosques/reservar_quiosque.html', context)

                reserva = form.save(commit=False)
                reserva.quiosque = quiosque
                reserva.responsavel = request.user
                reserva.lote = lote_obj
                reserva.valor_reserva = quiosque.valor_diaria

                if comprovante:
                    resultado = cloudinary.uploader.upload(
                        comprovante,
                        folder='comprovantes',
                        resource_type='auto',
                    )
                    reserva.comprovante_pagamento = resultado['secure_url']

                if form.cleaned_data.get('nome_responsavel_input'):
                    lote_obj.proprietario = form.cleaned_data['nome_responsavel_input']
                if form.cleaned_data.get('telefone_contato_input'):
                    lote_obj.telefone = form.cleaned_data['telefone_contato_input']
                lote_obj.save()

                reserva.save()

                messages.success(
                    request,
                    f'✅ Sua reserva do {quiosque.get_nome_display()} '
                    f'para o dia {reserva.data_reserva.strftime("%d/%m/%Y")} '
                    f'foi solicitada com sucesso! Aguarde a confirmação.'
                )
                return redirect('reservas_quiosques:minhas_reservas')

            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
            except Exception as e:
                messages.error(request, f'❌ Erro ao salvar a reserva: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        field_label = form.fields[field].label if field in form.fields else field
                        messages.error(request, f"❌ {field_label}: {error}")
    else:
        form = ReservaForm()

    context = {'form': form, 'quiosque': quiosque}
    return render(request, 'reservas_quiosques/reservar_quiosque.html', context)

def criar_senha(request):
    lote_id = request.session.get('lote_id')
    quiosque_id = request.session.get('quiosque_id')

    if not lote_id:
        messages.error(request, "Sessão expirada. Por favor, tente novamente.")
        return redirect('reservas_quiosques:lista_quiosques')

    lote = get_object_or_404(Lote, id=lote_id)

    if request.method == 'POST':
        form = CriarSenhaForm(request.POST)
        if form.is_valid():
            senha = form.cleaned_data['senha']
            username = f"lote{lote.numero_lote}".lower().replace(" ", "")
            user = User.objects.create_user(
                username=username,
                password=senha,
                first_name=lote.proprietario
            )
            lote.usuario = user
            lote.save()
            login(request, user)
            messages.success(request, f"✅ Conta criada com sucesso! Bem-vindo, {lote.proprietario}!")
            del request.session['lote_id']
            if quiosque_id:
                del request.session['quiosque_id']
                return redirect('reservas_quiosques:reservar_quiosque', quiosque_id=quiosque_id)
            return redirect('reservas_quiosques:lista_quiosques')
    else:
        form = CriarSenhaForm()

    context = {'form': form, 'lote': lote}
    return render(request, 'reservas_quiosques/criar_senha.html', context)

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, responsavel=request.user)

    if reserva.confirmada:
        messages.error(request, "❌ Não é possível cancelar uma reserva já confirmada. Entre em contato com o administrador.")
        return redirect('reservas_quiosques:minhas_reservas')

    quiosque_nome = reserva.quiosque.get_nome_display()
    data_reserva = reserva.data_reserva.strftime("%d/%m/%Y")
    reserva.delete()

    messages.success(
        request,
        f'✅ Reserva do {quiosque_nome} para o dia {data_reserva} foi cancelada com sucesso!'
    )
    return redirect('reservas_quiosques:minhas_reservas')
