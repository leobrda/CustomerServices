from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # Tela inicial - OK
    path('', views.homepage, name='homepage'),

    # Tela cadastro clientes - OK
    path('cadastro-cliente/', views.cadastrar_cliente, name='cadastrar_cliente'),
    # Tela cadastro servico - OK
    path('cadastro-servico/', views.cadastrar_servico, name='cadastrar_servico'),


    # Tela com cards dos serviços abertos - STATUS:CRIADO - OK
    path('servicosabertos/', views.servicos_abertos, name='servicos_abertos'),
    # Tela com detalhes de um serviço ao clicar no botão DETALHES - OK
    path('servico/<int:servico_id>/', views.detalhes_servico, name='detalhes_servico'),

    # Ao clicar no botão FINALIZAR, é redirecionado para a mesma tela (servicos_abertos) - OK
    path('servico/finalizar/<int:servico_id>/', views.finalizar_servico, name='finalizar_servico'),

    # Ao clicar no botão FINALIZAR em servicos_abertos, o serviço passa para a tela servicos_prontos_retirada.html com o STATUS:FINALIZADO e STATUS:NÃO PAGO - OK
    path('servicosprontosretirada/', views.servicos_prontos_retirada, name='servicos_prontos_retirada'),
    # Na tela servicos_prontos_retirada.html, ao clicar em PAGAR, o serviço é colocado na sessão RETIRADA com STATUS:FINALIZADO e STATUS:PAGO
    path('servico/pagar/<int:servico_id>/', views.pagar_servico, name='pagar_servico'),
    # Na tela servicos_prontos_retirada.html, ao clicar em ENTREGAR, o serviço some da tela com STATUS:ENTREGUE e STATUS:PAGO
    path('servico/entregar/<int:servico_id>/', views.entregar_servico, name='entregar_servico'),

    # CLIENTES
    path('clientes/', views.clientes, name='clientes'),
    # Tela de busca clientes
    path('busca/', views.listar_clientes, name='listar_clientes'),
    # Tela com detalhes de um cliente ao clicar no botão DETALHES - OK
    path('cliente/<int:cliente_id>/', views.detalhes_cliente, name='detalhes_cliente'),
    # Tela com todos os serviços de um mesmo cliente
    path('cliente/<int:cliente_id>/servicos/', views.servicos_cliente, name='servicos_cliente'),
    # Tela com os dados do cliente e dados do serviço
    path('servico/<int:servico_id>/detalhes/', views.servicos_cliente_final, name='servicos_cliente_final'),
    # Template com o pdf de ordem de serviço
    path('emitir_ordem_servico/<int:servico_id>/', views.emitir_ordem_servico, name='emitir_ordem_servico'),

    # Painel de usuario para novos usuarios
    path('painel/', views.painel_usuario, name='painel_usuario'),

    # Cadastro, login, logout
    path('criarconta/', views.criar_conta, name='criar_conta'),
    path('fazerlogin/', views.fazer_login, name='fazer_login'),
    path('fazerlogout/', views.fazer_logout, name='fazer_logout'),

    # Recuperação de senha
    path('senha-reset/', auth_views.PasswordResetView.as_view(template_name='auth/password_reset.html'), name='password_reset'),
    path('senha-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('senha-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('senha-reset-completo/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
]
