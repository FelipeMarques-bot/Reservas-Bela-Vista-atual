from django.contrib import admin, messages
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


@admin.action(description='Bloquear usuários selecionados')
def bloquear_usuarios(modeladmin, request, queryset):
	total = queryset.filter(is_active=True).update(is_active=False)
	modeladmin.message_user(
		request,
		f'{total} usuário(s) bloqueado(s) com sucesso.',
		level=messages.SUCCESS,
	)


@admin.action(description='Desbloquear usuários selecionados')
def desbloquear_usuarios(modeladmin, request, queryset):
	total = queryset.filter(is_active=False).update(is_active=True)
	modeladmin.message_user(
		request,
		f'{total} usuário(s) desbloqueado(s) com sucesso.',
		level=messages.SUCCESS,
	)


class UserAdmin(BaseUserAdmin):
	list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active')
	list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
	list_editable = ('is_active',)
	actions = (bloquear_usuarios, desbloquear_usuarios)


try:
	admin.site.unregister(User)
except NotRegistered:
	pass

admin.site.register(User, UserAdmin)
