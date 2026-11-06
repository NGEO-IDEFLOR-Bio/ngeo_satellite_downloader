"""
Modulo de componentes visuais para o ambiente Colab.
Nucleo de Geotecnologias (NGEO, IDEFLOR-Bio).
Estrutura paineis informativos em HTML, tabelas de controle espacial
e resumo dos arquivos exportados.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from IPython.display import HTML, display


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


def make_download_button(filepath: str, label: str, bg_color: str = "#1B4F72") -> str:
    """Gera link formal de download para arquivos de tamanho reduzido."""
    p = Path(filepath)
    if not p.exists():
        return ""
    file_size_mb = p.stat().st_size / (1024 * 1024)
    if file_size_mb > 40.0:
        return f"""
        <span style="display: inline-block; background-color: #6C757D; color: #FFFFFF; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: 600; margin: 4px 6px 4px 0;">
            {p.name} ({file_size_mb:.1f} MB no Google Drive)
        </span>
        """
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"""
    <a href="data:image/tiff;base64,{b64}" download="{p.name}" target="_blank"
       style="display: inline-block; background-color: {bg_color}; color: #ffffff; padding: 7px 14px;
              text-decoration: none; border-radius: 4px; font-weight: 600; font-family: Arial, sans-serif;
              font-size: 12px; margin: 4px 6px 4px 0px;">
       {label} ({file_size_mb:.1f} MB)
    </a>
    """


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
