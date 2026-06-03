from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from django.contrib.auth.models import User
from .models import Quiosque, Lote, Reserva

@admin.register(Quiosque)
class QuiosqueAdmin(admin.ModelAdmin):
    list_display = ['nome', 'capacidade_maxima', 'valor_diaria', 'disponivel']
    list_filter = ['disponivel']
    search_fields = ['nome', 'descricao']
    list_editable = ['disponivel']

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    change_list_template = 'admin/reservas_quiosques/lote/change_list.html'
    list_display = ['numero_lote', 'proprietario', 'telefone', 'usuario', 'status_acesso', 'acoes_acesso']
    search_fields = ['numero_lote', 'proprietario']
    list_filter = ['usuario']
    readonly_fields = ['usuario']  # Não permite editar o usuário vinculado manualmente
    actions = ['bloquear_acesso_lotes', 'desbloquear_acesso_lotes', 'criar_usuario_lotes']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:lote_id>/bloquear-usuario/',
                self.admin_site.admin_view(self.bloquear_usuario_lote_view),
                name='reservas_quiosques_lote_bloquear_usuario',
            ),
            path(
                '<int:lote_id>/desbloquear-usuario/',
                self.admin_site.admin_view(self.desbloquear_usuario_lote_view),
                name='reservas_quiosques_lote_desbloquear_usuario',
            ),
            path(
                '<int:lote_id>/criar-usuario/',
                self.admin_site.admin_view(self.criar_usuario_lote_view),
                name='reservas_quiosques_lote_criar_usuario',
            ),
        ]
        return custom_urls + urls

    @admin.display(description='Status de Acesso')
    def status_acesso(self, obj):
        if not obj.usuario:
            return format_html('<span class="bv-user-status is-blocked">Sem usuário</span>')
        if getattr(obj, 'bloqueado', False):
            return format_html('<span class="bv-user-status is-blocked">Bloqueado</span>')
        return format_html('<span class="bv-user-status is-active">Ativo</span>')

    @admin.display(description='Ações de Acesso')
    def acoes_acesso(self, obj):
        if not obj.usuario:
            criar_url = reverse('admin:reservas_quiosques_lote_criar_usuario', args=[obj.pk])
            return format_html(
                '<a class="bv-user-inline-action is-unblock" href="{}">Criar usuário</a>',
                criar_url,
            )

        if getattr(obj, 'bloqueado', False):
            desbloquear_url = reverse('admin:reservas_quiosques_lote_desbloquear_usuario', args=[obj.pk])
            return format_html(
                '<a class="bv-user-inline-action is-unblock" href="{}">Desbloquear</a>',
                desbloquear_url,
            )

        bloquear_url = reverse('admin:reservas_quiosques_lote_bloquear_usuario', args=[obj.pk])
        return format_html(
            '<a class="bv-user-inline-action is-block" href="{}">Bloquear</a>',
            bloquear_url,
        )

    @admin.action(description='Bloquear usuários vinculados aos lotes selecionados')
    def bloquear_acesso_lotes(self, request, queryset):
        total = queryset.filter(bloqueado=False).update(bloqueado=True)
        sem_usuario = queryset.filter(usuario__isnull=True).count()
        self.message_user(request, f'{total} lote(s) bloqueado(s) com sucesso.', level=messages.SUCCESS)
        if sem_usuario:
            self.message_user(request, f'{sem_usuario} lote(s) não possuem usuário vinculado.', level=messages.WARNING)

    @admin.action(description='Desbloquear usuários vinculados aos lotes selecionados')
    def desbloquear_acesso_lotes(self, request, queryset):
        total = queryset.filter(bloqueado=True).update(bloqueado=False)
        sem_usuario = queryset.filter(usuario__isnull=True).count()
        self.message_user(request, f'{total} lote(s) desbloqueado(s) com sucesso.', level=messages.SUCCESS)
        if sem_usuario:
            self.message_user(request, f'{sem_usuario} lote(s) não possuem usuário vinculado.', level=messages.WARNING)

    @admin.action(description='Criar usuário para lotes selecionados sem vínculo')
    def criar_usuario_lotes(self, request, queryset):
        criados = 0
        pulados = 0

        for lote in queryset.select_related('usuario'):
            if lote.usuario_id:
                pulados += 1
                continue

            username = f'lote{lote.numero_lote}'.lower().replace(' ', '')
            if User.objects.filter(username=username).exists():
                pulados += 1
                continue

            user = User.objects.create_user(
                username=username,
                password='senha123',
                first_name=lote.proprietario,
            )
            lote.usuario = user
            lote.save(update_fields=['usuario'])
            criados += 1

        if criados:
            self.message_user(request, f'{criados} usuário(s) criado(s) com senha temporária "senha123".', level=messages.SUCCESS)
        if pulados:
            self.message_user(request, f'{pulados} lote(s) foram ignorados (já vinculados ou username existente).', level=messages.WARNING)

    def bloquear_usuario_lote_view(self, request, lote_id):
        lote = Lote.objects.select_related('usuario').filter(pk=lote_id).first()
        if lote:
            lote.bloqueado = True
            lote.save(update_fields=['bloqueado'])
            self.message_user(request, f'Usuário do lote {lote.numero_lote} bloqueado com sucesso.', level=messages.SUCCESS)
        else:
            self.message_user(request, 'Lote não encontrado.', level=messages.WARNING)
        return HttpResponseRedirect(reverse('admin:reservas_quiosques_lote_changelist'))

    def desbloquear_usuario_lote_view(self, request, lote_id):
        lote = Lote.objects.select_related('usuario').filter(pk=lote_id).first()
        if lote:
            lote.bloqueado = False
            lote.save(update_fields=['bloqueado'])
            self.message_user(request, f'Usuário do lote {lote.numero_lote} desbloqueado com sucesso.', level=messages.SUCCESS)
        else:
            self.message_user(request, 'Lote não encontrado.', level=messages.WARNING)
        return HttpResponseRedirect(reverse('admin:reservas_quiosques_lote_changelist'))

    def criar_usuario_lote_view(self, request, lote_id):
        lote = Lote.objects.select_related('usuario').filter(pk=lote_id).first()
        if not lote:
            self.message_user(request, 'Lote não encontrado.', level=messages.ERROR)
            return HttpResponseRedirect(reverse('admin:reservas_quiosques_lote_changelist'))

        if lote.usuario_id:
            self.message_user(request, f'O lote {lote.numero_lote} já possui usuário vinculado.', level=messages.WARNING)
            return HttpResponseRedirect(reverse('admin:reservas_quiosques_lote_changelist'))

        username = f'lote{lote.numero_lote}'.lower().replace(' ', '')
        if User.objects.filter(username=username).exists():
            self.message_user(request, f'O username {username} já existe. Crie manualmente em Usuários.', level=messages.WARNING)
            return HttpResponseRedirect(reverse('admin:reservas_quiosques_lote_changelist'))

        user = User.objects.create_user(
            username=username,
            password='senha123',
            first_name=lote.proprietario,
        )
        lote.usuario = user
        lote.save(update_fields=['usuario'])
        self.message_user(
            request,
            f'Usuário {username} criado e vinculado ao lote {lote.numero_lote} com senha temporária "senha123".',
            level=messages.SUCCESS,
        )
        return HttpResponseRedirect(reverse('admin:reservas_quiosques_lote_changelist'))

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ['quiosque', 'lote', 'responsavel', 'data_reserva', 'confirmada', 'valor_reserva']
    list_filter = ['confirmada', 'data_reserva', 'quiosque']
    search_fields = ['lote__numero_lote', 'responsavel__username', 'quiosque__nome']
    list_editable = ['confirmada']
    readonly_fields = ['data_solicitacao', 'valor_reserva']
    date_hierarchy = 'data_reserva'

    fieldsets = (
        ('Informações da Reserva', {
            'fields': ('quiosque', 'lote', 'responsavel', 'data_reserva', 'quantidade_pessoas')
        }),
        ('Pagamento', {
            'fields': ('valor_reserva', 'comprovante_pagamento', 'confirmada')
        }),
        ('Dados do Sistema', {
            'fields': ('data_solicitacao',),
            'classes': ('collapse',)
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        class ReservaAdminForm(form_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields['comprovante_pagamento'].required = True

            def clean(self):
                cleaned_data = super().clean()
                self.instance._usuario_admin_requisicao = bool(
                    request.user.is_staff or request.user.is_superuser
                )
                return cleaned_data

        return ReservaAdminForm