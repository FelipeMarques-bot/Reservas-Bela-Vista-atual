from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .forms import ReservaForm
from .models import Lote, Quiosque, Reserva


class ReservaComprovanteObrigatorioTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='morador01', password='senha123')
		self.lote = Lote.objects.create(numero_lote='29', proprietario='Morador Teste', usuario=self.user)
		self.quiosque = Quiosque.objects.create(
			nome='AZ',
			capacidade_maxima=30,
			valor_diaria=Decimal('100.00'),
			disponivel=True,
		)

	def test_model_full_clean_rejeita_reserva_sem_comprovante(self):
		reserva = Reserva(
			quiosque=self.quiosque,
			lote=self.lote,
			responsavel=self.user,
			data_reserva=timezone.localdate() + timedelta(days=3),
			quantidade_pessoas=10,
			valor_reserva=Decimal('100.00'),
			comprovante_pagamento='',
		)

		with self.assertRaises(ValidationError) as exc:
			reserva.full_clean()

		self.assertIn('comprovante_pagamento', exc.exception.message_dict)

	def test_form_invalido_quando_comprovante_nao_for_enviado(self):
		form = ReservaForm(
			data={
				'numero_lote_input': '29',
				'data_reserva': (timezone.localdate() + timedelta(days=3)).isoformat(),
				'quantidade_pessoas': 8,
			},
			files={},
			user=self.user,
		)

		self.assertFalse(form.is_valid())
		self.assertIn('comprovante_pagamento', form.errors)
