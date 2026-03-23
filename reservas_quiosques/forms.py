from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit
from .models import Reserva, Lote
from django.utils import timezone

class ReservaForm(forms.ModelForm):
    numero_lote_input = forms.CharField(
        max_length=10,
        label="Número do Lote",
        help_text="Ex: 29",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o número do seu lote'})
    )
    nome_responsavel_input = forms.CharField(
        max_length=100,
        label="Nome Completo do Responsável",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu nome completo'})
    )
    telefone_contato_input = forms.CharField(
        max_length=15,
        label="Telefone de Contato",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'})
    )

    class Meta:
        model = Reserva
        fields = ['data_reserva', 'quantidade_pessoas', 'comprovante_pagamento']
        widgets = {
            'data_reserva': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantidade_pessoas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'comprovante_pagamento': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'data_reserva': 'Data da Reserva',
            'quantidade_pessoas': 'Quantas Pessoas Participarão?',
            'comprovante_pagamento': '📎 Anexar Comprovante de Pagamento (Imagem ou PDF)',
        }
        help_texts = {
            'data_reserva': 'A reserva deve ser feita com pelo menos 2 dias de antecedência.',
            'comprovante_pagamento': '⚠️ OBRIGATÓRIO - Formatos aceitos: JPG, PNG, PDF (máx. 5MB)',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['comprovante_pagamento'].required = True

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Row(
                Column('numero_lote_input', css_class='form-group col-md-6 mb-3'),
                Column('data_reserva', css_class='form-group col-md-6 mb-3'),
                css_class='row'
            ),
            Row(
                Column('quantidade_pessoas', css_class='form-group col-md-12 mb-3'),
                css_class='row'
            ),
            Row(
                Column('nome_responsavel_input', css_class='form-group col-md-6 mb-3'),
                Column('telefone_contato_input', css_class='form-group col-md-6 mb-3'),
                css_class='row'
            ),
            Row(
                Column('comprovante_pagamento', css_class='form-group col-md-12 mb-3'),
                css_class='row'
            ),
            Submit('submit', 'Solicitar Reserva', css_class='btn btn-primary mt-3')
        )

    def clean_numero_lote_input(self):
        numero_lote = self.cleaned_data['numero_lote_input'].strip().upper()
        try:
            lote = Lote.objects.get(numero_lote=numero_lote)
        except Lote.DoesNotExist:
            raise ValidationError(f"Lote {numero_lote} não encontrado. Entre em contato com o administrador.")
        return lote

    def clean_data_reserva(self):
        data_reserva = self.cleaned_data['data_reserva']
        hoje = timezone.localdate()

        # Admin (superuser ou staff) não tem restrição de antecedência
        if self.user and (self.user.is_superuser or self.user.is_staff):
            return data_reserva

        if data_reserva < hoje:
            raise ValidationError("Não é possível fazer reservas para datas passadas.")

        if data_reserva < hoje + timezone.timedelta(days=2):
            raise ValidationError("A reserva deve ser feita com pelo menos 2 dias de antecedência.")

        return data_reserva

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class CriarSenhaForm(forms.Form):
    senha = forms.CharField(
        label="Crie sua Senha",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite uma senha segura'
        }),
        min_length=6,
        help_text="Mínimo de 6 caracteres."
    )
    confirmar_senha = forms.CharField(
        label="Confirme sua Senha",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a senha novamente'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')

        if senha and confirmar_senha and senha != confirmar_senha:
            raise ValidationError("As senhas não coincidem. Tente novamente.")

        return cleaned_data
