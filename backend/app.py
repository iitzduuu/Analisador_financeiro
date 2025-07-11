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

# Caminhos de pasta robustos
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
OUTPUT_FOLDER = os.path.join(basedir, 'relatorios_gerados')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

class Transacao: # classe base que representa qualquer transação financeira
    def __init__(self, data, descricao, valor, categoria='N/A'):
        self.data = pd.to_datetime(data, errors='coerce')
        self.descricao = descricao #descreve a transação
        self.valor = float(valor) #valor da transação, pode ser + ou -
        self.categoria = categoria #classifca as transações

    def tipo(self):
        return "Receita" if self.valor > 0 else "Despesa"

# classes receita e despesas herdam de transação
class Receita(Transacao):
    pass

class Despesa(Transacao):
    pass

class CarteiraFinanceira: #armazena e categoriza as transações
    def __init__(self):
        self.transacoes = []

    def _categorizar_transacao(self, descricao: str) -> str:
        descricao = descricao.lower()
        regras = {
            'Alimentação': ['ifood', 'restaurante', 'mercado', 'lanche', 'padaria', 'super'],
            'Transporte': ['uber', '99', 'posto', 'gasolina', 'passagem', 'estacionamento'],
            'Moradia': ['aluguel', 'condominio', 'luz', 'internet', 'agua', 'conta de luz'],
            'Lazer': ['cinema', 'show', 'bar', 'spotify', 'netflix', 'disney+', 'ingresso'],
            'Saúde': ['farmacia', 'drogaria', 'medico', 'plano de saude', 'exame']
        }
        for categoria, palavras_chave in regras.items():
            if any(palavra in descricao for palavra in palavras_chave):
                return categoria
        return 'Outros'

    def obter_dataframe(self):
        dados = [{'Data': t.data, 'Descrição': t.descricao, 'Valor': t.valor, 'Tipo': t.tipo(), 'Categoria': t.categoria} for t in self.transacoes]
        return pd.DataFrame(dados)

    def importar_csv(self, caminho_do_arquivo):
        try:
            df = None
            for sep in [',', ';']:
                for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
                    try:
                        df = pd.read_csv(caminho_do_arquivo, sep=sep, encoding=encoding, skipinitialspace=True)
                        if 'data' in df.columns or 'Data' in df.columns:
                            break
                    except Exception:
                        continue
                if df is not None and not df.empty:
                    break
            
            if df is None or df.empty:
                raise ValueError("Não foi possível ler o arquivo CSV ou ele está vazio.")
            
            def normalize_col_name(col_name):
                s = str(col_name).lower().strip()
                s = re.sub(r'[áàãâä]', 'a', s); s = re.sub(r'[éèêë]', 'e', s); s = re.sub(r'[íìîï]', 'i', s); s = re.sub(r'[óòõôö]', 'o', s); s = re.sub(r'[úùûü]', 'u', s); s = re.sub(r'[ç]', 'c', s)
                s = re.sub(r'[^a-z0-9_ ]', '', s).replace(' ', '_')
                return s
            
            normalized_to_original_cols = {normalize_col_name(col): col for col in df.columns}
            def find_col(expected_list):
                for name in expected_list:
                    if name in normalized_to_original_cols: return normalized_to_original_cols[name]
                return None

            found_data_col = find_col(['data', 'date'])
            found_descricao_col = find_col(['descricao', 'historico'])
            found_valor_col = find_col(['valor', 'value', 'montante'])

            if not all([found_data_col, found_descricao_col, found_valor_col]):
                raise ValueError(f"Não foi possível encontrar as colunas essenciais. Colunas detectadas: {list(df.columns)}")

            df = df.rename(columns={found_data_col: 'data', found_descricao_col: 'descricao', found_valor_col: 'valor'})

            valid_transactions_count = 0
            for index, row in df.iterrows():
                try:
                    valor_str = str(row['valor']).strip().replace('.', '').replace(',', '.')
                    valor = float(valor_str)
                    
                    data = pd.to_datetime(row['data'], dayfirst=True, errors='coerce')
                    if pd.isna(data): continue

                    descricao = str(row.get('descricao', 'Sem Descrição')).strip()
                    categoria = self._categorizar_transacao(descricao)
                    transacao = Receita(data, descricao, valor, categoria) if valor > 0 else Despesa(data, descricao, valor, categoria)
                    
                    self.transacoes.append(transacao)
                    valid_transactions_count += 1
                except (ValueError, TypeError):
                    continue

            if valid_transactions_count == 0:
                raise ValueError("Nenhuma transação válida foi processada a partir do CSV.")

        except Exception as e:
            raise ValueError(f"Erro ao processar o CSV: {e}")

class RelatorioFinanceiro:
    def __init__(self, carteira: CarteiraFinanceira, id_relatorio: str):
        self.df = carteira.obter_dataframe()
        self.id_relatorio = id_relatorio
        self.pasta_saida = os.path.join(OUTPUT_FOLDER, id_relatorio)
        os.makedirs(self.pasta_saida, exist_ok=True)

    def _get_resumo_mensal_df(self):
        df_copy = self.df.copy()
        df_copy['Mês'] = df_copy['Data'].dt.to_period('M').astype(str)
        resumo = df_copy.groupby(['Mês', 'Tipo'])['Valor'].sum().unstack().fillna(0)
        if 'Receita' not in resumo: resumo['Receita'] = 0
        if 'Despesa' not in resumo: resumo['Despesa'] = 0
        return resumo

    def gerar_relatorio_mensal(self):
        return self._get_resumo_mensal_df()

    def gerar_resumo_categorias(self):
        despesas_df = self.df[self.df['Tipo'] == 'Despesa']
        if despesas_df.empty:
            return {}
        resumo = despesas_df.groupby('Categoria')['Valor'].sum().abs().sort_values(ascending=False)
        return resumo.to_dict()

    def gerar_kpis(self):
        if self.df.empty:
            return {'receita_total': 0, 'despesa_total': 0, 'saldo_final': 0, 'taxa_poupanca': 0}
        
        receita_total = self.df[self.df['Tipo'] == 'Receita']['Valor'].sum()
        despesa_total = self.df[self.df['Tipo'] == 'Despesa']['Valor'].sum()
        saldo_final = receita_total + despesa_total
        
        taxa_poupanca = (saldo_final / receita_total) * 100 if receita_total > 0 else 0

        return {
            'receita_total': receita_total,
            'despesa_total': despesa_total,
            'saldo_final': saldo_final,
            'taxa_poupanca': taxa_poupanca
        }

    def gerar_graficos(self):
        resumo = self._get_resumo_mensal_df()
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Gráfico de Barras
        fig, ax = plt.subplots(figsize=(10, 6))
        resumo.plot(kind='bar', stacked=False, ax=ax, color={'Despesa': '#d9534f', 'Receita': '#5cb85c'})
        ax.set_title('Receitas vs Despesas por Mês', fontsize=16)
        ax.set_ylabel('Valor (R$)', fontsize=12)
        ax.set_xlabel('Mês', fontsize=12)
        plt.xticks(rotation=45, ha="right")
        fig.tight_layout()
        caminho_grafico_barras = os.path.join(self.pasta_saida, 'balanco_mensal.png')
        fig.savefig(caminho_grafico_barras)
        plt.close(fig)

        # Gráfico de Pizza
        fig, ax = plt.subplots(figsize=(8, 8))
        tipos = self.df.groupby('Tipo')['Valor'].sum().abs()
        ax.pie(tipos, labels=tipos.index, autopct='%1.1f%%', colors=['#d9534f', '#5cb85c'], startangle=90)
        ax.set_title('Distribuição de Receitas e Despesas', fontsize=16)
        caminho_grafico_pizza = os.path.join(self.pasta_saida, 'distribuicao_tipos.png')
        fig.savefig(caminho_grafico_pizza)
        plt.close(fig)
        
        
        fig, ax = plt.subplots(figsize=(10, 7)) 
        categorias_df = self.df[self.df['Tipo'] == 'Despesa'].groupby('Categoria')['Valor'].sum().abs().sort_values()
        
        cores = plt.get_cmap('Paired')(range(len(categorias_df)))
        
        wedges, texts, autotexts = ax.pie(
            categorias_df, autopct='%1.1f%%', startangle=90, colors=cores,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )
        ax.legend(wedges, categorias_df.index, title="Categorias", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
        plt.setp(autotexts, size=10, weight="bold", color="white")
        ax.set_title('Despesas por Categoria', fontsize=16)
        
        caminho_grafico_categorias = os.path.join(self.pasta_saida, 'categorias_despesas.png')
        fig.savefig(caminho_grafico_categorias, bbox_inches='tight')
        plt.close(fig)

        return (
            f"/relatorios/{self.id_relatorio}/balanco_mensal.png",
            f"/relatorios/{self.id_relatorio}/distribuicao_tipos.png",
            f"/relatorios/{self.id_relatorio}/categorias_despesas.png"
        )

    def exportar_pdf(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16, style='B')
        pdf.cell(0, 10, txt="Relatório Financeiro Completo", ln=True, align='C')
        pdf.ln(5)

        #KPIs
        kpis = self.gerar_kpis()
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 10, txt="Resumo Geral do Período", ln=True, align='L')
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, txt=f"Receita Total: R$ {kpis['receita_total']:,.2f}", ln=True, border=1)
        pdf.cell(0, 8, txt=f"Despesa Total: R$ {abs(kpis['despesa_total']):,.2f}", ln=True, border=1)
        pdf.cell(0, 8, txt=f"Saldo Final: R$ {kpis['saldo_final']:,.2f}", ln=True, border=1)
        pdf.cell(0, 8, txt=f"Taxa de Poupança: {kpis['taxa_poupanca']:.1f}%", ln=True, border=1)
        pdf.ln(10)

        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 10, txt="Balanço Mensal", ln=True, align='L')
        pdf.set_font("Arial", size=10)
        resumo = self.gerar_relatorio_mensal()
        for idx, row in resumo.iterrows():
            receita = row.get('Receita', 0); despesa = row.get('Despesa', 0); saldo = receita + despesa
            linha = f"Mês {idx}: Receita: R${receita:,.2f} | Despesa: R${abs(despesa):,.2f} | Saldo: R${saldo:,.2f}"
            pdf.cell(0, 8, txt=linha, ln=True, border=1)
        pdf.ln(10)

        # Categoria
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 10, txt="Despesas por Categoria", ln=True, align='L')
        pdf.set_font("Arial", size=10)
        resumo_categorias = self.gerar_resumo_categorias()
        for categoria, valor in resumo_categorias.items():
            pdf.cell(0, 8, txt=f"{categoria}: R$ {valor:,.2f}", ln=True, border=1)
        pdf.ln(10)

        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 10, txt="Gráficos de Análise", ln=True, align='L')
        for imagem in ["balanco_mensal.png", "distribuicao_tipos.png", "categorias_despesas.png"]:
            caminho_imagem = os.path.join(self.pasta_saida, imagem)
            if os.path.exists(caminho_imagem):
                pdf.image(caminho_imagem, w=180)
                pdf.ln(5)

        caminho_pdf = os.path.join(self.pasta_saida, 'relatorio_completo.pdf')
        pdf.output(caminho_pdf)
        return f"/relatorios/{self.id_relatorio}/relatorio_completo.pdf"

@app.route('/analisar', methods=['POST'])
def analisar_planilha():
    if 'planilha' not in request.files: return jsonify({"erro": "Nenhum arquivo enviado."}), 400
    file = request.files['planilha']
    if file.filename == '': return jsonify({"erro": "Nenhum arquivo selecionado."}), 400

    filename = secure_filename(file.filename)
    id_unico = str(int(datetime.now().timestamp()))
    caminho_salvo = os.path.join(UPLOAD_FOLDER, f"{id_unico}_{filename}")
    file.save(caminho_salvo)

    try:
        carteira = CarteiraFinanceira()
        carteira.importar_csv(caminho_salvo)
        relatorio = RelatorioFinanceiro(carteira, id_unico)
        
        resumo_mensal = relatorio.gerar_relatorio_mensal()
        despesas_por_categoria = relatorio.gerar_resumo_categorias()
        kpis = relatorio.gerar_kpis()
        
        # MODIFICADO: Recebe os 3 caminhos de URL
        url_grafico_barras, url_grafico_pizza, url_grafico_categorias = relatorio.gerar_graficos()
        url_pdf = relatorio.exportar_pdf()
        
        return jsonify({
            "sucesso": True,
            "resumo_mensal": resumo_mensal.to_dict(orient='index'),
            "despesas_por_categoria": despesas_por_categoria,
            "kpis": kpis,
            "urls": {
                "grafico_barras": url_grafico_barras,
                "grafico_pizza": url_grafico_pizza,
                "grafico_categorias": url_grafico_categorias, # NOVO: Envia a URL do novo gráfico
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
