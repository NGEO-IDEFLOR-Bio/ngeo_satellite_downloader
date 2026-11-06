"""
Modulo de componentes visuais para o ambiente Colab.
Nucleo de Geotecnologias (NGEO, IDEFLOR-Bio).
Estrutura paineis informativos em HTML, tabelas de controle espacial,
interface de selecao parametrica condicional e relatorios de exportacao.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List

import ee
import ipywidgets as widgets
from IPython.display import HTML, display, clear_output


def render_aoi_card(stats: Dict[str, Any]) -> None:
    """Apresenta painel institucional com os parametros geometricos da area processada."""
    b = stats.get("bounds", {})
    xmin, xmax = b.get("xmin", 0.0), b.get("xmax", 0.0)
    ymin, ymax = b.get("ymin", 0.0), b.get("ymax", 0.0)
    area_ha = stats.get("area_ha", 0.0)
    area_km2 = stats.get("area_km2", 0.0)
    pixels = stats.get("pixels", {})

    px_rows = ""
    for sensor, count in pixels.items():
        if count < 5000000:
            status_badge = '<span style="background-color: #1E7E34; color: #FFFFFF; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 600;">CONFORME</span>'
        else:
            status_badge = '<span style="background-color: #D39E00; color: #FFFFFF; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 600;">PARTICIONAMENTO EM TILES</span>'

        px_rows += f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #DEE2E6; font-weight: 500;">{sensor}</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #DEE2E6; text-align: right; font-family: monospace;">{count:,} px</td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #DEE2E6; text-align: center;">{status_badge}</td>
        </tr>
        """

    html = f"""
    <div style="background-color: #F8F9FA; border-left: 5px solid #1B4F72; border-radius: 4px; padding: 18px 22px; margin: 16px 0; font-family: Arial, sans-serif; box-shadow: 0 1px 4px rgba(0,0,0,0.08);">
        <h3 style="margin: 0 0 8px 0; color: #1B4F72; font-size: 16px; font-weight: bold; text-transform: uppercase;">
            Area de Interesse Validada
        </h3>
        <p style="margin: 0 0 14px 0; color: #495057; font-size: 13px;">
            Geometria ajustada para o sistema de coordenadas WGS-84 (EPSG:4326). Parametros territoriais calculados:
        </p>
        <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px;">
            <div style="background-color: #FFFFFF; border: 1px solid #CED4DA; border-radius: 4px; padding: 10px 14px; min-width: 170px;">
                <div style="color: #6C757D; font-size: 11px; font-weight: bold; text-transform: uppercase;">Area Total</div>
                <div style="color: #212529; font-size: 17px; font-weight: bold; margin-top: 3px;">
                    {area_ha:,.1f} ha <span style="font-size: 12px; font-weight: normal; color: #6C757D;">({area_km2:,.2f} km²)</span>
                </div>
            </div>
            <div style="background-color: #FFFFFF; border: 1px solid #CED4DA; border-radius: 4px; padding: 10px 14px; min-width: 250px;">
                <div style="color: #6C757D; font-size: 11px; font-weight: bold; text-transform: uppercase;">Coordenadas Envolventes (Bounds)</div>
                <div style="color: #212529; font-size: 12px; font-family: monospace; margin-top: 3px;">
                    Longitude: [{xmin:.4f}, {xmax:.4f}]<br>Latitude: [{ymin:.4f}, {ymax:.4f}]
                </div>
            </div>
        </div>
        <table style="width: 100%; max-width: 540px; border-collapse: collapse; background-color: #FFFFFF; border: 1px solid #CED4DA; font-size: 12px;">
            <thead style="background-color: #E9ECEF; color: #495057;">
                <tr>
                    <th style="padding: 8px 12px; text-align: left;">Sensor</th>
                    <th style="padding: 8px 12px; text-align: right;">Estimativa de Pixels</th>
                    <th style="padding: 8px 12px; text-align: center;">Estrategia Operacional</th>
                </tr>
            </thead>
            <tbody>
                {px_rows}
            </tbody>
        </table>
    </div>
    """
    display(HTML(html))


def render_results_cards(summary: Dict[str, Any]) -> None:
    """Exibe o relatorio tabular das operacoes de exportacao no Google Drive."""
    sensor = summary.get("sensor", "Satelite")
    area_dir = summary.get("area_dir", "")
    drive_folder = summary.get("drive_folder", "Satellite_Downloads")
    results = summary.get("results", [])
    success_count = summary.get("success_count", 0)
    total_ops = summary.get("total_ops", len(results))

    files_html = ""
    for r in results:
        status = r.get("status", "DESCONHECIDO")
        filename = r.get("file", "")
        if status == "OK":
            badge = '<span style="color: #1E7E34; font-weight: bold;">Concluido com sucesso</span>'
        elif status == "SEM_IMAGEM":
            badge = '<span style="color: #D39E00; font-weight: bold;">Sem cenas validas no periodo</span>'
        else:
            badge = '<span style="color: #BD2130; font-weight: bold;">Falha de processamento</span>'

        files_html += f"""
        <li style="padding: 8px 12px; border-bottom: 1px solid #DEE2E6; display: flex; justify-content: space-between; align-items: center; font-size: 12px;">
            <span style="font-family: monospace; font-size: 13px;">{filename}</span>
            <span>{badge}</span>
        </li>
        """

    drive_url = "https://drive.google.com/drive/u/0/my-drive"

    card_html = f"""
    <div style="background-color: #F8F9FA; border: 1px solid #CED4DA; border-radius: 4px; padding: 18px 22px; margin: 20px 0; font-family: Arial, sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #CED4DA; padding-bottom: 10px; margin-bottom: 14px;">
            <h3 style="margin: 0; color: #1B4F72; font-size: 16px; font-weight: bold; text-transform: uppercase;">
                Relatorio de Exportacao: {sensor}
            </h3>
            <span style="background-color: #1B4F72; color: #FFFFFF; padding: 4px 10px; border-radius: 3px; font-size: 11px; font-weight: bold;">
                {success_count} de {total_ops} processados
            </span>
        </div>
        <p style="color: #495057; font-size: 13px; line-height: 1.4; margin: 0 0 12px 0;">
            Os arquivos GeoTIFF estao sendo armazenados na pasta designada no Google Drive:
            <code style="background-color: #E9ECEF; padding: 2px 6px; border-radius: 3px; color: #1B4F72;">
                MyDrive/{drive_folder}/{os.path.basename(area_dir)}
            </code>
        </p>
        <ul style="list-style: none; padding: 0; margin: 0 0 14px 0; background: #FFFFFF; border: 1px solid #CED4DA; border-radius: 3px;">
            {files_html}
        </ul>
        <div>
            <a href="{drive_url}" target="_blank"
               style="display: inline-block; background-color: #1B4F72; color: #FFFFFF; padding: 8px 16px;
                      text-decoration: none; border-radius: 4px; font-weight: 600; font-size: 12px;">
                Acessar pasta no Google Drive
            </a>
        </div>
    </div>
    """
    display(HTML(card_html))


def create_download_panel(region: ee.Geometry, gdf: Optional[Any] = None) -> None:
    """
    Cria painel interativo condicional com selecao parametrica controlada
    e botao de disparo integrado na mesma interface.
    """
    from src.vector_ops import parse_years
    from src.exporter import run_pipeline

    # 1. Seletor de Satelite
    sat_dropdown = widgets.Dropdown(
        options=[
            ('Sentinel-2 (10m)', 'Sentinel-2 (10m)'),
            ('Landsat 5, 7, 8 e 9 (30m)', 'Landsat 5, 7, 8 e 9 (30m)'),
            ('CBERS-4A (MUX e WPM 2m)', 'CBERS-4A (MUX e WPM 2m)'),
            ('SPOT 2008 (Codigo Florestal 5m)', 'SPOT 2008 (Codigo Florestal 5m)')
        ],
        value='Sentinel-2 (10m)',
        description='Satelite:',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )

    # 2. Entrada de Anos
    years_text = widgets.Text(
        value='2024',
        description='Anos de interesse:',
        placeholder='Ex: 2024 ou 2020-2024 ou 2020, 2022, 2024',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )

    # 3. Modo Temporal
    mode_radio = widgets.RadioButtons(
        options=['Composicao por Semestre', 'Analise Anual (Meses)'],
        value='Composicao por Semestre',
        description='Modo temporal:',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )

    # 4. Seletor de Semestre (visivel apenas no modo Semestre)
    semester_dropdown = widgets.Dropdown(
        options=[
            ('1 Semestre (Jan a Jun)', '1 Semestre (Jan a Jun)'),
            ('2 Semestre (Jul a Dez)', '2 Semestre (Jul a Dez)'),
            ('Ambos os semestres', 'Ambos')
        ],
        value='Ambos',
        description='Semestre:',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )

    # 5. Seletor de Meses (visivel apenas no modo Mensal)
    month_names = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    month_checks = []
    for i, name in enumerate(month_names):
        cb = widgets.Checkbox(value=(i in [5, 6, 7]), description=name, layout=widgets.Layout(width='95px'))
        month_checks.append(cb)

    month_grid = widgets.GridBox(
        children=month_checks,
        layout=widgets.Layout(grid_template_columns='repeat(4, 95px)', grid_gap='4px', width='420px', margin='4px 0px 4px 150px')
    )
    month_container = widgets.VBox([
        widgets.HTML(value='<div style="font-size: 13px; color: #495057; font-weight: 500; margin-left: 150px; margin-bottom: 4px;">Selecione os meses da amostragem:</div>'),
        month_grid
    ])
    month_container.layout.display = 'none'

    # 6. Metodo de Composicao (opcoes fixas em lista fechada)
    method_dropdown = widgets.Dropdown(
        options=[
            ('Mediana estatistica (redutor de nuvens e ruidos)', 'median'),
            ('Melhor cena (menor cobertura de nuvens na area)', 'best')
        ],
        value='median',
        description='Metodo de composicao:',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )

    # 7. Buffer de expansao
    buffer_slider = widgets.FloatSlider(
        value=2.0,
        min=1.0,
        max=5.0,
        step=0.5,
        description='Fator de buffer:',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )

    # 8. Pasta de Destino no Google Drive
    folder_text = widgets.Text(
        value='Satellite_Downloads',
        description='Pasta Google Drive:',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )

    # 9. Credenciais INPE (visivel exclusivamente para CBERS-4A)
    inpe_email_text = widgets.Text(
        value='',
        description='E-mail INPE:',
        placeholder='usuario@dominio.gov.br',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )
    inpe_pass_text = widgets.Password(
        value='',
        description='Senha INPE:',
        placeholder='Senha de acesso ao catalogo',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )
    inpe_container = widgets.VBox([
        widgets.HTML(value='<div style="font-size: 12px; color: #1B4F72; font-weight: bold; margin-left: 150px; margin-top: 6px; margin-bottom: 4px;">Credenciais do Catalogo INPE (CBERS-4A):</div>'),
        inpe_email_text,
        inpe_pass_text
    ])
    inpe_container.layout.display = 'none'

    # 10. Atualizacao reativa condicional dos controles
    def update_visibility(*args):
        sat = sat_dropdown.value
        is_sentinel = 'Sentinel' in sat
        is_landsat = 'Landsat' in sat
        is_cbers = 'CBERS' in sat
        is_spot = 'SPOT' in sat

        # Credenciais INPE
        inpe_container.layout.display = '' if is_cbers else 'none'

        # Modo temporal
        if is_landsat or is_spot:
            mode_radio.layout.display = 'none'
        else:
            mode_radio.layout.display = ''

        # Metodo de composicao
        method_dropdown.disabled = (is_cbers or is_spot)

        # Semestre versus Meses
        if is_spot:
            semester_dropdown.layout.display = 'none'
            month_container.layout.display = 'none'
        elif is_landsat:
            semester_dropdown.layout.display = ''
            month_container.layout.display = 'none'
        else:
            if mode_radio.value == 'Composicao por Semestre':
                semester_dropdown.layout.display = ''
                month_container.layout.display = 'none'
            else:
                semester_dropdown.layout.display = 'none'
                month_container.layout.display = ''

    sat_dropdown.observe(update_visibility, names='value')
    mode_radio.observe(update_visibility, names='value')
    update_visibility()

    # 11. Botao de Disparo e Area de Execucao
    download_btn = widgets.Button(
        description='INICIAR DOWNLOAD',
        button_style='primary',
        layout=widgets.Layout(width='320px', height='44px', margin='14px 0px 8px 150px')
    )
    download_btn.style.button_color = '#1B4F72'

    progress_bar = widgets.IntProgress(
        value=0,
        min=0,
        max=100,
        description='Progresso:',
        bar_style='info',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='480px')
    )

    output_box = widgets.Output(layout=widgets.Layout(margin='12px 0px'))

    # 12. Funcao de Disparo do Download
    def on_download_click(b):
        download_btn.disabled = True
        progress_bar.value = 0
        progress_bar.bar_style = 'info'

        with output_box:
            clear_output(wait=True)

            sat = sat_dropdown.value
            years = parse_years(years_text.value)
            if not years:
                print("[ERRO] Informe ao menos um ano valido no campo de anos.")
                download_btn.disabled = False
                return

            mode = mode_radio.value
            sem = semester_dropdown.value
            selected_months = [i + 1 for i, cb in enumerate(month_checks) if cb.value]
            method = method_dropdown.value
            buffer_val = float(buffer_slider.value)
            folder_val = folder_text.value.strip() or 'Satellite_Downloads'

            inpe_email = inpe_email_text.value.strip() if 'CBERS' in sat else None
            if 'CBERS' in sat and not inpe_email:
                print("[ERRO] Informe o e-mail de acesso ao catalogo INPE para processamento CBERS.")
                download_btn.disabled = False
                return

            def on_progress(current, total, step_label):
                pct = int((current / total) * 100) if total > 0 else 0
                progress_bar.value = pct

            try:
                result = run_pipeline(
                    region=region,
                    satellite=sat,
                    years=years,
                    mode=mode,
                    semester=sem,
                    months=selected_months,
                    method=method,
                    buffer_factor=buffer_val,
                    drive_folder=folder_val,
                    inpe_email=inpe_email,
                    progress_callback=on_progress
                )
                progress_bar.value = 100
                progress_bar.bar_style = 'success'
                render_results_cards(result)
            except Exception as err:
                print(f"[FALHA NA EXECUCAO] {err}")
            finally:
                download_btn.disabled = False

    download_btn.on_click(on_download_click)

    # 13. Montagem do Painel Completo
    panel = widgets.VBox([
        widgets.HTML(value='<div style="font-size: 14px; font-weight: bold; color: #1B4F72; border-bottom: 2px solid #CED4DA; padding-bottom: 6px; margin-bottom: 12px;">PARAMETROS DE AQUISICAO E EXPORTACAO</div>'),
        sat_dropdown,
        years_text,
        mode_radio,
        semester_dropdown,
        month_container,
        method_dropdown,
        buffer_slider,
        folder_text,
        inpe_container,
        download_btn,
        progress_bar,
        output_box
    ], layout=widgets.Layout(
        background_color='#FAFAFA',
        border='1px solid #CED4DA',
        border_radius='4px',
        padding='18px 24px',
        margin='16px 0px'
    ))

    display(panel)
