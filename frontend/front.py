import flet as ft
import requests
import time

# URL da api
API_URL = "http://127.0.0.1:5000"


#login e senha
USUARIO_DEMO = "admin"
SENHA_DEMO = "123"

def main(page: ft.Page):
    """Função principal da aplicação Flet com tela de login de demonstração."""
    page.title = "Analisador Financeiro"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER 
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 800
    page.window_height = 600 

    #Função que constrói e mostra a tela principal
    def mostrar_tela_principal():
        page.clean() 
        page.vertical_alignment = ft.MainAxisAlignment.START 
        page.window_height = 950 

        
        
        # --- Funções Lógicas da tela principal ---
        def analisar_planilha(e):
            if not selected_files.value:
                status_text.value = "Erro: Por favor, selecione um arquivo CSV primeiro."
                status_text.color = "red"
                page.update()
                return

            progress_ring.visible = True
            status_text.value = "Enviando e processando..."
            status_text.color = "orange"
            botao_analisar.disabled = True
            page.update()

            caminho_arquivo = selected_files.value[0].path
            nome_arquivo = selected_files.value[0].name
            files = {'planilha': (nome_arquivo, open(caminho_arquivo, 'rb'), 'text/csv')}

            try:
                response = requests.post(f"{API_URL}/analisar", files=files, timeout=300)
                response.raise_for_status()
                resultado = response.json()
                if resultado.get("sucesso"):
                    status_text.value = "Análise concluída com sucesso!"
                    status_text.color = "green"
                    base_url = API_URL
                    timestamp = f"?t={time.time()}"
                    grafico_barras.src = resultado['urls']['grafico_barras'] + timestamp
                    grafico_pizza.src = resultado['urls']['grafico_pizza'] + timestamp
                    link_pdf.url = resultado['urls']['pdf_completo']
                    area_resultados.visible = True
                else:
                    status_text.value = f"Erro na API: {resultado.get('erro', 'Erro desconhecido.')}"
                    status_text.color = "red"
                    area_resultados.visible = False
            except requests.exceptions.RequestException as ex:
                status_text.value = f"Erro de conexão com a API: {ex}"
                status_text.color = "red"
                area_resultados.visible = False
            finally:
                progress_ring.visible = False
                botao_analisar.disabled = False
                page.update()

        def on_files_selected(e: ft.FilePickerResultEvent):
            if e.files:
                selected_files.value = e.files
                caminho_arquivo_text.value = f"Arquivo: {e.files[0].name}"
            else:
                selected_files.value = None
                caminho_arquivo_text.value = "Nenhum arquivo selecionado."
            page.update()

        # --- Componentes da Interface Principal ---
        file_picker = ft.FilePicker(on_result=on_files_selected)
        page.overlay.append(file_picker)
        selected_files = ft.Ref()
        header = ft.Text("Relatório Financeiro a partir de CSV", size=28, weight=ft.FontWeight.BOLD)
        botao_selecionar = ft.ElevatedButton("Selecionar Planilha CSV", icon=ft.Icons.UPLOAD_FILE, on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["csv"]))
        caminho_arquivo_text = ft.Text("Nenhum arquivo selecionado.", italic=True)
        botao_analisar = ft.ElevatedButton("Analisar", on_click=analisar_planilha, icon=ft.Icons.INSIGHTS, disabled=False)
        status_text = ft.Text("", size=16)
        progress_ring = ft.ProgressRing(visible=False, width=24, height=24)
        grafico_barras = ft.Image(src="", border_radius=ft.border_radius.all(10))
        grafico_pizza = ft.Image(src="", border_radius=ft.border_radius.all(10))
        link_pdf = ft.FilledButton("Baixar Relatório PDF Completo", icon=ft.Icons.PICTURE_AS_PDF, url="")
        area_resultados = ft.Column(controls=[ft.Divider(), ft.Text("Resultados da Análise", size=22, weight=ft.FontWeight.BOLD), grafico_barras, grafico_pizza, ft.Row([link_pdf], alignment=ft.MainAxisAlignment.CENTER)], spacing=20, visible=False, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        page.add(ft.Column(controls=[header, ft.Row([botao_selecionar, caminho_arquivo_text], alignment=ft.MainAxisAlignment.CENTER, spacing=20), ft.Row([botao_analisar, progress_ring], alignment=ft.MainAxisAlignment.CENTER), ft.Container(content=status_text, padding=ft.padding.only(top=10, bottom=10)), area_resultados], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
        page.update()


    # --- Função de verificação de login ---
    def checar_login(e):
        if campo_usuario.value == USUARIO_DEMO and campo_senha.value == SENHA_DEMO:
            # Se o login estiver correto, mostra a tela principal
            mostrar_tela_principal()
        else:
            # Se estiver incorreto, mostra uma mensagem de erro
            texto_erro_login.value = "Usuário ou senha inválidos."
            page.update()

    # --- Componentes da tela de login ---
    campo_usuario = ft.TextField(label="Usuário", width=300, autofocus=True)
    campo_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300, on_submit=checar_login)
    botao_entrar = ft.ElevatedButton("Entrar", on_click=checar_login)
    texto_erro_login = ft.Text(color="red")

    # --- Visão inicial da aplicação (Tela de Login) ---
    page.add(
        ft.Column(
            [
                ft.Icon(ft.Icons.LOCK, size=48),
                ft.Text("Acesso Restrito", size=32, weight=ft.FontWeight.BOLD),
                campo_usuario,
                campo_senha,
                botao_entrar,
                texto_erro_login
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )

# Executa a aplicação Flet
if __name__ == "__main__":
    ft.app(target=main)
