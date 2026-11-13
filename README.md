# Hospeda — Plataforma de Gerenciamento de Hotéis e Reservas

O **Hospeda** é uma aplicação web em Python com Django desenvolvida por Matheus Junior Z. para centralizar a gestão de hotéis, acomodações e reservas. Atualmente em fase de MVP, o projeto separa o sistema em dois perfis principais: proprietários (que gerenciam hotéis e quartos) e hóspedes (que consultam e solicitam reservas).

## 🛠️ Instalação Local

1. **Clone o repositório:**
   ```bash
   git clone https://github.com
   cd hospeda
   ```
2. **Configure o ambiente virtual e instale as dependências:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
   pip install -r requirements.txt # ou pip install django
   ```
3. **Execute o banco de dados e inicie o servidor:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
   Acesse em `http://127.0.0`.

##  Roadmap
* Validação de disponibilidade e prevenção de conflitos de datas.
* Filtros e busca dinâmica de hotéis e quartos.
* Melhorias na interface frontend e testes automatizados.
