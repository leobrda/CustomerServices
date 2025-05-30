from django import forms
from .models import Cliente, Servico


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'endereco', 'cidade', 'estado', 'bairro', 'cep', 'documento', 'email']

    estado = forms.ChoiceField(
        choices=[('', 'Selecione um Estado')] + Cliente.ESTADO_CHOICES,
        required=False,
        label='Estado'
    )


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['cliente', 'dispositivo', 'acessorios', 'numero_serie', 'defeito_cliente', 'descricao_curta', 'descricao_longa', 'imagem', 'preco']

