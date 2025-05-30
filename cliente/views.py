from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from .models import Cliente, Servico, Pagamento, TipoPagamento
from .forms import ClienteForm, ServicoForm
from django.utils import timezone
from django.utils.timezone import now, timedelta
from django.contrib import messages
from django.http import JsonResponse
from datetime import date
from calendar import monthrange
from django.template.loader import render_to_string
import weasyprint
from django.http import HttpResponse
from django.conf import settings
import os
from django.templatetags.static import static


def homepage(request):
    total_clientes = 0
    if request.user.is_authenticated:
        total_clientes = Cliente.objects.filter(dono=request.user).count()

    context = {
        'total_clientes': total_clientes,
    }

    return render(request, 'homepage.html', context=context)


@login_required
def cadastrar_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        nome = request.POST.get('nome')

        if Cliente.objects.filter(nome=nome, dono=request.user).exists():
            messages.error(request, 'Já existe um cliente cadastrado com este nome!')
        else:
            if form.is_valid():
                cliente = form.save(commit=False)
                cliente.dono = request.user
                cliente.save()
                messages.success(request, 'Cliente cadastrado com sucesso!')
                return redirect('cadastrar_cliente')
            else:
                messages.error(request, 'Erro ao cadastrar cliente. Verifique os campos e tente novamente.')
    else:
        form = ClienteForm()

    context = {
        'form': form,
    }
    return render(request, 'cadastro_cliente.html', context=context)


@login_required
def cadastrar_servico(request):
    if request.method == 'POST':
        form = ServicoForm(request.POST, request.FILES)
        if form.is_valid():
            servico = form.save(commit=False) # Não salva ainda
            servico.dono = request.user
            servico.data_abertura = timezone.localtime(timezone.now()) # Define o horário de Brasília
            servico.save()
            messages.success(request, 'Serviço cadastrado com sucesso!')
            return redirect('cadastrar_servico')  # Permanece na mesma página
        else:
            messages.error(request, 'Erro ao cadastrar serviço. Verifique os campos e tente novamente.')
    else:
        form = ServicoForm()

    # Filtra os clientes apenas do usuário logado
    form.fields['cliente'].queryset = Cliente.objects.filter(dono=request.user)

    context = {
        'form': form,
        'clientes': clientes,
    }

    return render(request, 'cadastro_servico.html', context=context)


@login_required
def servicos_abertos(request):
    # Apenas serviços com status 'C'
    servicos = Servico.objects.filter(status='C', dono=request.user).order_by('-id')

    context = {
        'servicos': servicos,
    }
    return render(request, 'servicos_abertos.html', context=context)


@login_required
def detalhes_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id, dono=request.user)

    if servico.dono != request.user:
        messages.error(request, 'Você não tem permissão para acessar este serviço.')
        return redirect('servicos_abertos')

    if request.method == 'POST':
        defeito_cliente = request.POST.get('defeito_cliente')
        descricao_curta = request.POST.get('descricao_curta')
        descricao_longa = request.POST.get('descricao_longa')
        acessorios = request.POST.get('acessorios')
        numero_serie = request.POST.get('numero_serie')
        preco = request.POST.get('preco')
        imagem = request.FILES.get('imagem')

        if defeito_cliente:
            servico.defeito_cliente = defeito_cliente
        if descricao_curta:
            servico.descricao_curta = descricao_curta
        if descricao_longa:
            servico.descricao_longa = descricao_longa
        if acessorios:
            servico.acessorios = acessorios
        if numero_serie:
            servico.numero_serie = numero_serie
        if preco:
            # Substituir vírgula por ponto para evitar erro
            preco = preco.replace(',', '.')
            try:
                servico.preco = float(preco)  # Converter para número decimal
            except ValueError:
                servico.preco = None  # Caso não seja um número válido
        if imagem:
            servico.imagem = imagem

        servico.save()
        messages.success(request, 'Dados do serviço atualizados com sucesso!')
        return redirect('detalhes_servico', servico_id=servico.id)

    # Verificar se todos os campos obrigatórios estão preenchidos
    servico_completo = all([
        servico.defeito_cliente,
        servico.descricao_curta,
        servico.descricao_longa,
        servico.acessorios,
        servico.numero_serie,
        servico.preco is not None
    ])

    context = {
        'servico': servico,
        'servico_completo': servico_completo,
    }
    return render(request, 'detalhes_servico.html', context=context)


@login_required
def finalizar_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id, dono=request.user)

    if request.method == "POST":
        # Verifica se todos os campos obrigatórios foram preenchidos
        if not all([
            servico.defeito_cliente,
            servico.descricao_curta,
            servico.descricao_curta,
            servico.acessorios,
            servico.numero_serie,
            servico.preco is not None
        ]):
            messages.error(request, 'Preencha todos os detalhes do serviço antes de finalizá-lo.')
            return redirect('detalhes_servico', servico_id=servico.id)

        # Se todos os campos estiverem preenchidos, permite a finalização
        # Atualiza o status para 'F' (Finalizado)
        servico.status = 'F'
        servico.data_finalizacao = timezone.now()
        servico.save()

        # Verifica se já existe um pagamento para o serviço
        pagamento, created = Pagamento.objects.get_or_create(servico=servico, defaults={'status': 'N'})

        messages.success(request, 'Serviço finalizado com sucesso!')
        return redirect('servicos_abertos')
    return redirect('servicos_abertos')


@login_required
def servicos_prontos_retirada(request):
    # Buscar serviços finalizados cujo pagamento está como 'Não Pago'
    servicos_prontos = Servico.objects.filter(status='F', pagamento__status='N', dono=request.user).exclude(id__isnull=True).order_by('-id')
    # Buscar serviços finalizados cujo pagamento está como 'Pago'
    servicos_para_retirada = Servico.objects.filter(status='F', pagamento__status='P', dono=request.user).exclude(id__isnull=True).order_by('-id')
    tipos_pagamento = TipoPagamento.objects.all()

    context = {
        'servicos_prontos': servicos_prontos,
        'servicos_para_retirada': servicos_para_retirada,
        'tipos_pagamento': tipos_pagamento,
    }

    return render(request, 'servicos_prontos_retirada.html', context=context)


@login_required
def pagar_servico(request, servico_id):  # <-- Precisa aceitar servico_id
    if request.method == 'POST':
        servico = get_object_or_404(Servico, id=servico_id, dono=request.user)

        tipo_pagamento_id = request.POST.get('tipo_pagamento')
        if not tipo_pagamento_id:
            return JsonResponse({"status": "error", "message": "Tipo de pagamento inválido"}, status=400)

        tipo_pagamento = get_object_or_404(TipoPagamento, id=tipo_pagamento_id)

        pagamento, created = Pagamento.objects.get_or_create(servico=servico)
        pagamento.tipo_pagamento = tipo_pagamento
        pagamento.status = 'P'
        pagamento.data_pagamento = timezone.now()
        pagamento.save()

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"}, status=400)


@login_required
def entregar_servico(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id, dono=request.user)

    if request.method == 'POST':
        servico.status = 'E'
        servico.data_entrega = timezone.localtime(timezone.now())
        servico.save()
        messages.success(request, 'Serviço entregue com sucesso!')

    return redirect('servicos_prontos_retirada')


@login_required
def clientes(request):
    clientes = Cliente.objects.filter(dono=request.user).order_by('nome')
    context = {
        'clientes': clientes,
    }
    return render(request, 'clientes.html', context=context)


@login_required
def listar_clientes(request):
    query = request.GET.get('q')
    clientes = Cliente.objects.filter(dono=request.user)

    if query:
        clientes = clientes.filter(nome__icontains=query)

    context = {
        'clientes': clientes,
        'query': query,
    }

    return render(request, 'clientes.html', context=context)


@login_required
def detalhes_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id, dono=request.user)

    if cliente.dono != request.user:
        raise PermissionDenied

    if request.method == "POST":
        data = request.POST.copy()
        data['nome'] = cliente.nome
        data['telefone'] = request.POST.get('telefone', cliente.telefone)  # Atualização do telefone
        data['endereco'] = request.POST.get('endereco', cliente.endereco)
        data['cidade'] = request.POST.get('cidade', cliente.cidade)
        data['estado'] = request.POST.get('estado', cliente.estado)
        data['bairro'] = request.POST.get('bairro', cliente.bairro)
        data['cep'] = request.POST.get('cep', cliente.cep)
        data['documento'] = request.POST.get('documento', cliente.documento)
        data['email'] = request.POST.get('email', cliente.email)

        form = ClienteForm(data, instance=cliente)

        if form.is_valid():
            form.save()
            messages.success(request, 'Dados do cliente atualizados com sucesso!')
            return redirect('detalhes_cliente', cliente_id=cliente.id)
        else:
            messages.error(request, 'Erro ao atualizados os dados. Verifique os campos e tente novamente!')
    else:
        form = ClienteForm(instance=cliente)

    context = {
        'cliente': cliente,
        'form': form,
    }
    return render(request, 'detalhes_cliente.html', context=context)


@login_required
def servicos_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    servicos_em_aberto = Servico.objects.filter(cliente=cliente, status='C', dono=request.user).order_by('-id')
    servicos_finalizados = Servico.objects.filter(cliente=cliente, status='F', dono=request.user).exclude(pagamento__status='P').order_by('-id')
    servicos_pagos = Servico.objects.filter(cliente=cliente, pagamento__status='P', dono=request.user).exclude(status='E').order_by('-id')
    servicos_entregues = Servico.objects.filter(cliente=cliente, status='E', dono=request.user).order_by('-id')

    # Cálculo dos totais de pagamento por método
    total_pix = Servico.objects.filter(cliente=cliente, pagamento__tipo_pagamento__tipo='P', dono=request.user).aggregate(Sum('preco'))['preco__sum'] or 0
    total_credito = Servico.objects.filter(cliente=cliente, pagamento__tipo_pagamento__tipo='CC', dono=request.user).aggregate(Sum('preco'))['preco__sum'] or 0
    total_debito = Servico.objects.filter(cliente=cliente, pagamento__tipo_pagamento__tipo='CD', dono=request.user).aggregate(Sum('preco'))['preco__sum'] or 0
    total_dinheiro = Servico.objects.filter(cliente=cliente, pagamento__tipo_pagamento__tipo='D', dono=request.user).aggregate(Sum('preco'))['preco__sum'] or 0

    context = {
        'cliente': cliente,
        'servicos_em_aberto': servicos_em_aberto,
        'servicos_finalizados': servicos_finalizados,
        'servicos_pagos': servicos_pagos,
        'servicos_entregues': servicos_entregues,
        'qtd_abertos': servicos_em_aberto.count(),
        'qtd_finalizados': servicos_finalizados.count(),
        'qtd_pagos': servicos_pagos.count(),
        'qtd_entregues': servicos_entregues.count(),
        'total_pix': total_pix,
        'total_credito': total_credito,
        'total_debito': total_debito,
        'total_dinheiro': total_dinheiro,
    }

    return render(request, 'servicos_cliente.html', context=context)


@login_required
def servicos_cliente_final(request, servico_id):
    servico = get_object_or_404(Servico, id=servico_id, dono=request.user)
    cliente = servico.cliente

    context = {
        'servico': servico,
        'cliente': cliente,
    }

    return render(request, 'servicos_cliente_final.html', context=context)


def criar_conta(request):
    if request.method == 'POST':
        dados = request.POST.dict()

        username = dados.get('username')
        email = dados.get('email')
        password = dados.get('password')
        password_confirm = dados.get('password_confirm')

        if password != password_confirm:
            messages.error(request, 'As senhas não conferem!')
            return redirect('criar_conta')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Nome de usuário já está em uso!')
            return redirect('criar_conta')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Esta e-mail já está cadastrado!')
            return redirect('criar_conta')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        login(request, user)
        messages.success(request, 'Conta criada com sucesso! Você está logado')
        return redirect('homepage')

    return render(request, 'auth/criar_conta.html')


def fazer_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('painel_usuario')
        else:
            messages.error(request, 'Usuário ou senha incorretos!')

    return render(request, 'auth/fazer_login.html')


def fazer_logout(request):
    logout(request)
    messages.success(request, 'Você saiu da sua conta com sucesso!')
    return redirect('fazer_login')


@login_required
def painel_usuario(request):
    # Mapeamento de meses
    meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    mes = int(request.GET.get('mes', date.today().month))
    ano = int(request.GET.get('ano', date.today().year))

    # Datas para filtro
    inicio_mes = date(ano, mes, 1)
    fim_mes = date(ano, mes, monthrange(ano, mes)[1])

    # Lista de anos para filtro (ex: últimos 5 anos)
    anos = list(range(date.today().year, date.today().year - 6, -1))

    # Serviços finalizados no mês selecionado
    servicos_finalizados_mes = Servico.objects.filter(dono=request.user, status='F', data_finalizacao__range=(inicio_mes, fim_mes)).count()

    hoje = now().date()
    dias_limite = 7

    # Dados gerais
    total_servicos_abertos = Servico.objects.filter(dono=request.user, status='C').count()
    total_servicos_finalizados = Servico.objects.filter(dono=request.user, status='F').count()
    total_servicos_pagos = Pagamento.objects.filter(servico__dono=request.user, status='P').count()
    total_servicos_entregues = Servico.objects.filter(dono=request.user, status='E').count()
    total_clientes = Cliente.objects.filter(dono=request.user).count()

    # Faturamento por tipo
    total_pix = Servico.objects.filter(dono=request.user, pagamento__tipo_pagamento__tipo='P').aggregate(Sum('preco'))['preco__sum'] or 0
    total_credito = Servico.objects.filter(dono=request.user, pagamento__tipo_pagamento__tipo='CC').aggregate(Sum('preco'))['preco__sum'] or 0
    total_debito = Servico.objects.filter(dono=request.user, pagamento__tipo_pagamento__tipo='CD').aggregate(Sum('preco'))['preco__sum'] or 0
    total_dinheiro = Servico.objects.filter(dono=request.user, pagamento__tipo_pagamento__tipo='D').aggregate(Sum('preco'))['preco__sum'] or 0

    # Faturamento mês
    faturamento_mes = Pagamento.objects.filter(servico__dono=request.user, status='P', data_pagamento__range=(inicio_mes, fim_mes)).aggregate(total=Sum('servico__preco'))['total'] or 0

    # Tarefas recentes
    ultimos_servicos_cadastrados = Servico.objects.filter(dono=request.user).order_by('-data_abertura')[:5]
    ultimos_servicos_finalizados = Servico.objects.filter(dono=request.user, status='F').order_by('-data_finalizacao')[:5]
    pagamentos_recentes = Pagamento.objects.filter(servico__dono=request.user).order_by('-data_pagamento')[:5]

    # Notificações e alertas
    data_limite = hoje - timedelta(days=dias_limite)
    servicos_em_aberto_mais_x_dias = Servico.objects.filter(dono=request.user, status='C', data_abertura__lt=data_limite)
    servicos_entrega_pendente = Servico.objects.filter(dono=request.user).filter(Q(status='F') | Q(status='P'))
    servicos_aguardando_pagamento = Servico.objects.filter(dono=request.user, status='F', pagamento__status='N').distinct()

    # Tabela painel
    clientes = Cliente.objects.filter(dono=request.user)
    clientes_com_servicos = Cliente.objects.filter(dono=request.user).prefetch_related('servicos')
    servicos_para_emissao_os = Servico.objects.filter(Q(status__in=['F', 'E']) | Q(pagamento__status='P'), dono=request.user).distinct().order_by('-data_abertura')

    context = {
        'total_servicos_abertos': total_servicos_abertos,
        'total_servicos_finalizados': total_servicos_finalizados,
        'total_servicos_pagos': total_servicos_pagos,
        'total_servicos_entregues': total_servicos_entregues,
        'total_clientes': total_clientes,
        'servicos_finalizados_mes': servicos_finalizados_mes,
        'total_pix': total_pix,
        'total_credito': total_credito,
        'total_debito': total_debito,
        'total_dinheiro': total_dinheiro,
        'faturamento_mes': faturamento_mes,
        'meses': meses,
        'anos': anos,
        'mes_selecionado': mes,
        'ano_selecionado': ano,
        'nome_mes_selecionado': meses[mes],
        'ultimos_servicos_cadastrados': ultimos_servicos_cadastrados,
        'ultimos_servicos_finalizados': ultimos_servicos_finalizados,
        'pagamentos_recentes': pagamentos_recentes,
        'servicos_em_aberto_mais_x_dias': servicos_em_aberto_mais_x_dias,
        'servicos_entrega_pendente': servicos_entrega_pendente,
        'servicos_aguardando_pagamento': servicos_aguardando_pagamento,
        'dias_limite': dias_limite,
        'clientes': clientes,
        'clientes_com_servicos': clientes_com_servicos,
        'servicos_para_emissao_os': servicos_para_emissao_os,
    }
    return render(request, 'painel_usuario.html', context=context)


def emitir_ordem_servico(request, servico_id):
    servico = Servico.objects.get(id=servico_id, dono=request.user)
    logo_url = request.build_absolute_uri(static('logo_final_preto.png'))

    # Renderizando o template com os dados do serviço
    html_string = render_to_string('ordem_servico.html',
                                   {'servico': servico,
                                    'logo_url': logo_url
                                    })

    # Criação do PDF
    pdf_file = weasyprint.HTML(string=html_string).write_pdf(stylesheets=[weasyprint.CSS(os.path.join(settings.BASE_DIR, 'templates/static/css/ordem_servico.css'))])

    # Criação da resposta HTTP para visualização no navegador
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="OrdemServico_{servico_id}"'
    response.write(pdf_file)
    return response