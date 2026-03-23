from django.urls import path
from . import views

app_name = 'reservas_quiosques'

urlpatterns = [
    path('', views.lista_quiosques, name='lista_quiosques'),
    path('reservar/<int:quiosque_id>/', views.reservar_quiosque, name='reservar_quiosque'),
    path('criar-senha/', views.criar_senha, name='criar_senha'),
    path('minhas-reservas/', views.minhas_reservas, name='minhas_reservas'),
    path('cancelar-reserva/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),  # ✅ NOVA URL
]