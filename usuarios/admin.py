from django.contrib import admin, messages
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html
from reservas_quiosques.models import Lote


@admin.action(description='Bloquear usuários selecionados')
def bloquear_usuarios(modeladmin, request, queryset):
    total = 0
    for user in queryset:
        lote = getattr(user, 'lote', None)
        if not lote:
            expected_username = user.username.strip().lower()
            lote_numero = expected_username.replace('lote', '', 1).strip()
            lote = Lote.objects.filter(numero_lote=lote_numero).first()
        if lote and not lote.bloqueado:
            lote.bloqueado = True
            lote.save(update_fields=['bloqueado'])
            total += 1
    modeladmin.message_user(
        request,
        f'{total} usuário(s) bloqueado(s) com sucesso.',
        level=messages.SUCCESS,
    )


@admin.action(description='Desbloquear usuários selecionados')
def desbloquear_usuarios(modeladmin, request, queryset):
    total = 0
    for user in queryset:
        lote = getattr(user, 'lote', None)
        if not lote:
            expected_username = user.username.strip().lower()
            lote_numero = expected_username.replace('lote', '', 1).strip()
            lote = Lote.objects.filter(numero_lote=lote_numero).first()
        if lote and lote.bloqueado:
            lote.bloqueado = False
            lote.save(update_fields=['bloqueado'])
            total += 1
    modeladmin.message_user(
        request,
        f'{total} usuário(s) desbloqueado(s) com sucesso.',
        level=messages.SUCCESS,
    )


class UserAdmin(BaseUserAdmin):
	change_list_template = 'admin/auth/user/change_list.html'
	list_display = (
		'username',
		'first_name',
		'last_name',
		'email',
		'is_staff',
		'status_acesso',
		'acoes_acesso',
	)
	list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
	actions = (bloquear_usuarios, desbloquear_usuarios)

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path(
				'<int:user_id>/bloquear/',
				self.admin_site.admin_view(self.bloquear_usuario_view),
				name='auth_user_bloquear',
			),
			path(
				'<int:user_id>/desbloquear/',
				self.admin_site.admin_view(self.desbloquear_usuario_view),
				name='auth_user_desbloquear',
			),
		]
		return custom_urls + urls

	@admin.display(description='Status de Acesso')
	def status_acesso(self, obj):
		if obj.is_active:
			return format_html('<span class="bv-user-status is-active">Ativo</span>')
		return format_html('<span class="bv-user-status is-blocked">Bloqueado</span>')

	@admin.display(description='Ações')
	def acoes_acesso(self, obj):
		if obj.is_active:
			url = reverse('admin:auth_user_bloquear', args=[obj.pk])
			return format_html(
				'<a class="bv-user-inline-action is-block" href="{}">Bloquear</a>',
				url,
			)

		url = reverse('admin:auth_user_desbloquear', args=[obj.pk])
		return format_html(
			'<a class="bv-user-inline-action is-unblock" href="{}">Desbloquear</a>',
			url,
		)

	def bloquear_usuario_view(self, request, user_id):
		user = User.objects.filter(pk=user_id).first()
		if user:
			lote = getattr(user, 'lote', None)
			if not lote:
				expected_username = user.username.strip().lower()
				lote_numero = expected_username.replace('lote', '', 1).strip()
				lote = Lote.objects.filter(numero_lote=lote_numero).first()
			if lote and not lote.bloqueado:
				lote.bloqueado = True
				lote.save(update_fields=['bloqueado'])
				self.message_user(request, f'Usuário {user.username} bloqueado com sucesso.', level=messages.SUCCESS)
		return HttpResponseRedirect(reverse('admin:auth_user_changelist'))

	def desbloquear_usuario_view(self, request, user_id):
		user = User.objects.filter(pk=user_id).first()
		if user:
			lote = getattr(user, 'lote', None)
			if not lote:
				expected_username = user.username.strip().lower()
				lote_numero = expected_username.replace('lote', '', 1).strip()
				lote = Lote.objects.filter(numero_lote=lote_numero).first()
			if lote and lote.bloqueado:
				lote.bloqueado = False
				lote.save(update_fields=['bloqueado'])
				self.message_user(request, f'Usuário {user.username} desbloqueado com sucesso.', level=messages.SUCCESS)
		return HttpResponseRedirect(reverse('admin:auth_user_changelist'))


try:
	admin.site.unregister(User)
except NotRegistered:
	pass

admin.site.register(User, UserAdmin)
