# 📊 Analisador Financeiro Inteligente  
**Projeto Final — MATA55**  
**Docente:** Rodrigo Rocha  
**Discentes:** Eduardo Coutinho e Atalla Silva  

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.x-black.svg)
![Flet](https://img.shields.io/badge/Flet-0.28.3-green.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.x-informational.svg)

---

## ✨ Visão Geral

O **Analisador Financeiro Inteligente** é uma aplicação completa para análise de finanças pessoais e geração de relatórios. Ele permite importar arquivos CSV com extratos bancários, realiza o processamento inteligente dos dados, gera gráficos interativos e exporta relatórios em PDF — tudo isso por meio de uma interface gráfica intuitiva.

---

## 🔧 Funcionalidades

- ✅ **Interface Gráfica Moderna:** Desenvolvida com Flet, oferecendo navegação fluida e visual agradável com componentes em cartões.
- 🔄 **API Backend:** Servidor Flask com lógica de negócio desacoplada, facilitando manutenção e escalabilidade.
- 📁 **Importação Inteligente de CSVs:** Leitura de arquivos com diferentes padrões, reconhecendo automaticamente variações de nomes de colunas, separadores e formatos.
- 📊 **Geração de Gráficos:**
  - Gráfico de barras: receitas vs. despesas por mês.
  - Gráfico de pizza: distribuição percentual das categorias.
- 🧾 **Exportação para PDF:** Geração de relatórios mensais contendo resumos financeiros e os gráficos.
  
---

## 🛠️ Tecnologias Utilizadas

| Camada       | Tecnologias |
|--------------|-------------|
| **Backend**  | Python, Flask, Pandas, Matplotlib, FPDF, Werkzeug |
| **Frontend** | Flet |
| **Comunicação** | API REST (via Requests) |

---

## 🚀 Instalação e Execução

Siga os passos abaixo para rodar o projeto localmente:

### 1. Pré-requisitos
- Python 3.10+
- Git (opcional)

### 3. Criando e Ativando o Ambiente Virtual
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalando as Dependências
```bash
pip install -r requirements.txt
```

### 5. Iniciando a Aplicação

**No primeiro terminal (Backend):**
```bash
cd backend
python app.py
```

**No segundo terminal (Frontend):**
```bash
cd frontend
flet run front.py
```

---

## 📄 Formato Esperado do Arquivo CSV

O sistema é flexível, mas para uma análise correta o CSV deve conter:

- **Data da Transação**  
  Nomes aceitos: `data`, `date`

- **Descrição da Transação**  
  Nomes aceitos: `descricao`, `descrição`, `historico`, `histórico`, `description`

- **Valor da Transação:** duas opções possíveis:

  **Opção 1: Coluna Única**
  - Valores positivos = receitas
  - Valores negativos = despesas
  - Nomes aceitos: `valor`, `value`, `amount`, `montante`

  **Opção 2: Colunas Separadas**
  - Crédito (entradas): `credito`, `crédito`, `credit`
  - Débito (saídas): `debito`, `débito`, `debit`

---

## 📁 Estrutura do Projeto

```
├── backend/
│   ├── uploads/                 # Arquivos CSV enviados
│   ├── relatorios_gerados/     # PDFs exportados
│   └── app.py                  # Servidor Flask
│
├── frontend/
│   └── front.py                # Interface Flet
│
├── requirements.txt            # Dependências do projeto
├── .venv/                      # Ambiente virtual
└── README.md                   
```

---






