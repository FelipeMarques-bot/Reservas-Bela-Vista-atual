from django.contrib import admin
from .models import Quiosque, Lote, Reserva

@admin.register(Quiosque)
class QuiosqueAdmin(admin.ModelAdmin):
    list_display = ['nome', 'capacidade_maxima', 'valor_diaria', 'disponivel']
    list_filter = ['disponivel']
    search_fields = ['nome', 'descricao']
    list_editable = ['disponivel']

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ['numero_lote', 'proprietario', 'telefone', 'usuario']
    search_fields = ['numero_lote', 'proprietario']
    list_filter = ['usuario']
    readonly_fields = ['usuario']  # Não permite editar o usuário vinculado manualmente

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
            def clean(self):
                cleaned_data = super().clean()
                self.instance._usuario_admin_requisicao = bool(
                    request.user.is_staff or request.user.is_superuser
                )
                return cleaned_data

        return ReservaAdminForm