from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone

class Quiosque(models.Model):
    QUIOSQUES_CHOICES = [
        ('AZ', 'Azaléia'),
        ('PR', 'Primavera'),
    ]

    nome = models.CharField(max_length=2, choices=QUIOSQUES_CHOICES, unique=True, verbose_name="Nome do Quiosque")
    capacidade_maxima = models.PositiveIntegerField(verbose_name="Capacidade Máxima de Pessoas")
    valor_diaria = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Diária (R$)")
    disponivel = models.BooleanField(default=True, verbose_name="Disponível para Reserva")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição")
    imagem = models.ImageField(upload_to='quiosques/', blank=True, null=True, verbose_name="Imagem do Quiosque")

    class Meta:
        verbose_name = "Quiosque"
        verbose_name_plural = "Quiosques"
        ordering = ['nome']

    def __str__(self):
        return self.get_nome_display()


class Lote(models.Model):
    numero_lote = models.CharField(max_length=10, unique=True, verbose_name="Número do Lote")
    proprietario = models.CharField(max_length=100, verbose_name="Nome do Proprietário")
    telefone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Telefone de Contato")
    usuario = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='lote', verbose_name="Usuário Vinculado")

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ['numero_lote']

    def __str__(self):
        return f"Lote {self.numero_lote} - {self.proprietario}"


class Reserva(models.Model):
    quiosque = models.ForeignKey(Quiosque, on_delete=models.CASCADE, related_name='reservas', verbose_name="Quiosque")
    lote = models.ForeignKey(Lote, on_delete=models.CASCADE, related_name='reservas', verbose_name="Lote")
    responsavel = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservas', verbose_name="Responsável")
    data_reserva = models.DateField(verbose_name="Data da Reserva")
    data_solicitacao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Solicitação")
    quantidade_pessoas = models.PositiveIntegerField(verbose_name="Quantidade de Pessoas")
    confirmada = models.BooleanField(default=False, verbose_name="Reserva Confirmada")
    valor_reserva = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor da Reserva (R$)")
    comprovante_pagamento = models.CharField(max_length=500, blank=True, null=True, verbose_name="Comprovante de Pagamento")

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-data_reserva']
        unique_together = ['quiosque', 'data_reserva']

    def clean(self):
        if not self.data_reserva:
            return

        hoje = timezone.localdate()

        if self.data_reserva < hoje:
            raise ValidationError("Não é possível fazer reservas para datas passadas.")

        # Moradores devem respeitar antecedência mínima de 2 dias.
        # Admin/staff pode agendar sem essa restrição (inclusive pelo Django Admin).
        admin_no_responsavel = bool(
            self.responsavel and (self.responsavel.is_staff or self.responsavel.is_superuser)
        )
        admin_na_requisicao = bool(getattr(self, '_usuario_admin_requisicao', False))

        if not (admin_no_responsavel or admin_na_requisicao):
            if self.data_reserva < hoje + timedelta(days=2):
                raise ValidationError("A reserva deve ser feita com pelo menos 2 dias de antecedência.")

    def save(self, *args, **kwargs):
        if self.quiosque_id and not self.valor_reserva:
            self.valor_reserva = self.quiosque.valor_diaria
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quiosque.get_nome_display()} - {self.data_reserva} - Lote {self.lote.numero_lote}"
