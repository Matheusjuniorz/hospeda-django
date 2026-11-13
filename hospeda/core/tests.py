from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import hotel, quarto_reservado, quartos, usuario_admin, usuario_padrao


def cria_admin(username="dono", nome_hotel="Hotel Sol"):
    h = hotel.objects.create(nome_hotel=nome_hotel, endereco="Rua A, 1")
    u = User.objects.create_user(username, password="Senha#12345")
    usuario_admin.objects.create(user=u, nome_admin=username, hotel=h, email_admin="a@a.com", telefone_admin="+5511999999999")
    return u, h


def cria_hospede(username="ana"):
    u = User.objects.create_user(username, password="Senha#12345")
    p = usuario_padrao.objects.create(user=u, nome_usuario=username, email_usuario="h@h.com", telefone_usuario="+5511988888888")
    return u, p


class CadastroELoginTests(TestCase):
    def test_cadastro_admin_cria_login_perfil_e_hotel(self):
        r = self.client.post(reverse("cadastrar_admin"), {
            "username": "novo", "senha": "Senha#12345", "nome_admin": "Novo", "email_admin": "n@n.com",
            "telefone_admin": "11999999999", "nome_hotel": "Pousada Mar", "endereco_hotel": "Av. Mar, 10"})
        self.assertRedirects(r, reverse("login_admin"))
        perfil = User.objects.get(username="novo").perfil_admin
        self.assertEqual(perfil.hotel.nome_hotel, "Pousada Mar")

    def test_cadastro_hospede_e_username_duplicado(self):
        dados = {"username": "joao", "senha_usuario": "Senha#12345", "nome_usuario": "João",
                 "email_usuario": "j@j.com", "telefone_usuario": "11988887777"}
        self.assertRedirects(self.client.post(reverse("cadastrar_hospede"), dados), reverse("login"))
        r = self.client.post(reverse("cadastrar_hospede"), dados)
        self.assertEqual(r.status_code, 200)  # reexibe o form com erro, sem 500
        self.assertContains(r, "já está em uso")

    def test_redirecionamento_por_perfil(self):
        admin, _ = cria_admin()
        hosp, _ = cria_hospede()
        self.client.force_login(admin)
        self.assertRedirects(self.client.get(reverse("redirecionar_login")), reverse("painel_admin_hotel"))
        self.client.force_login(hosp)
        self.assertRedirects(self.client.get(reverse("redirecionar_login")), reverse("pagina_do_hospede"))

    def test_login_redireciona_conforme_perfil(self):
        cria_hospede()
        r = self.client.post(reverse("login"), {"username": "ana", "password": "Senha#12345"})
        self.assertRedirects(r, reverse("redirecionar_login"), fetch_redirect_response=False)


class PermissoesTests(TestCase):
    def test_anonimo_nao_acessa_telas_de_gestao(self):
        for nome, args in [("lista_quartos", []), ("hoteis", []), ("cadastrar_quarto", []), ("painel_admin_hotel", []),
                           ("deletar_quarto", [1]), ("deletar_hotel", []), ("reserva_quarto_vazia", []), ("pagina_do_hospede", [])]:
            r = self.client.get(reverse(nome, args=args))
            self.assertEqual(r.status_code, 302, nome)
            self.assertIn("/login", r["Location"], nome)

    def test_hospede_nao_gerencia_quartos(self):
        hosp, _ = cria_hospede()
        self.client.force_login(hosp)
        self.assertRedirects(self.client.get(reverse("cadastrar_quarto")), reverse("redirecionar_login"), fetch_redirect_response=False)

    def test_admin_nao_reserva(self):
        admin, _ = cria_admin()
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("reserva_quarto_vazia")).status_code, 302)

    def test_admin_so_mexe_no_proprio_hotel(self):
        a1, h1 = cria_admin("dono1", "Hotel 1")
        _, h2 = cria_admin("dono2", "Hotel 2")
        q2 = quartos.objects.create(nome_quarto="Q9", preco=100, hotel=h2)
        self.client.force_login(a1)
        self.assertEqual(self.client.post(reverse("deletar_quarto", args=[q2.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("editar_quarto", args=[q2.pk])).status_code, 404)
        self.assertTrue(quartos.objects.filter(pk=q2.pk).exists())

    def test_logout_exige_post(self):
        hosp, _ = cria_hospede()
        self.client.force_login(hosp)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)


class QuartosTests(TestCase):
    def test_admin_cria_edita_exclui_quarto_do_seu_hotel(self):
        admin, h = cria_admin()
        self.client.force_login(admin)
        self.client.post(reverse("cadastrar_quarto"), {"nome_quarto": "Suíte", "preco": "250.00"})
        q = quartos.objects.get()
        self.assertEqual(q.hotel, h)
        self.client.post(reverse("editar_quarto", args=[q.pk]), {"nome_quarto": "Suíte Luxo", "preco": "300.00"})
        q.refresh_from_db()
        self.assertEqual((q.nome_quarto, q.preco), ("Suíte Luxo", Decimal("300.00")))
        self.client.post(reverse("deletar_quarto", args=[q.pk]))
        self.assertFalse(quartos.objects.exists())

    def test_preco_invalido(self):
        admin, _ = cria_admin()
        self.client.force_login(admin)
        r = self.client.post(reverse("cadastrar_quarto"), {"nome_quarto": "X", "preco": "0"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(quartos.objects.exists())


class ReservaTests(TestCase):
    def setUp(self):
        _, self.h = cria_admin()
        self.q = quartos.objects.create(nome_quarto="Q1", preco=Decimal("100.00"), hotel=self.h)
        self.user, self.hosp = cria_hospede()
        self.client.force_login(self.user)
        hoje = date.today()
        self.ent, self.sai = hoje + timedelta(days=5), hoje + timedelta(days=8)

    def reserva(self, **extra):
        dados = {"quarto": self.q.pk, "data_entrada": self.ent.isoformat(), "data_saida": self.sai.isoformat()}
        dados.update(extra)
        return self.client.post(reverse("reserva_quarto", args=[self.q.pk]), dados)

    def test_reserva_ok_calcula_total_e_vincula_hospede(self):
        self.assertRedirects(self.reserva(), reverse("pagina_do_hospede"))
        r = quarto_reservado.objects.get()
        self.assertEqual((r.usuario_padrao, r.quarto, r.preco_total), (self.hosp, self.q, Decimal("300.00")))
        self.assertEqual(r.hotel, self.h)
        self.assertContains(self.client.get(reverse("pagina_do_hospede")), "R$ 300,00")

    def test_get_preseleciona_quarto(self):
        r = self.client.get(reverse("reserva_quarto", args=[self.q.pk]))
        self.assertContains(r, f'value="{self.q.pk}" selected')

    def test_datas_invalidas(self):
        self.assertEqual(self.reserva(data_saida=self.ent.isoformat()).status_code, 200)
        self.assertEqual(self.reserva(data_entrada=(date.today() - timedelta(days=1)).isoformat()).status_code, 200)
        self.assertFalse(quarto_reservado.objects.exists())

    def test_conflito_de_datas(self):
        self.reserva()
        outro, _ = cria_hospede("bia")
        self.client.force_login(outro)
        r = self.reserva(data_entrada=(self.ent + timedelta(days=1)).isoformat(), data_saida=(self.sai + timedelta(days=2)).isoformat())
        self.assertContains(r, "já está reservado")
        # sai no mesmo dia em que outro entra: permitido
        r = self.reserva(data_entrada=self.sai.isoformat(), data_saida=(self.sai + timedelta(days=1)).isoformat())
        self.assertEqual(r.status_code, 302)
        self.assertEqual(quarto_reservado.objects.count(), 2)

    def test_cancelar_so_a_propria_reserva(self):
        self.reserva()
        r = quarto_reservado.objects.get()
        outro, _ = cria_hospede("carlos")
        self.client.force_login(outro)
        self.assertEqual(self.client.post(reverse("cancelar_reserva", args=[r.pk])).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("cancelar_reserva", args=[r.pk])).status_code, 405)
        self.client.post(reverse("cancelar_reserva", args=[r.pk]))
        self.assertFalse(quarto_reservado.objects.exists())

    def test_painel_admin_mostra_reserva(self):
        self.reserva()
        admin = User.objects.get(username="dono")
        self.client.force_login(admin)
        self.assertContains(self.client.get(reverse("painel_admin_hotel")), "ana")

    def test_str_da_reserva_e_texto(self):
        self.reserva()
        self.assertIsInstance(str(quarto_reservado.objects.get()), str)
