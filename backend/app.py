import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from fpdf import FPDF
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
OUTPUT_FOLDER = os.path.join(basedir, 'relatorios_gerados')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

class Transacao:
    def __init__(self, data, descricao, valor):
        self.data = pd.to_datetime(data, errors='coerce')
        self.descricao = descricao
        self.valor = float(valor)
    def tipo(self):
        return "Receita" if self.valor > 0 else "Despesa"

class Receita(Transacao): pass
class Despesa(Transacao): pass

class CarteiraFinanceira:
    def __init__(self):
        self.transacoes = []
        self.COLUNAS_ALIAS = {
            'data': ['data', 'date'],
            'descricao': ['descricao', 'descrição', 'historico', 'histórico', 'description'],
            'valor': ['valor', 'value', 'amount', 'montante'],
            'credito': ['crédito', 'credito', 'credit', 'entrada'],
            'debito': ['débito', 'debito', 'debit', 'saida', 'saída']
        }

    def _encontrar_nome_coluna(self, df_columns, aliases):
        for alias in aliases:
            if alias in df_columns:
                return alias
        return None

    def importar_csv(self, caminho_do_arquivo):
        df = None
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
            try:
                df = pd.read_csv(caminho_do_arquivo, sep=None, engine='python', encoding=encoding, skipinitialspace=True, thousands='.', decimal=',')
                if df is not None and not df.empty:
                    print(f"CSV lido com sucesso usando encoding='{encoding}'.")
                    break
            except Exception:
                continue
        
        if df is None or df.empty:
            raise ValueError("Não foi possível ler o arquivo CSV. Verifique o formato.")

        df.columns = [str(c).lower().strip() for c in df.columns]

        col_data = self._encontrar_nome_coluna(df.columns, self.COLUNAS_ALIAS['data'])
        col_desc = self._encontrar_nome_coluna(df.columns, self.COLUNAS_ALIAS['descricao'])
        col_valor = self._encontrar_nome_coluna(df.columns, self.COLUNAS_ALIAS['valor'])
        col_credito = self._encontrar_nome_coluna(df.columns, self.COLUNAS_ALIAS['credito'])
        col_debito = self._encontrar_nome_coluna(df.columns, self.COLUNAS_ALIAS['debito'])

        if not col_data or not col_desc:
            raise ValueError("Não foi possível encontrar as colunas de 'data' e 'descrição'.")

        tem_valor_unico = col_valor is not None
        tem_cred_deb = col_credito is not None and col_debito is not None

        if not tem_valor_unico and not tem_cred_deb:
            raise ValueError("Não foi possível encontrar a coluna 'valor' ou o par 'crédito'/'débito'.")

        for _, row in df.iterrows():
            try:
                data = pd.to_datetime(row[col_data], dayfirst=True, errors='coerce')
                if pd.isna(data): continue
                
                descricao = str(row.get(col_desc, 'Sem Descrição'))
                valor = 0.0

                if tem_valor_unico:
                    valor = float(row[col_valor])
                else:
                    credito = float(row.get(col_credito, 0) or 0)
                    debito = float(row.get(col_debito, 0) or 0)
                    valor = credito - debito

                self.transacoes.append(Receita(data, descricao, valor) if valor > 0 else Despesa(data, descricao, valor))
            except (ValueError, TypeError):
                continue

        if not self.transacoes:
            raise ValueError("Nenhuma transação válida foi processada.")
            
    def obter_dataframe(self):
        dados = [{'Data': t.data, 'Descrição': t.descricao, 'Valor': t.valor, 'Tipo': t.tipo()} for t in self.transacoes]
        return pd.DataFrame(dados)

class RelatorioFinanceiro:
    def __init__(self, carteira: CarteiraFinanceira, id_relatorio: str):
        self.df = carteira.obter_dataframe()
        self.id_relatorio = id_relatorio
        self.pasta_saida = os.path.join(OUTPUT_FOLDER, id_relatorio)
        os.makedirs(self.pasta_saida, exist_ok=True)

    def _get_resumo_mensal_df(self):
        if 'Data' not in self.df.columns or self.df['Data'].isnull().all():
            raise ValueError("Coluna 'Data' não encontrada ou vazia.")
        
        df_copy = self.df.copy()
        df_copy['Mês'] = df_copy['Data'].dt.to_period('M').astype(str)
        resumo = df_copy.groupby(['Mês', 'Tipo'])['Valor'].sum().unstack().fillna(0)
        # Garante que ambas as colunas existam
        if 'Receita' not in resumo: resumo['Receita'] = 0
        if 'Despesa' not in resumo: resumo['Despesa'] = 0
        return resumo

    def gerar_relatorio_mensal(self):
        return self._get_resumo_mensal_df()

    def gerar_graficos(self):
        resumo = self._get_resumo_mensal_df()

        # --- Gráfico de Barras ---
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 6))
        resumo.plot(kind='bar', stacked=False, ax=ax, color={'Despesa': '#d9534f', 'Receita': '#5cb85c'})
        ax.set_title('Receitas vs Despesas por Mês', fontsize=16)
        ax.set_ylabel('Valor (R$)', fontsize=12)
        ax.set_xlabel('Mês', fontsize=12)
        plt.xticks(rotation=45, ha="right")
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        fig.tight_layout()
        caminho_grafico_barras = os.path.join(self.pasta_saida, 'balanco_mensal.png')
        fig.savefig(caminho_grafico_barras)
        plt.close(fig)

        # --- Gráfico de Pizza ---
        fig, ax = plt.subplots(figsize=(8, 8))
        tipos = self.df.groupby('Tipo')['Valor'].sum().abs()
        if 'Receita' not in tipos: tipos['Receita'] = 0
        if 'Despesa' not in tipos: tipos['Despesa'] = 0
        
        wedges, texts, autotexts = ax.pie(tipos, autopct='%1.1f%%', colors=[ '#5cb85c', '#d9534f'], startangle=90, wedgeprops={'edgecolor': 'white', 'linewidth': 1})
        ax.legend(wedges, tipos.index, title="Tipo", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.setp(autotexts, size=10, weight="bold", color="white")
        ax.set_title('Distribuição de Receitas e Despesas', fontsize=16)
        fig.tight_layout()
        caminho_grafico_pizza = os.path.join(self.pasta_saida, 'distribuicao_tipos.png')
        fig.savefig(caminho_grafico_pizza)
        plt.close(fig)

        return f"/relatorios/{self.id_relatorio}/balanco_mensal.png", f"/relatorios/{self.id_relatorio}/distribuicao_tipos.png"

    def exportar_pdf(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16, style='B')
        pdf.cell(0, 10, txt="Relatório Financeiro", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 10, txt="Resumo Mensal", ln=True, align='L')
        pdf.set_font("Arial", size=10)
        resumo = self.gerar_relatorio_mensal()
        for idx, row in resumo.iterrows():
            receita = row.get('Receita', 0)
            despesa = row.get('Despesa', 0)
            saldo = receita + despesa
            linha = f"Mês {idx}: Receita: R${receita:,.2f} | Despesa: R${abs(despesa):,.2f} | Saldo: R${saldo:,.2f}"
            pdf.cell(0, 8, txt=linha, ln=True, border=1)
        pdf.ln(10)

        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 10, txt="Gráficos de Análise", ln=True, align='L')
        for imagem in ["balanco_mensal.png", "distribuicao_tipos.png"]:
            caminho_imagem = os.path.join(self.pasta_saida, imagem)
            if os.path.exists(caminho_imagem):
                pdf.image(caminho_imagem, w=180)
                pdf.ln(5)

        caminho_pdf = os.path.join(self.pasta_saida, 'relatorio_completo.pdf')
        pdf.output(caminho_pdf)
        return f"/relatorios/{self.id_relatorio}/relatorio_completo.pdf"

@app.route('/analisar', methods=['POST'])
def analisar_planilha():
    if 'planilha' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400
    file = request.files['planilha']
    if file.filename == '':
        return jsonify({"erro": "Nenhum arquivo selecionado."}), 400

    filename = secure_filename(file.filename)
    id_unico = str(int(datetime.now().timestamp()))
    caminho_salvo = os.path.join(UPLOAD_FOLDER, f"{id_unico}_{filename}")
    file.save(caminho_salvo)

    try:
        carteira = CarteiraFinanceira()
        carteira.importar_csv(caminho_salvo)
        relatorio = RelatorioFinanceiro(carteira, id_unico)
        resumo_mensal = relatorio.gerar_relatorio_mensal()
        url_grafico_barras, url_grafico_pizza = relatorio.gerar_graficos()
        url_pdf = relatorio.exportar_pdf()
        
        return jsonify({
            "sucesso": True,
            "resumo_mensal": resumo_mensal.to_dict(orient='index'),
            "urls": {
                "grafico_barras": url_grafico_barras,
                "grafico_pizza": url_grafico_pizza,
                "pdf_completo": url_pdf
            }
        })
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": f"Ocorreu um erro interno inesperado: {e}"}), 500

@app.route('/relatorios/<path:path>')
def servir_relatorio(path):
    return send_from_directory(OUTPUT_FOLDER, path)

if __name__ == '__main__':
    app.run(debug=False, port=5000)
