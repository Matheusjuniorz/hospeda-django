from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (ReservaForm, hotelForm, quartosForm, usuario_adminForm,
                    usuario_padraoForm)
from .models import hotel, quarto_reservado, quartos


def admin_required(view):
    @wraps(view)
    @login_required(login_url='login_admin')
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'perfil_admin'):
            messages.error(request, "Esta área é exclusiva de administradores de hotel.")
            return redirect('redirecionar_login')
        return view(request, *args, **kwargs)
    return wrapper


def hospede_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'perfil_padrao'):
            messages.error(request, "Esta área é exclusiva de hóspedes.")
            return redirect('redirecionar_login')
        return view(request, *args, **kwargs)
    return wrapper


def home(request):
    return render(request, 'home.html')


@login_required
def redirecionar_login(request):
    if hasattr(request.user, 'perfil_admin'):
        return redirect('painel_admin_hotel')
    if hasattr(request.user, 'perfil_padrao'):
        return redirect('pagina_do_hospede')
    return redirect('/admin/')


def cadastrar_admin(request):
    form = usuario_adminForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Cadastro concluído! Entre com seu usuário e senha.")
        return redirect('login_admin')
    return render(request, 'admin/cadastro_admin.html', {'form': form})


def cadastrar_hospede(request):
    form = usuario_padraoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Cadastro concluído! Entre com seu usuário e senha.")
        return redirect('login')
    return render(request, 'usuario/cadastro_hospede.html', {'form': form})


@hospede_required
def pagina_do_hospede(request):
    hospede = request.user.perfil_padrao
    reservas = hospede.reservas.select_related('quarto', 'quarto__hotel')
    return render(request, 'usuario/pagina_hospede.html', {'hospede': hospede, 'reservas': reservas})


@login_required
def hoteis(request):
    lista = hotel.objects.prefetch_related('quartos').all()
    meu_hotel = request.user.perfil_admin.hotel if hasattr(request.user, 'perfil_admin') else None
    return render(request, 'hoteis/hoteis.html', {'hoteis': lista, 'meu_hotel': meu_hotel})


@login_required
def lista_quartos(request):
    if hasattr(request.user, 'perfil_admin'):
        lista = quartos.objects.filter(hotel=request.user.perfil_admin.hotel)
        return render(request, 'quartos/quartos.html', {'quartos': lista, 'eh_admin': True})
    lista = quartos.objects.filter(hotel__isnull=False).select_related('hotel')
    return render(request, 'quartos/quartos.html', {'quartos': lista, 'eh_admin': False})


@hospede_required
def reserva_quarto(request, pk=None):
    quarto_escolhido = get_object_or_404(quartos, pk=pk, hotel__isnull=False) if pk else None
    form = ReservaForm(request.POST or None, initial={'quarto': quarto_escolhido})
    if request.method == 'POST' and form.is_valid():
        reserva = form.save(commit=False)
        reserva.usuario_padrao = request.user.perfil_padrao
        reserva.preco_total = reserva.calcular_preco()
        reserva.save()
        total = f"{reserva.preco_total:.2f}".replace(".", ",")
        messages.success(request, f"Reserva confirmada: {reserva} — total R$ {total}.")
        return redirect('pagina_do_hospede')
    return render(request, 'quartos/reserva_quarto.html', {'form': form, 'quarto_selecionado': quarto_escolhido})


@hospede_required
@require_POST
def cancelar_reserva(request, pk):
    reserva = get_object_or_404(quarto_reservado, pk=pk, usuario_padrao=request.user.perfil_padrao)
    reserva.delete()
    messages.success(request, "Reserva cancelada.")
    return redirect('pagina_do_hospede')


@admin_required
def painel_admin_hotel(request):
    perfil = request.user.perfil_admin
    reservas = quarto_reservado.objects.filter(quarto__hotel=perfil.hotel).select_related('quarto', 'usuario_padrao')
    return render(request, 'admin/painel_admin.html', {
        'admin': perfil,
        'hotel': perfil.hotel,
        'quartos': perfil.hotel.quartos.all(),
        'reservas': reservas,
    })


@admin_required
def editar_hotel(request):
    meu_hotel = request.user.perfil_admin.hotel
    form = hotelForm(request.POST or None, instance=meu_hotel)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Dados do hotel atualizados.")
        return redirect('painel_admin_hotel')
    return render(request, 'hoteis/editar_hotel.html', {'form': form})


@admin_required
def cadastrar_quarto(request):
    form = quartosForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        quarto = form.save(commit=False)
        quarto.hotel = request.user.perfil_admin.hotel
        quarto.save()
        messages.success(request, "Quarto cadastrado.")
        return redirect('lista_quartos')
    return render(request, 'quartos/novo_quarto.html', {'form': form})


@admin_required
def editar_quarto(request, pk):
    quarto = get_object_or_404(quartos, pk=pk, hotel=request.user.perfil_admin.hotel)
    form = quartosForm(request.POST or None, instance=quarto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Quarto atualizado.")
        return redirect('lista_quartos')
    return render(request, 'quartos/editar_quarto.html', {'form': form, 'quarto': quarto})


@admin_required
def deletar_quarto(request, pk):
    objeto = get_object_or_404(quartos, pk=pk, hotel=request.user.perfil_admin.hotel)
    if request.method == 'POST':
        objeto.delete()
        messages.success(request, "Quarto excluído.")
        return redirect('lista_quartos')
    return render(request, 'quartos/confirmar_delecao_quarto.html', {'objeto': objeto})


@admin_required
def deletar_hotel(request):
    objeto = request.user.perfil_admin.hotel
    if request.method == 'POST':
        objeto.delete()
        messages.success(request, "Hotel excluído.")
        return redirect('home')
    return render(request, 'hoteis/confirmar_delecao_hotel.html', {'objeto': objeto})
