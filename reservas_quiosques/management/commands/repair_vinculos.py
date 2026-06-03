from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from reservas_quiosques.models import Lote


class Command(BaseCommand):
    help = 'Repara vínculos de lotes buscando usuários pelo padrão lote{numero_lote}.'

    def handle(self, *args, **options):
        vinculados = 0
        nao_encontrados = []

        for lote in Lote.objects.all():
            expected_username = f'lote{lote.numero_lote}'.lower().replace(' ', '')
            user = User.objects.filter(username=expected_username).first()
            if not user:
                nao_encontrados.append(lote.numero_lote)
                continue

            if lote.usuario_id != user.pk:
                lote.usuario = user
                lote.save(update_fields=['usuario'])
                vinculados += 1

        self.stdout.write(self.style.SUCCESS(f'Vínculos atualizados: {vinculados}'))
        if nao_encontrados:
            self.stdout.write(self.style.WARNING(f'Lotes sem usuário correspondente: {nao_encontrados}'))
