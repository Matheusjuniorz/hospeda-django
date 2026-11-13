"""
URL configuration for hospeda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home_raiz'),
    path('home/', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='usuario/login.html', redirect_authenticated_user=True), name='login'),
    path('login_admin/', auth_views.LoginView.as_view(template_name='admin/login_admin.html', redirect_authenticated_user=True), name='login_admin'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/admin/', views.cadastrar_admin, name='cadastrar_admin'),
    path('cadastro/hospede/', views.cadastrar_hospede, name='cadastrar_hospede'),
    path('redirecionar/', views.redirecionar_login, name='redirecionar_login'),
    path('hospede/perfil/', views.pagina_do_hospede, name='pagina_do_hospede'),
    path('reserva_quarto/', views.reserva_quarto, name='reserva_quarto_vazia'),
    path('reserva_quarto/<int:pk>/', views.reserva_quarto, name='reserva_quarto'),
    path('reserva/<int:pk>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
    path('hoteis/', views.hoteis, name='hoteis'),
    path('quartos/', views.lista_quartos, name='lista_quartos'),
    path('hotel/painel/', views.painel_admin_hotel, name='painel_admin_hotel'),
    path('hotel/editar/', views.editar_hotel, name='editar_hotel'),
    path('hotel/deletar/', views.deletar_hotel, name='deletar_hotel'),
    path('novo_quarto/', views.cadastrar_quarto, name='cadastrar_quarto'),
    path('editar_quarto/<int:pk>/', views.editar_quarto, name='editar_quarto'),
    path('deletar_quarto/<int:pk>/', views.deletar_quarto, name='deletar_quarto'),
]
