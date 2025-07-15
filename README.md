# Projeto final - MATA55
Docente: Rodrigo Rocha

Discentes: Eduardo Coutinho e Atalla Silva

# 📊 Analisador Financeiro Inteligente

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.x-black.svg)
![Flet](https://img.shields.io/badge/Flet-0.28.3-green.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.x-informational.svg)

### ✨Funcionalidades principais
- **Interface Gráfica Intuitiva:** Frontend construído com Flet, fácil de usar e com um design limpo baseado em cartões.
- **API Backend:** Um servidor Flask que lida com a lógica de negócio e o processamento dos dados.
- **Leitor de CSV Inteligente:** O backend usa Pandas para ler arquivos CSV com diferentes formatos, reconhecendo variações nos nomes das colunas (ex: 'data'/'Data'), diferentes separadores e até mesmo colunas de 'Crédito' e 'Débito' separadas.
- **Geração de Gráficos:** Criação automática de gráficos de barras (Receitas vs. Despesas por Mês) e de pizza (Distribuição Total) com Matplotlib.
- **Exportação para PDF:** Geração de um relatório em PDF, incluindo o resumo mensal e os gráficos, utilizando a biblioteca FPDF.

### 🛠️ Tecnologias Utilizadas
- **Backend:** Python, Flask, Pandas, Matplotlib, FPDF, Werkzeug
- **Frontend:** Flet
- **Comunicação:** API REST (via Requests)

### 🚀 Instalação e Configuração
Para rodar este projeto em sua máquina local, siga os passos abaixo.

**1. Pré-requisitos**
- Python 3.10 ou superior
- Git (opcional, para clonar)

# Crie o ambiente (só precisa ser feito uma vez)
python -m venv venv

# Ative o ambiente no Windows
.\venv\Scripts\activate

# Em Linux/macOS, use: 
source venv/bin/activate

# Instale as dependencias 
pip install -r requirements.txt

# Acesse a pasta do backend
no seu primeiro terminal, acesse a pasta do backend: cd backend

#  Inicie o Backend (API)
 ainda no seu primeiro terminal (com o venv ativo), execute:
 python app.py

 # Abra outro terminal e acesse a pasta do Frontend (Interface Flet)

 cd frontend
 
 # Após isso execute:
 flet run front.py

### 📄 Formato do Arquivo CSV

O backend é flexível, mas para uma análise correta, o arquivo CSV deve conter as seguintes informações lógicas:

* **Data da Transação:** Uma coluna com a data de cada operação.
    * *Nomes que o sistema reconhece:* `data`, `date`.

* **Descrição da Transação:** Uma coluna com o histórico ou descrição do lançamento.
    * *Nomes que o sistema reconhece:* `descricao`, `descrição`, `historico`, `histórico`, `description`.

* **Valor da Transação:** O sistema pode lidar com duas estruturas diferentes:

    * **Opção 1: Coluna Única de Valor**
        * Uma só coluna com os valores, onde receitas são positivas (ex: `5000.00`) e despesas são negativas (ex: `-250.50`).
        * *Nomes que o sistema reconhece:* `valor`, `value`, `amount`, `montante`.
   
    * **Opção 2: Colunas Separadas de Crédito e Débito**
        * Duas colunas distintas, uma para entradas (créditos) e outra para saídas (débitos).
        * *Nomes para crédito:* `crédito`, `credito`, `credit`.
        * *Nomes para débito:* `débito`, `debito`, `debit`.

---

### 📂 Estrutura do Projeto
├── backend/

│   ├── uploads/

│   ├── relatorios_gerados/

│└── app.py             

├── frontend/

│   └── front.py             
│
├── .venv/

├── README.md

└── requirements.txt




