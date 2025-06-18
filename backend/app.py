import pandas as pd
import matplotlib
matplotlib.use('Agg') # Adicionei esta linha
import matplotlib.pyplot as plt # Mantenha esta linha, mas ela deve vir DEPOIS de matplotlib.use('Agg')
import seaborn as sns
from datetime import datetime
import os
from fpdf import FPDF
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import re

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

    # ... (seu método importar_csv vai aqui) ...

    def obter_dataframe(self): # <--- GARANTA QUE ESTE MÉTODO ESTÁ PRESENTE E INDENTADO CORRETAMENTE
        dados = [{'Data': t.data, 'Descrição': t.descricao, 'Valor': t.valor, 'Tipo': t.tipo()} for t in self.transacoes]
        return pd.DataFrame(dados)

    def importar_csv(self, caminho_do_arquivo):
        try:
            # Tenta ler o CSV com diferentes separadores e encodings para maior compatibilidade.
            df = None
            for sep in [',', ';']: # Tenta vírgula e ponto e vírgula como separadores
                for encoding in ['utf-8', 'latin1', 'iso-8859-1']: # Tenta encodings comuns
                    try:
                        df = pd.read_csv(caminho_do_arquivo, sep=sep, encoding=encoding)
                        if not df.empty: # Se leu algo e o DataFrame não está vazio, assume que é o correto
                            print(f"CSV lido com sucesso usando separador='{sep}' e encoding='{encoding}'.")
                            break # Sai do loop de encoding
                    except Exception:
                        continue # Tenta o próximo encoding ou separador
                if df is not None and not df.empty:
                    break # Sai do loop de separador

            if df is None or df.empty:
                raise ValueError("Não foi possível ler o arquivo CSV ou ele está vazio. Verifique o formato e o conteúdo.")

            # --- ESTRATÉGIA DE PADRONIZAÇÃO E VERIFICAÇÃO DE NOMES DE COLUNAS ---

            # Função auxiliar para normalizar nomes de coluna
            def normalize_col_name(col_name):
                s = str(col_name).lower()
                s = re.sub(r'[áàãâä]', 'a', s)
                s = re.sub(r'[éèêë]', 'e', s)
                s = re.sub(r'[íìîï]', 'i', s)
                s = re.sub(r'[óòõôö]', 'o', s)
                s = re.sub(r'[úùûü]', 'u', s)
                s = re.sub(r'[ç]', 'c', s)
                s = re.sub(r'[^a-z0-9_]', '', s) # Remove caracteres não alfanuméricos ou underscore
                s = s.strip().replace(' ', '_') # Substitui espaços por underscore e remove espaços extras
                return s

            # Cria um mapeamento de nomes normalizados para os nomes originais das colunas no DataFrame
            normalized_to_original_cols = {normalize_col_name(col): col for col in df.columns}
            
            # Define as possíveis variações normalizadas dos nomes de colunas esperados
            expected_data_cols = ['data', 'date', 'datahora', 'data_hora', 'dt']
            expected_descricao_cols = ['descricao', 'desc', 'detalhes', 'description', 'transacao']
            expected_valor_cols = ['valor', 'value', 'quantia', 'montante', 'quantia_movimentada']

            # Encontra a melhor correspondência para cada coluna essencial no CSV original
            found_data_col_original = None
            for expected_name in expected_data_cols:
                if expected_name in normalized_to_original_cols:
                    found_data_col_original = normalized_to_original_cols[expected_name]
                    break
            
            found_descricao_col_original = None
            for expected_name in expected_descricao_cols:
                if expected_name in normalized_to_original_cols:
                    found_descricao_col_original = normalized_to_original_cols[expected_name]
                    break

            found_valor_col_original = None
            for expected_name in expected_valor_cols:
                if expected_name in normalized_to_original_cols:
                    found_valor_col_original = normalized_to_original_cols[expected_name]
                    break

            # Lança um ValueError se alguma das colunas essenciais não for encontrada após a busca
            if not found_data_col_original:
                raise ValueError(f"Coluna de 'data' não encontrada. Tente usar nomes como 'Data', 'Date', 'Data/Hora'. Colunas detectadas: {list(df.columns)}")
            if not found_descricao_col_original:
                raise ValueError(f"Coluna de 'descrição' não encontrada. Tente usar nomes como 'Descrição', 'Desc', 'Detalhes'. Colunas detectadas: {list(df.columns)}")
            if not found_valor_col_original:
                raise ValueError(f"Coluna de 'valor' não encontrada. Tente usar nomes como 'Valor', 'Value', 'Quantia'. Colunas detectadas: {list(df.columns)}")
            
            # Renomeia as colunas no DataFrame para os nomes padronizados esperados pelo restante do código
            df = df.rename(columns={
                found_data_col_original: 'data',
                found_descricao_col_original: 'descricao',
                found_valor_col_original: 'valor'
            })
            
            # --- FIM DA ESTRATÉGIA DE PADRONIZAÇÃO ---

            # Limpeza e conversão dos dados linha a linha
            valid_transactions_count = 0
            for index, row in df.iterrows():
                # Tratamento da coluna 'valor': remove pontos de milhares e troca vírgula por ponto decimal
                try:
                    valor_str = str(row['valor']).strip()
                    # Remove separadores de milhares (pontos) e depois troca a vírgula decimal por ponto
                    # Ex: "1.234,56" -> "1234,56" -> "1234.56" (Formato BR)
                    valor_str = valor_str.replace('.', '').replace(',', '.')
                    valor = float(valor_str)
                except ValueError:
                    print(f"Aviso na linha {index+2} do CSV: Valor inválido '{row.get('valor', 'N/A')}' na coluna 'valor'. Esta transação será ignorada.")
                    continue # Pula a linha com valor inválido
                except TypeError: # Captura casos onde o valor pode ser NaN, None ou outro tipo inesperado
                    print(f"Aviso na linha {index+2} do CSV: Valor ausente ou tipo inválido na coluna 'valor'. Esta transação será ignorada.")
                    continue


                # Tratamento da coluna 'data': conversão para datetime, ignorando erros
                # `dayfirst=True` é essencial se suas datas estão no formato DD/MM/YYYY
                # O Pandas agora infere o formato automaticamente por padrão, e dayfirst=True
# é mantido para garantir o formato DD/MM/YYYY.
                data = pd.to_datetime(row['data'], errors='coerce')
                if pd.isna(data):
                    print(f"Aviso na linha {index+2} do CSV: Data inválida '{row.get('data', 'N/A')}' na coluna 'data'. Esta transação será ignorada.")
                    continue # Pula a linha com data inválida

                # Tratamento da coluna 'descricao': garante que seja string e fornece um valor padrão se vazia
                descricao = str(row.get('descricao', 'Sem Descrição')).strip()

                # Cria a transação e adiciona à carteira
                transacao = Receita(data, descricao, valor) if valor > 0 else Despesa(data, descricao, valor)
                self.transacoes.append(transacao)
                valid_transactions_count += 1

            if valid_transactions_count == 0:
                raise ValueError("Nenhuma transação válida foi processada a partir do CSV. Verifique o formato dos dados e a presença das colunas essenciais.")
            
            print(f"Total de {valid_transactions_count} transações válidas processadas.")

        except pd.errors.EmptyDataError:
            raise ValueError("O arquivo CSV está vazio ou contém apenas o cabeçalho.")
        except FileNotFoundError:
            raise ValueError("Erro interno: O arquivo CSV temporário não foi encontrado no servidor.")
        except Exception as e:
            # Captura outros erros inesperados durante o processamento do CSV
            raise ValueError(f"Erro inesperado ao processar o CSV: {e}. Verifique se o arquivo é um CSV válido, o separador e o encoding.")

class RelatorioFinanceiro:
    """Gera relatórios e gráficos a partir de uma carteira."""
    def __init__(self, carteira: CarteiraFinanceira, id_relatorio: str):
        self.df = carteira.obter_dataframe()
        self.id_relatorio = id_relatorio # ID único para os nomes dos arquivos
        self.pasta_saida = os.path.join(OUTPUT_FOLDER, id_relatorio)
        os.makedirs(self.pasta_saida, exist_ok=True)

    def gerar_relatorio_mensal(self):
        return self._extracted_from_gerar_graficos_3(
            "Coluna 'Data' não encontrada no DataFrame para gerar o relatório mensal."
        )

    def gerar_graficos(self):
        resumo = self._extracted_from_gerar_graficos_3(
            "Coluna 'Data' não encontrada no DataFrame para gerar gráficos."
        )
        # Gráfico de barras
        plt.figure(figsize=(10, 6))
        resumo.plot(kind='bar', stacked=False, ax=plt.gca())
        plt.title('Receitas vs Despesas por Mês')
        plt.ylabel('Valor (R$)')
        plt.xlabel('Mês')
        plt.xticks(rotation=45)
        plt.tight_layout()
        self._extracted_from_gerar_graficos_14('balanco_mensal.png')
        # Gráfico de pizza
        plt.figure(figsize=(8, 8))
        tipos = self.df.groupby('Tipo')['Valor'].sum().abs()
        tipos.plot(kind='pie', autopct='%1.1f%%', ax=plt.gca())
        plt.title('Distribuição de Receitas e Despesas')
        plt.ylabel('')
        self._extracted_from_gerar_graficos_14('distribuicao_tipos.png')
        # As URLs aqui devem ser relativas ao endpoint /relatorios/ para o Flask servir
        return f"/relatorios/{self.id_relatorio}/balanco_mensal.png", f"/relatorios/{self.id_relatorio}/distribuicao_tipos.png"

    # TODO Rename this here and in `gerar_relatorio_mensal` and `gerar_graficos`
    def _extracted_from_gerar_graficos_14(self, arg0):
        caminho_grafico_barras = os.path.join(self.pasta_saida, arg0)
        plt.savefig(caminho_grafico_barras)
        plt.close()

    # TODO Rename this here and in `gerar_relatorio_mensal` and `gerar_graficos`
    def _extracted_from_gerar_graficos_3(self, arg0):
        if 'Data' not in self.df.columns:
            raise ValueError(arg0)
        self.df['Mês'] = self.df['Data'].dt.to_period('M').astype(str)
        return self.df.groupby(['Mês', 'Tipo'])['Valor'].sum().unstack().fillna(0)

    def exportar_pdf(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=16, style='B')
        pdf.cell(200, 10, txt="Relatório Financeiro", ln=True, align='C')
        self._extracted_from_exportar_pdf_4(pdf, "Resumo Mensal")
        pdf.set_font("Arial", size=10)
        resumo = self.gerar_relatorio_mensal()
        for idx, row in resumo.iterrows():
            # Despesa é um valor negativo no df, então abs para exibir positivo
            receita = row.get('Receita', 0); despesa = row.get('Despesa', 0); saldo = receita + despesa
            linha = f"Mês {idx}: Receita: R${receita:.2f} | Despesa: R${abs(despesa):.2f} | Saldo: R${saldo:.2f}"
            pdf.cell(0, 8, txt=linha, ln=True, border=1)
        self._extracted_from_exportar_pdf_4(pdf, "Gráficos de Análise")
        for imagem in ["balanco_mensal.png", "distribuicao_tipos.png"]:
            caminho_imagem = os.path.join(self.pasta_saida, imagem)
            if os.path.exists(caminho_imagem):
                # Ajuste as coordenadas x, y e largura para a imagem caber
                pdf.image(caminho_imagem, x=15, w=180); pdf.ln(5)

        caminho_pdf = os.path.join(self.pasta_saida, 'relatorio_completo.pdf')
        pdf.output(caminho_pdf)
        return f"/relatorios/{self.id_relatorio}/relatorio_completo.pdf"

    # TODO Rename this here and in `exportar_pdf`
    def _extracted_from_exportar_pdf_4(self, pdf, txt):
        pdf.ln(10)

        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(200, 10, txt=txt, ln=True, align='L')

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
            print("Passou por importar_csv com sucesso.") # Debug Print
            
            if not carteira.transacoes:
                # Esta verificação já é feita dentro de importar_csv agora, mas mantida como segurança extra
                return jsonify({"erro": "Nenhuma transação válida encontrada na planilha após processamento."}), 400
            
            relatorio = RelatorioFinanceiro(carteira, id_unico)
            print("Objeto RelatorioFinanceiro criado.") # Debug Print
            
            resumo_mensal = relatorio.gerar_relatorio_mensal()
            print("Resumo mensal gerado.") # Debug Print
            
            grafico_barras_path, grafico_pizza_path = relatorio.gerar_graficos() # <--- Variáveis renomeadas para clareza
            print("Gráficos gerados e URLs obtidas.") # Debug Print
            
            pdf_path = relatorio.exportar_pdf() # <--- Variável renomeada para clareza
            print("PDF exportado e URL obtida.")

            base_url = request.host_url.rstrip('/') # Pega a URL base do servidor Flask (ex: http://127.0.0.1:5000)
            
            return jsonify({
                "sucesso": True,
                "resumo_mensal": resumo_mensal.to_dict(orient='index'),
                "urls": {
                    # Use nome_grafico_barras e nome_grafico_pizza diretamente com base_url
                    "grafico_barras": f"{base_url}{grafico_barras_path}", # <-- CORRIGIDO
                    "grafico_pizza": f"{base_url}{grafico_pizza_path}",   # <-- CORRIGIDO
                    "pdf_completo": f"{base_url}{pdf_path}"                # <-- CORRIGIDO
                }
            })
            
        except ValueError as e:
            print(f"ERRO DE VALIDAÇÃO (ValueError): {e}") # Debug Print
            return jsonify({"erro": str(e)}), 400
        except Exception as e:
            print(f"ERRO INTERNO GENÉRICO NO FLASK: {e}") # Debug Print
            return jsonify({"erro": f"Ocorreu um erro interno inesperado: {e}"}), 500

@app.route('/relatorios/<path:path>')
def servir_relatorio(path):
    """Endpoint para servir os arquivos gerados (gráficos e PDF)."""
    # Certifique-se de que OUTPUT_FOLDER está corretamente configurado para o diretório base
    return send_from_directory(OUTPUT_FOLDER, path)


# Executa a API Flask
if __name__ == '__main__':
    # **IMPORTANTE:** debug=False para evitar problemas de reinicialização durante o processamento de arquivos.
    app.run(debug=False, port=5000)
