# Reservas-Bela-Vista

Sistema de reserva de quiosques do condomínio Bela Vista (Rodeio/SC).

## Fluxo de bloqueio de usuário por lote

1. Admin cria o lote no painel `Admin > Lotes`.
2. O morador cria o usuário no sistema usando o padrão `lote{numero}` (exemplo: `lote29`).
3. No admin, selecione o lote e execute a ação:
   - `Vincular usuário automaticamente pelo padrão lote{numero}`.
4. Com o vínculo criado, use o botão `Bloquear` na linha do lote.
5. Quando o usuário tentar logar em `/usuarios/login/`, o sistema impede o acesso e exibe a mensagem:
   - `❌ Entre em contato com o administrador do condomínio.`
6. Para liberar o acesso novamente, use o botão `Desbloquear` no mesmo lote.

## Comando de manutenção

```bash
python manage.py repair_vinculos
```

Esse comando:
- Corrige vínculos de lotes procurando usuários pelo padrão `lote{numero_lote}`.
- Sincroniza o campo `Lote.bloqueado` com o estado atual de `User.is_active`.

## Tecnologias

- Django
- Render (deploy)
- Admin nativo do Django
