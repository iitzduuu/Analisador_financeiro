import flet as ft
import requests
import time

API_URL = "http://127.0.0.1:5000"

# CLASSE PRINCIPAL DA APLICAÇÃO - SEM HERDAR DE USERCONTROL
class AnalisadorApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_files = ft.Ref()
        self._inicializar_componentes()
        self._construir_layout()

    def _inicializar_componentes(self):
        self.page.overlay.append(ft.FilePicker(on_result=self._on_files_selected))

        self.header = ft.Column(
            [
                ft.Icon("insights_rounded", size=42, color="#1565C0"),
                ft.Text("Analisador Financeiro Inteligente", size=32, weight=ft.FontWeight.BOLD, font_family="Roboto"),
                ft.Text("Gere relatórios e gráficos a partir de seus extratos em CSV", size=16, color="#757575")
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5
        )

        self.caminho_arquivo_text = ft.Text("Nenhum arquivo selecionado.", italic=True, color="#9E9E9E")
        self.botao_selecionar = ft.OutlinedButton(
            "Selecionar Planilha CSV",
            icon="upload_file",
            on_click=lambda _: self.page.overlay[0].pick_files(allow_multiple=False, allowed_extensions=["csv"]),
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        self.botao_analisar = ft.ElevatedButton(
            "Analisar", 
            on_click=self._analisar_planilha, 
            icon="analytics_outlined",
            bgcolor="#1976D2",
            color="white",
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
        )
        self.status_text = ft.Text(size=16)
        self.progress_bar = ft.ProgressBar(visible=False, color="#90CAF9", bgcolor="#EEEEEE")

        self.card_upload = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Row([self.botao_selecionar, self.caminho_arquivo_text], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                        ft.Divider(height=10, color="transparent"),
                        self.botao_analisar,
                        self.progress_bar,
                        self.status_text
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                padding=25
            ),
            elevation=2, shadow_color="#E0E0E0"
        )

        self.tabela_resumo = ft.DataTable(
            column_spacing=30, heading_row_color="#E3F2FD",
            columns=[
                ft.DataColumn(ft.Text("Mês", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Receitas", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Despesas", weight=ft.FontWeight.BOLD), numeric=True),
                ft.DataColumn(ft.Text("Saldo", weight=ft.FontWeight.BOLD), numeric=True),
            ],
            rows=[],
        )
        
        self.grafico_categorias = ft.PieChart(
            sections=[], sections_space=2, center_space_radius=50,
            on_chart_event=self._on_chart_event, expand=True,
        )

        self.grafico_barras = ft.Image(src="", border_radius=ft.border_radius.all(8))
        self.grafico_pizza = ft.Image(src="", border_radius=ft.border_radius.all(8))
        self.link_pdf = ft.FilledButton("Baixar Relatório PDF Completo", url="", icon="picture_as_pdf", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))

        self.card_resultados = ft.Card(
            visible=False,
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Resultados da Análise", size=22, weight=ft.FontWeight.W_600),
                        ft.Divider(height=10), self.tabela_resumo,
                        ft.Divider(height=20),
                        ft.Text("Despesas por Categoria", size=18, weight=ft.FontWeight.W_600),
                        ft.Container(content=self.grafico_categorias, height=350, padding=10),
                        ft.Divider(height=20),
                        ft.Text("Análise Geral", size=18, weight=ft.FontWeight.W_600),
                        self.grafico_barras, self.grafico_pizza,
                        ft.Divider(height=15),
                        ft.Row([self.link_pdf], alignment=ft.MainAxisAlignment.CENTER)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                padding=25, width=750
            ),
            elevation=2, shadow_color="#E0E0E0"
        )

    def _construir_layout(self):
        self.page.add(
            ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(
                       width=850,
                       controls=[
                           self.header,
                           ft.Divider(height=20, color="transparent"),
                           self.card_upload,
                           self.card_resultados
                       ]
                    )
                ]
            )
        )

    def _on_chart_event(self, e: ft.PieChartEvent):
        for idx, section in enumerate(self.grafico_categorias.sections):
            if idx == e.section_index:
                section.radius = 90
                section.border_side = ft.BorderSide(3, "#424242") # Cor para borda do gráfico
            else:
                section.radius = 80
                section.border_side = None
        self.grafico_categorias.update()

    def _on_files_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_files.current = e.files
            self.caminho_arquivo_text.value = f"Arquivo: {e.files[0].name}"
            self.caminho_arquivo_text.color = "#757575"
            self.status_text.value = ""
        else:
            self.selected_files.current = None
            self.caminho_arquivo_text.value = "Nenhum arquivo selecionado."
            self.caminho_arquivo_text.color = "#9E9E9E"
        self.page.update()

    def _analisar_planilha(self, e):
        if not self.selected_files.current:
            self.status_text.value = "Erro: Por favor, selecione um arquivo CSV primeiro."
            self.status_text.color = "#D32F2F"
            self.page.update()
            return

        self.progress_bar.visible = True
        self.botao_analisar.disabled = True
        self.status_text.value = ""
        self.tabela_resumo.rows.clear()
        self.grafico_categorias.sections.clear()
        self.card_resultados.visible = False
        self.page.update()

        caminho_arquivo = self.selected_files.current[0].path
        nome_arquivo = self.selected_files.current[0].name
        files = {'planilha': (nome_arquivo, open(caminho_arquivo, 'rb'), 'text/csv')}

        try:
            response = requests.post(f"{API_URL}/analisar", files=files, timeout=300)
            response.raise_for_status()
            resultado = response.json()

            if resultado.get("sucesso"):
                self.status_text.value = "Análise concluída com sucesso!"
                self.status_text.color = "#388E3C"

                # Preenche Tabela
                resumo_data = resultado.get("resumo_mensal", {})
                for mes, valores in resumo_data.items():
                    receita = valores.get('Receita', 0); despesa = valores.get('Despesa', 0); saldo = receita + despesa
                    self.tabela_resumo.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(mes, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(ft.Text(f"R$ {receita:,.2f}", color="#2E7D32")),
                        ft.DataCell(ft.Text(f"R$ {despesa:,.2f}", color="#C62828")),
                        ft.DataCell(ft.Text(f"R$ {saldo:,.2f}", weight=ft.FontWeight.BOLD, color="#37474F" if saldo >= 0 else "#C62828")),
                    ]))
                
                # Preenche Gráfico de Rosca
                categorias_data = resultado.get("despesas_por_categoria", {})
                cores = ["#42A5F5", "#EF5350", "#66BB6A", "#FFA726", "#AB47BC", "#8D6E63", "#EC407A", "#26A69A"]
                total_despesas = sum(categorias_data.values()) or 1

                for i, (categoria, valor) in enumerate(categorias_data.items()):
                    porcentagem = (valor / total_despesas) * 100
                    self.grafico_categorias.sections.append(
                        ft.PieChartSection(
                            value=valor, title=f"{porcentagem:.1f}%",
                            title_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, color="white"),
                            color=cores[i % len(cores)], radius=80,
                            badge=ft.Container(
                                padding=ft.padding.all(5), border_radius=ft.border_radius.all(4),
                                bgcolor="white70",
                                content=ft.Text(f"{categoria}\nR$ {valor:,.2f}", size=12, text_align=ft.TextAlign.CENTER),
                            ),
                            badge_position=1,
                        )
                    )
                
                # Atualiza Gráficos Antigos e PDF
                timestamp = f"?t={time.time()}"
                self.grafico_barras.src = f"{API_URL}{resultado['urls']['grafico_barras']}{timestamp}"
                self.grafico_pizza.src = f"{API_URL}{resultado['urls']['grafico_pizza']}{timestamp}"
                self.link_pdf.url = f"{API_URL}{resultado['urls']['pdf_completo']}"
                self.card_resultados.visible = True
            else:
                self.status_text.value = f"Erro na API: {resultado.get('erro', 'Erro desconhecido.')}"
                self.status_text.color = "#D32F2F"

        except requests.exceptions.RequestException as ex:
            self.status_text.value = f"Erro de conexão com a API: {ex}"
            self.status_text.color = "#D32F2F"
        finally:
            self.progress_bar.visible = False
            self.botao_analisar.disabled = False
            self.page.update()


def main(page: ft.Page):
    page.title = "Analisador Financeiro Inteligente"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = { "Roboto": "https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/fira_code.ttf" }
    page.theme = ft.Theme(font_family="Roboto", color_scheme_seed="#1976D2")
    
    # Apenas cria a instância da nossa classe principal.
    AnalisadorApp(page)
    
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
