from django.db import models
from PIL import Image
import os
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User


class Cliente(models.Model):
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    ESTADO_CHOICES = [
        ('AC', 'Acre'),
        ('AL', 'Alagoas'),
        ('AP', 'Amapá'),
        ('AM', 'Amazonas'),
        ('BA', 'Bahia'),
        ('CE', 'Ceará'),
        ('DF', 'Distrito Federal'),
        ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'),
        ('MA', 'Maranhão'),
        ('MT', 'Mato Grosso'),
        ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'),
        ('PA', 'Pará'),
        ('PB', 'Paraíba'),
        ('PR', 'Paraná'),
        ('PE', 'Pernambuco'),
        ('PI', 'Piauí'),
        ('RJ', 'Rio de Janeiro'),
        ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'),
        ('RO', 'Rondônia'),
        ('RR', 'Roraima'),
        ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'),
        ('SE', 'Sergipe'),
        ('TO', 'Tocantins'),
    ]

    dono = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clientes')
    nome = models.CharField(max_length=255, unique=True)
    telefone = models.CharField(max_length=20)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, choices=ESTADO_CHOICES, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cep = models.CharField(max_length=9, blank=True, null=True)
    documento = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f'{self.nome} - {self.telefone}'


class Servico(models.Model):
    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'

    STATUS_CHOICES = [
        ('C', 'Criado'),
        ('F', 'Finalizado'),
        ('E', 'Entregue')
    ]

    dono = models.ForeignKey(User, on_delete=models.CASCADE, related_name='servicos')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='servicos')
    defeito_cliente = models.CharField(max_length=1000, blank=True, null=True)
    descricao_curta = models.CharField(max_length=500, blank=True, null=True)
    descricao_longa = models.TextField(max_length=1000, blank=True, null=True)
    imagem = models.ImageField(upload_to='servicos/', null=True, blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='C', verbose_name='Status do Serviço')
    data_abertura = models.DateTimeField(default=timezone.now)
    data_finalizacao = models.DateTimeField(blank=True, null=True)
    data_entrega = models.DateTimeField(blank=True, null=True)
    dispositivo = models.CharField(max_length=255)
    acessorios = models.CharField(max_length=255, blank=True, null=True, verbose_name='Acessórios')
    numero_serie = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nº de Série')

    def __str__(self):
        return f'Cliente: {self.cliente.nome} - Dispositivo: {self.dispositivo} - Serviço: {self.descricao_curta} - Valor: {self.preco}'

    def data_abertura_formatada(self):
        # Converte a data de abertura para o horário de Brasília e formata
        return timezone.localtime(self.data_abertura).strftime('%d/%m/%Y - %H:%M')

    def data_finalizacao_formatada(self):
        # Verifica se a data de finalização existe, se sim, converte para horário de Brasília e formata
        if self.data_finalizacao:
            return timezone.localtime(self.data_finalizacao).strftime('%d/%m/%Y - %H:%M')
        return 'Ainda não finalizado'

    def data_entrega_formatada(self):
        if self.data_entrega:
            return timezone.localtime(self.data_entrega).strftime('%d/%m/%Y - %H:%M')
        return 'Ainda não entregue ou retirado'

    def redimensionar_imagem(self):
        """Redimensiona a imagem antes de salvar"""
        if self.imagem and hasattr(self.imagem, 'path'):  # Verifica se existe uma imagem válida
            imagem_caminho = self.imagem.path  # Obtém o caminho físico do arquivo

            if os.path.exists(imagem_caminho):  # Garante que o arquivo existe
                largura_alvo = 600
                altura_alvo = 800

                with Image.open(imagem_caminho) as img:
                    img.thumbnail((largura_alvo, altura_alvo), Image.LANCZOS)
                    img.save(imagem_caminho)  # Sobrescreve a imagem original

    def save(self, *args, **kwargs):
        """Chama a função de redimensionamento após salvar a imagem"""
        super().save(*args, **kwargs)  # Primeiro, salva o objeto
        self.redimensionar_imagem()  # Agora, redimensiona a imagem


class TipoPagamento(models.Model):
    STATUS_CHOICES = [
        ('P', 'PIX'),
        ('CC', 'Cartão de Crédito'),
        ('CD', 'Cartão de Débito'),
        ('D', 'Dinheiro'),
    ]
    tipo = models.CharField(max_length=2, choices=STATUS_CHOICES, unique=True)

    def __str__(self):
        return self.get_tipo_display()


class Pagamento(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pago'),
        ('N', 'Não pago'),
    ]

    servico = models.OneToOneField(Servico, on_delete=models.CASCADE, related_name='pagamento')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='N', verbose_name='Status do Pagamento')
    tipo_pagamento = models.ForeignKey(TipoPagamento, on_delete=models.SET_NULL, null=True, blank=True)
    data_pagamento = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.servico.cliente.nome} - {self.servico.descricao_curta or 'Serviço sem descrição'} - Data Pagamento: {self.data_pagamento} - {self.tipo_pagamento} - {self.get_status_display()}'

    def data_pagamento_formatada(self):
        # Verifica se a data de finalização existe, se sim, converte para horário de Brasília e formata
        if self.data_pagamento:
            return timezone.localtime(self.data_pagamento).strftime('%d/%m/%Y - %H:%M')
        return 'Ainda não pago.'
