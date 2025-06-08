import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from fpdf import FPDF
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename # Para segurança no upload
import flet as ft

def main(page: ft.Page):
    pass

ft.app(target=main)


app = Flask(__name__)


UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'relatorios_gerados'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


class Transacao:
    """Representa uma única transação financeira."""
    def __init__(self, data, descricao, valor):
        self.data = pd.to_datetime(data, errors='coerce')
        self.descricao = descricao
        self.valor = float(valor)

    def tipo(self):
        return "Receita" if self.valor > 0 else "Despesa"

class Receita(Transacao):
    pass

class Despesa(Transacao):
    pass

class CarteiraFinanceira:
    """Gerencia a coleção de transações financeiras."""
    def __init__(self):
        self.transacoes = []

    def importar_csv(self, caminho_do_arquivo):
        try:
            # Especificar o separador e o encoding pode ajudar a evitar erros
            df = pd.read_csv(caminho_do_arquivo, sep=',', encoding='utf-8')
            for _, row in df.iterrows():
                valor = float(row['valor'])
                transacao = Receita(row['data'], row['descricao'], valor) if valor > 0 else Despesa(row['data'], row['descricao'], valor)
                self.transacoes.append(transacao)
        except Exception as e:
            # Se der erro, lança uma exceção para a API tratar
            raise ValueError(f"Erro ao processar o CSV: {e}")

    def obter_dataframe(self):
        dados = [{'Data': t.data, 'Descrição': t.descricao, 'Valor': t.valor, 'Tipo': t.tipo()} for t in self.transacoes]
        return pd.DataFrame(dados)

class RelatorioFinanceiro:
    """Gera relatórios e gráficos a partir de uma carteira."""
    def __init__(self, carteira: CarteiraFinanceira, id_relatorio: str):
        self.df = carteira.obter_dataframe()
        self.id_relatorio = id_relatorio # ID único para os nomes dos arquivos
        self.pasta_saida = os.path.join(OUTPUT_FOLDER, id_relatorio)
        os.makedirs(self.pasta_saida, exist_ok=True)

    def gerar_relatorio_mensal(self):
        self.df['Mês'] = self.df['Data'].dt.to_period('M').astype(str)
        resumo = self.df.groupby(['Mês', 'Tipo'])['Valor'].sum().unstack().fillna(0)
        return resumo

    def gerar_graficos(self):
        self.df['Mês'] = self.df['Data'].dt.to_period('M').astype(str)
        resumo = self.df.groupby(['Mês', 'Tipo'])['Valor'].sum().unstack().fillna(0)
        
        # Gráfico de barras
        resumo.plot(kind='bar', stacked=False, figsize=(10, 6))
        plt.title('Receitas vs Despesas por Mês')
        plt.ylabel('Valor (R$)'); plt.xlabel('Mês'); plt.xticks(rotation=45)
        plt.tight_layout()
        caminho_grafico_barras = os.path.join(self.pasta_saida, 'balanco_mensal.png')
        plt.savefig(caminho_grafico_barras)
        plt.close()

        # Gráfico de pizza
        tipos = self.df.groupby('Tipo')['Valor'].sum().abs()
        tipos.plot(kind='pie', autopct='%1.1f%%', figsize=(8, 8))
        plt.title('Distribuição de Receitas e Despesas'); plt.ylabel('')
        caminho_grafico_pizza = os.path.join(self.pasta_saida, 'distribuicao_tipos.png')
        plt.savefig(caminho_grafico_pizza)
        plt.close()
        
        return f"/relatorios/{self.id_relatorio}/balanco_mensal.png", f"/relatorios/{self.id_relatorio}/distribuicao_tipos.png"

    def exportar_pdf(self):
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", size=16, style='B')
        pdf.cell(200, 10, txt="Relatório Financeiro", ln=True, align='C'); pdf.ln(10)

        pdf.set_font("Arial", size=12, style='B'); pdf.cell(200, 10, txt="Resumo Mensal", ln=True, align='L')
        pdf.set_font("Arial", size=10)
        resumo = self.gerar_relatorio_mensal()
        for idx, row in resumo.iterrows():
            receita = row.get('Receita', 0); despesa = row.get('Despesa', 0); saldo = receita + despesa
            linha = f"Mês {idx}: Receita: R${receita:.2f} | Despesa: R${despesa:.2f} | Saldo: R${saldo:.2f}"
            pdf.cell(0, 8, txt=linha, ln=True, border=1)
        pdf.ln(10)

        pdf.set_font("Arial", size=12, style='B'); pdf.cell(200, 10, txt="Gráficos de Análise", ln=True, align='L')
        for imagem in ["balanco_mensal.png", "distribuicao_tipos.png"]:
            caminho_imagem = os.path.join(self.pasta_saida, imagem)
            if os.path.exists(caminho_imagem):
                pdf.image(caminho_imagem, w=180); pdf.ln(5)

        caminho_pdf = os.path.join(self.pasta_saida, 'relatorio_completo.pdf')
        pdf.output(caminho_pdf)
        return f"/relatorios/{self.id_relatorio}/relatorio_completo.pdf"

# --- ENDPOINTS DA API ---

@app.route('/analisar', methods=['POST'])
def analisar_planilha():
    """Endpoint principal que recebe a planilha e retorna a análise."""
    # 1. Verifica se o arquivo foi enviado
    if 'planilha' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400
    
    file = request.files['planilha']
    if file.filename == '':
        return jsonify({"erro": "Nenhum arquivo selecionado."}), 400

    if file:
        # 2. Salva o arquivo de forma segura
        filename = secure_filename(file.filename)
        # Cria um ID único para esta requisição para evitar sobreposição de arquivos
        id_unico = str(int(datetime.now().timestamp()))
        caminho_salvo = os.path.join(UPLOAD_FOLDER, f"{id_unico}_{filename}")
        file.save(caminho_salvo)

        try:
            # 3. Processa o arquivo usando suas classes
            carteira = CarteiraFinanceira()
            carteira.importar_csv(caminho_salvo)
            
            if not carteira.transacoes:
                return jsonify({"erro": "Nenhuma transação válida encontrada na planilha."}), 400
            
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
            return jsonify({"erro": f"Ocorreu um erro interno: {e}"}), 500

@app.route('/relatorios/<path:path>')
def servir_relatorio(path):
    """Endpoint para servir os arquivos gerados (gráficos e PDF)."""
    return send_from_directory(OUTPUT_FOLDER, path)


    # bloco que executa
if __name__ == '__main__':

    app.run(debug=True, port=5000)