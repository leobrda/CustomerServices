from django.contrib import admin
from .models import Cliente, Servico, Pagamento, TipoPagamento


class ServicoAdmin(admin.ModelAdmin):
    list_display = ('cliente',
                    'descricao_curta',
                    'dispositivo',
                    'data_abertura_formatada',
                    'data_finalizacao_formatada',
                    'data_entrega_formatada',
                    'status')


class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('servico',
                    'status',
                    'tipo_pagamento',
                    'data_pagamento_formatada',)


admin.site.register(Cliente)
admin.site.register(Servico, ServicoAdmin)
admin.site.register(TipoPagamento)
admin.site.register(Pagamento, PagamentoAdmin)
