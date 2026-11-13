from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class hotel(models.Model):
    nome_hotel = models.CharField(max_length=100)
    endereco = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nome_hotel} - {self.endereco}"


class quartos(models.Model):
    nome_quarto = models.CharField(max_length=20)
    preco = models.DecimalField(max_digits=8, decimal_places=2, help_text="Preço da diária")
    hotel = models.ForeignKey(hotel, on_delete=models.CASCADE, related_name="quartos", null=True, blank=True)

    def __str__(self):
        return f"{self.nome_quarto} - R$ {self.preco}"


class usuario_admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_admin')
    nome_admin = models.CharField(max_length=100)
    hotel = models.ForeignKey(hotel, on_delete=models.CASCADE, related_name="administradores")
    email_admin = models.EmailField()
    telefone_admin = PhoneNumberField(region="BR")

    def __str__(self):
        return self.nome_admin


class usuario_padrao(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_padrao')
    nome_usuario = models.CharField(max_length=100)
    email_usuario = models.EmailField()
    telefone_usuario = PhoneNumberField(region="BR")

    def __str__(self):
        return self.nome_usuario


class quarto_reservado(models.Model):
    usuario_padrao = models.ForeignKey(usuario_padrao, on_delete=models.CASCADE, related_name="reservas")
    quarto = models.ForeignKey(quartos, on_delete=models.CASCADE, related_name="reservas")
    data_entrada = models.DateField()
    data_saida = models.DateField()
    preco_total = models.DecimalField(max_digits=10, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_entrada"]

    @property
    def hotel(self):
        return self.quarto.hotel

    @property
    def noites(self):
        return (self.data_saida - self.data_entrada).days

    @property
    def ativa(self):
        return self.data_saida >= date.today()

    def calcular_preco(self):
        return Decimal(self.noites) * self.quarto.preco

    def __str__(self):
        return f"{self.quarto.nome_quarto}: {self.data_entrada:%d/%m/%Y} a {self.data_saida:%d/%m/%Y}"
