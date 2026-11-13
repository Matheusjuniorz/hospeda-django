from datetime import date

from django import forms
from django.contrib.auth.models import User
from django.db import transaction

from .models import hotel, quarto_reservado, quartos, usuario_admin, usuario_padrao


class _DateInput(forms.DateInput):
    input_type = "date"

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%d", **kwargs)


def _validar_username_livre(username):
    if User.objects.filter(username__iexact=username).exists():
        raise forms.ValidationError("Este nome de usuário já está em uso.")
    return username


class quartosForm(forms.ModelForm):
    class Meta:
        model = quartos
        fields = ['nome_quarto', 'preco']
        widgets = {'preco': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'})}

    def clean_preco(self):
        preco = self.cleaned_data['preco']
        if preco <= 0:
            raise forms.ValidationError("O preço deve ser maior que zero.")
        return preco


class hotelForm(forms.ModelForm):
    class Meta:
        model = hotel
        fields = ['nome_hotel', 'endereco']


class ReservaForm(forms.ModelForm):
    quarto = forms.ModelChoiceField(queryset=quartos.objects.none(), label="Quarto", empty_label="Selecione:")

    class Meta:
        model = quarto_reservado
        fields = ['quarto', 'data_entrada', 'data_saida']
        widgets = {'data_entrada': _DateInput(), 'data_saida': _DateInput()}
        labels = {'data_entrada': 'Entrada', 'data_saida': 'Saída'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quarto'].queryset = quartos.objects.filter(hotel__isnull=False).select_related('hotel')
        self.fields['quarto'].label_from_instance = lambda q: f"{q.hotel.nome_hotel} — {q.nome_quarto} (R$ {q.preco}/diária)"

    def clean(self):
        dados = super().clean()
        entrada, saida, quarto = dados.get('data_entrada'), dados.get('data_saida'), dados.get('quarto')
        if entrada and entrada < date.today():
            self.add_error('data_entrada', "A entrada não pode ser no passado.")
        if entrada and saida and saida <= entrada:
            self.add_error('data_saida', "A saída deve ser depois da entrada.")
        if entrada and saida and quarto and not self.errors:
            conflito = quarto_reservado.objects.filter(
                quarto=quarto, data_entrada__lt=saida, data_saida__gt=entrada
            ).exists()
            if conflito:
                raise forms.ValidationError("Este quarto já está reservado em parte do período escolhido.")
        return dados


class usuario_adminForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label="Nome de Usuário (Login)")
    senha = forms.CharField(widget=forms.PasswordInput(), label="Senha")
    nome_hotel = forms.CharField(max_length=100, label="Nome do Hotel")
    endereco_hotel = forms.CharField(max_length=100, label="Endereço do Hotel")

    class Meta:
        model = usuario_admin
        fields = ['nome_admin', 'email_admin', 'telefone_admin']

    def clean_username(self):
        return _validar_username_livre(self.cleaned_data['username'])

    @transaction.atomic
    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email_admin'],
            password=self.cleaned_data['senha'],
        )
        novo_hotel = hotel.objects.create(
            nome_hotel=self.cleaned_data['nome_hotel'],
            endereco=self.cleaned_data['endereco_hotel'],
        )
        perfil = super().save(commit=False)
        perfil.user = user
        perfil.hotel = novo_hotel
        if commit:
            perfil.save()
        return perfil


class usuario_padraoForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label="Nome de Usuário (Login)")
    senha_usuario = forms.CharField(widget=forms.PasswordInput(), label="Senha")

    class Meta:
        model = usuario_padrao
        fields = ['nome_usuario', 'email_usuario', 'telefone_usuario']

    def clean_username(self):
        return _validar_username_livre(self.cleaned_data['username'])

    @transaction.atomic
    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email_usuario'],
            password=self.cleaned_data['senha_usuario'],
        )
        perfil = super().save(commit=False)
        perfil.user = user
        if commit:
            perfil.save()
        return perfil
