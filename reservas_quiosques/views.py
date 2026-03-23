from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import Quiosque, Reserva, Lote
from .forms import ReservaForm, CriarSenhaForm

def lista_quiosques(request):
    """Exibe a lista de quiosques disponíveis para reserva"""
    quiosques = Quiosque.objects.filter(disponivel=True).order_by('nome')
    context = {'quiosques': quiosques}
    return render(request, 'reservas_quiosques/lista_quiosques.html', context)

@login_required
def minhas_reservas(request):
    """Exibe as reservas feitas pelo usuário logado"""
    reservas = Reserva.objects.filter(responsavel=request.user).select_related('quiosque', 'lote').order_by('-data_reserva')
    context = {'reservas': reservas}
    return render(request, 'reservas_quiosques/minhas_reservas.html', context)

def reservar_quiosque(request, quiosque_id):
    """Permite reservar um quiosque - com criação de conta se necessário"""
    quiosque = get_object_or_404(Quiosque, id=quiosque_id)

    # Se o usuário NÃO está logado, precisa verificar o lote primeiro
    if not request.user.is_authenticated:
        if request.method == 'POST' and 'numero_lote' in request.POST:
            numero_lote = request.POST.get('numero_lote').strip().upper()

            try:
                lote = Lote.objects.get(numero_lote=numero_lote)

                # Verifica se o lote JÁ tem usuário vinculado
                if lote.usuario:
                    messages.warning(request, f"O Lote {numero_lote} já possui um usuário cadastrado. Por favor, faça login.")
                    return redirect('usuarios:login')

                # Lote existe mas NÃO tem usuário - redireciona para criar senha
                request.session['lote_id'] = lote.id
                request.session['quiosque_id'] = quiosque_id
                return redirect('reservas_quiosques:criar_senha')

            except Lote.DoesNotExist:
                messages.error(request, f"Lote {numero_lote} não encontrado. Entre em contato com o administrador.")

        # Mostra formulário para digitar o número do lote
        context = {'quiosque': quiosque}
        return render(request, 'reservas_quiosques/verificar_lote.html', context)

    # Usuário JÁ está logado - mostra formulário de reserva
    if request.method == 'POST':
        # ✅ IMPORTANTE: Passar request.FILES para o formulário
        form = ReservaForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            try:
                # Pega o lote validado do formulário
                lote_obj = form.cleaned_data['numero_lote_input']

                # Cria a reserva
                reserva = form.save(commit=False)
                reserva.quiosque = quiosque
                reserva.responsavel = request.user
                reserva.lote = lote_obj
                reserva.valor_reserva = quiosque.valor_diaria

                # ✅ O comprovante já vem do form.save() automaticamente
                # Não precisa fazer nada extra, o Django cuida disso

                # Atualiza dados do lote
                if form.cleaned_data.get('nome_responsavel_input'):
                    lote_obj.proprietario = form.cleaned_data['nome_responsavel_input']
                if form.cleaned_data.get('telefone_contato_input'):
                    lote_obj.telefone = form.cleaned_data['telefone_contato_input']
                lote_obj.save()

                # Salva a reserva
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
            # Mostra erros do formulário
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
    """Tela para o morador criar senha no primeiro acesso"""
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

            # Cria o username baseado no número do lote
            username = f"lote{lote.numero_lote}".lower().replace(" ", "")

            # Cria o usuário
            user = User.objects.create_user(
                username=username,
                password=senha,
                first_name=lote.proprietario
            )

            # Vincula o usuário ao lote
            lote.usuario = user
            lote.save()

            # Faz login automaticamente
            login(request, user)

            messages.success(request, f"✅ Conta criada com sucesso! Bem-vindo, {lote.proprietario}!")

            # Limpa a sessão
            del request.session['lote_id']

            # Redireciona para a reserva do quiosque
            if quiosque_id:
                del request.session['quiosque_id']
                return redirect('reservas_quiosques:reservar_quiosque', quiosque_id=quiosque_id)

            return redirect('reservas_quiosques:lista_quiosques')
    else:
        form = CriarSenhaForm()

    context = {
        'form': form,
        'lote': lote
    }
    return render(request, 'reservas_quiosques/criar_senha.html', context)

@login_required
def cancelar_reserva(request, reserva_id):
    """Permite que o usuário cancele uma reserva não confirmada"""
    reserva = get_object_or_404(Reserva, id=reserva_id, responsavel=request.user)

    # Só permite cancelar reservas NÃO confirmadas
    if reserva.confirmada:
        messages.error(request, "❌ Não é possível cancelar uma reserva já confirmada. Entre em contato com o administrador.")
        return redirect('reservas_quiosques:minhas_reservas')

    # Guarda informações para a mensagem
    quiosque_nome = reserva.quiosque.get_nome_display()
    data_reserva = reserva.data_reserva.strftime("%d/%m/%Y")

    # Deleta a reserva
    reserva.delete()

    messages.success(
        request,
        f'✅ Reserva do {quiosque_nome} para o dia {data_reserva} foi cancelada com sucesso!'
    )

    return redirect('reservas_quiosques:minhas_reservas')