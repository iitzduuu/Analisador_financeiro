import flet as ft
import requests
import time

#url da api
API_URL = "http://127.0.0.1:5000"

def main(page: ft.Page):
    """Função principal da aplicação Flet."""
    page.title = "Analisador Financeiro"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.window_height = 900
    page.padding = 30

    # --- Funções Lógicas ---

    def analisar_planilha(e):
        """
        Função chamada ao clicar no botão 'Analisar'.
        Envia o arquivo selecionado para a API e processa a resposta.
        """
        if not selected_files.value:
            status_text.value = "Erro: Por favor, selecione um arquivo CSV primeiro."
            status_text.color = "red"
            page.update()
            return

        #exibe status de progresso
        progress_ring.visible = True
        status_text.value = "Enviando e processando... Por favor, aguarde."
        status_text.color = "orange"
        botao_analisar.disabled = True
        page.update()

        
        caminho_arquivo = selected_files.value[0].path
        nome_arquivo = selected_files.value[0].name
        
        files = {'planilha': (nome_arquivo, open(caminho_arquivo, 'rb'), 'text/csv')}

        try:
            #envia a requisição POST para a API
            response = requests.post(f"{API_URL}/analisar", files=files, timeout=300)
            response.raise_for_status()  # Lança exceção para respostas com erro (4xx ou 5xx)
            
            resultado = response.json()

            #processa a resposta da API
            if resultado.get("sucesso"):
                status_text.value = "Análise concluída com sucesso!"
                status_text.color = "green"

                # Constrói as URLs completas para os artefatos
                base_url = API_URL
                url_grafico_barras = base_url + resultado['urls']['grafico_barras']
                url_grafico_pizza = base_url + resultado['urls']['grafico_pizza']
                url_pdf = base_url + resultado['urls']['pdf_completo']

                #atualiza os componentes visuais com os resultados
                timestamp = f"?t={time.time()}"
                grafico_barras.src = url_grafico_barras + timestamp
                grafico_pizza.src = url_grafico_pizza + timestamp
                link_pdf.text = "Baixar Relatório PDF Completo"
                link_pdf.url = url_pdf
                
                area_resultados.visible = True

            else:
                #exibe mensagem de erro retornada pela API
                status_text.value = f"Erro na API: {resultado.get('erro', 'Erro desconhecido.')}"
                status_text.color = "red"
                area_resultados.visible = False

        except requests.exceptions.RequestException as ex:
            #exibe erros de conexão ou de requisição
            status_text.value = f"Erro de conexão com a API: {ex}"
            status_text.color = "red"
            area_resultados.visible = False
        finally:
            #restaura a interface para o estado inicial
            progress_ring.visible = False
            botao_analisar.disabled = False
            page.update()

    def on_files_selected(e: ft.FilePickerResultEvent):
        """Callback para quando o usuário seleciona um ou mais arquivos."""
        if e.files:
            selected_files.value = e.files
            caminho_arquivo_text.value = f"Arquivo selecionado: {e.files[0].name}"
        else:
            selected_files.value = None
            caminho_arquivo_text.value = "Nenhum arquivo selecionado."
        page.update()

    # --- Componentes da Interface ---

    file_picker = ft.FilePicker(on_result=on_files_selected)
    page.overlay.append(file_picker)
    
    selected_files = ft.Ref()

    #cabeçalho
    header = ft.Text("Relatório Financeiro a partir de CSV", size=28, weight=ft.FontWeight.BOLD)
    
    #seletor de arquivo
    botao_selecionar = ft.ElevatedButton(
        "Selecionar Planilha CSV",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["csv"]
        )
    )
    caminho_arquivo_text = ft.Text("Nenhum arquivo selecionado.", italic=True)

    #botão de análise e status
    botao_analisar = ft.ElevatedButton("Analisar", on_click=analisar_planilha, icon=ft.Icons.INSIGHTS, disabled=False)
    status_text = ft.Text("", size=16)
    progress_ring = ft.ProgressRing(visible=False, width=24, height=24)
    
    #area de resultados (inicialmente invisível)
    grafico_barras = ft.Image(src="", border_radius=ft.border_radius.all(10))
    grafico_pizza = ft.Image(src="", border_radius=ft.border_radius.all(10))
    
    # AQUI ESTÁ A ÚNICA LINHA QUE FOI ALTERADA:
    link_pdf = ft.FilledButton(text="Baixar Relatório PDF Completo", icon=ft.Icons.PICTURE_AS_PDF, url="")

    area_resultados = ft.Column(
        controls=[
            ft.Divider(),
            ft.Text("Resultados da Análise", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Balanço Mensal (Receitas vs. Despesas)"),
            grafico_barras,
            ft.Text("Distribuição Total (Receitas vs. Despesas)"),
            grafico_pizza,
            ft.Row([link_pdf], alignment=ft.MainAxisAlignment.CENTER)
        ],
        spacing=20,
        visible=False,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # --- Layout da Página ---
    
    page.add(
        ft.Column(
            controls=[
                header,
                ft.Row(
                    [botao_selecionar, caminho_arquivo_text], 
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=20
                ),
                ft.Row(
                    [botao_analisar, progress_ring], 
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(content=status_text, padding=ft.padding.only(top=10, bottom=10)),
                area_resultados
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

# executa a aplicação Flet
if __name__ == "__main__":
    ft.app(target=main)

