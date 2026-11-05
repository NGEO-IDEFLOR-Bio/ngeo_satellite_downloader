"""
Módulo de Componentes de Interface e Exibição Visual
====================================================
Núcleo de Geotecnologias (NGEO / IDEFLOR-Bio)
Gera cartões HTML modernos, botões clicáveis de download e resumos
para o Google Colab, mantendo o padrão visual institucional do NGEO.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from IPython.display import HTML, display


def render_aoi_card(stats: Dict[str, Any]) -> None:
    """Gera cartão HTML com métricas e validação espacial do shapefile carregado."""
    b = stats.get("bounds", {})
    xmin, xmax = b.get("xmin", 0.0), b.get("xmax", 0.0)
    ymin, ymax = b.get("ymin", 0.0), b.get("ymax", 0.0)
    area_ha = stats.get("area_ha", 0.0)
    area_km2 = stats.get("area_km2", 0.0)
    pixels = stats.get("pixels", {})

    px_rows = ""
    for sensor, count in pixels.items():
        status_badge = '<span style="background-color: #27AE60; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">OK</span>' if count < 5000000 else '<span style="background-color: #E67E22; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">GRADE EM TILES</span>'
        px_rows += f"""
        <tr>
            <td style="padding: 6px 12px; border-bottom: 1px solid #E5E7E9; font-weight: 500;">{sensor}</td>
            <td style="padding: 6px 12px; border-bottom: 1px solid #E5E7E9; text-align: right; font-family: monospace;">{count:,} px</td>
            <td style="padding: 6px 12px; border-bottom: 1px solid #E5E7E9; text-align: center;">{status_badge}</td>
        </tr>
        """

    html = f"""
    <div style="background-color: #F8F9FA; border-left: 6px solid #1B4F72; border-radius: 6px; padding: 18px 24px; margin: 15px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; box-shadow: 0 2px 6px rgba(0,0,0,0.06);">
        <h3 style="margin: 0 0 10px 0; color: #1B4F72; font-size: 18px; display: flex; align-items: center; gap: 8px;">
            <span>📍</span> Área de Interesse Validada com Sucesso
        </h3>
        <p style="margin: 0 0 14px 0; color: #5D6D7E; font-size: 13px;">
            Geometria projetada para <b>WGS-84 / SIRGAS 2000 (EPSG:4326)</b>. Bounding box e dimensões operacionais:
        </p>
        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 16px;">
            <div style="background-color: #FFFFFF; border: 1px solid #D6DBDF; border-radius: 6px; padding: 10px 16px; min-width: 180px;">
                <div style="color: #7F8C8D; font-size: 11px; text-transform: uppercase; font-weight: bold;">Área Estimada</div>
                <div style="color: #2C3E50; font-size: 18px; font-weight: bold; margin-top: 4px;">{area_ha:,.1f} ha <span style="font-size: 12px; font-weight: normal; color: #7F8C8D;">({area_km2:,.2f} km²)</span></div>
            </div>
            <div style="background-color: #FFFFFF; border: 1px solid #D6DBDF; border-radius: 6px; padding: 10px 16px; min-width: 260px;">
                <div style="color: #7F8C8D; font-size: 11px; text-transform: uppercase; font-weight: bold;">Extensão Geográfica (Bounds)</div>
                <div style="color: #2C3E50; font-size: 12px; font-family: monospace; margin-top: 4px;">
                    Lon: [{xmin:.4f}, {xmax:.4f}]<br>Lat: [{ymin:.4f}, {ymax:.4f}]
                </div>
            </div>
        </div>
        <table style="width: 100%; max-width: 550px; border-collapse: collapse; background-color: #FFFFFF; border-radius: 6px; overflow: hidden; border: 1px solid #D6DBDF; font-size: 13px;">
            <thead style="background-color: #EAEDED; color: #34495E; font-weight: bold;">
                <tr>
                    <th style="padding: 8px 12px; text-align: left;">Sensor</th>
                    <th style="padding: 8px 12px; text-align: right;">Pixels Estimados</th>
                    <th style="padding: 8px 12px; text-align: center;">Estratégia</th>
                </tr>
            </thead>
            <tbody>
                {px_rows}
            </tbody>
        </table>
    </div>
    """
    display(HTML(html))


def make_download_button(filepath: str, label: str, bg_color: str = "#1B4F72", icon: str = "📥") -> str:
    """Gera um botão de download direto HTML codificado em base64 (para arquivos pequenos)."""
    p = Path(filepath)
    if not p.exists():
        return ""
    file_size_mb = p.stat().st_size / (1024 * 1024)
    # Evitar travar navegador com base64 se arquivo for muito grande (> 40MB)
    if file_size_mb > 40.0:
        return f"""
        <span style="display: inline-block; background-color: #7F8C8D; color: #FFFFFF; padding: 8px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; margin: 4px 6px 4px 0;">
            💾 {p.name} ({file_size_mb:.1f} MB no Drive)
        </span>
        """
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"""
    <a href="data:image/tiff;base64,{b64}" download="{p.name}" target="_blank"
       style="display: inline-block; background-color: {bg_color}; color: #ffffff; padding: 8px 16px;
              text-decoration: none; border-radius: 6px; font-weight: 600; font-family: Arial, sans-serif;
              font-size: 13px; margin: 4px 6px 4px 0px; box-shadow: 0 2px 4px rgba(0,0,0,0.12);">
       {icon} {label} ({file_size_mb:.1f} MB)
    </a>
    """


def render_results_cards(summary: Dict[str, Any]) -> None:
    """Exibe painel com status final das exportações e links diretos para o Google Drive."""
    sensor = summary.get("sensor", "Satélite")
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
            icon = "✅"
            badge = '<span style="color: #27AE60; font-weight: bold;">Exportação Concluída</span>'
        elif status == "SEM_IMAGEM":
            icon = "⚠️"
            badge = '<span style="color: #E67E22; font-weight: bold;">Sem Cenas no Período</span>'
        else:
            icon = "❌"
            badge = '<span style="color: #C0392B; font-weight: bold;">Falha</span>'

        files_html += f"""
        <li style="padding: 8px 12px; border-bottom: 1px solid #EBEDEF; display: flex; justify-content: space-between; align-items: center; font-size: 13px;">
            <span>{icon} <b>{filename}</b></span>
            <span>{badge}</span>
        </li>
        """

    drive_url = "https://drive.google.com/drive/u/0/my-drive"

    card_html = f"""
    <div style="background-color: #F4F6F6; border: 2px solid #1B4F72; border-radius: 8px; padding: 20px 24px; margin: 20px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #D5D8DC; padding-bottom: 12px; margin-bottom: 16px;">
            <h3 style="margin: 0; color: #154360; font-size: 19px;">
                🛰️ Relatório de Exportação — {sensor}
            </h3>
            <span style="background-color: #1B4F72; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                {success_count} / {total_ops} Sucesso
            </span>
        </div>
        <p style="color: #2C3E50; font-size: 13px; line-height: 1.5; margin: 0 0 14px 0;">
            Os arquivos GeoTIFF foram enviados para o seu Google Drive na pasta:
            <code style="background-color: #EAECEE; padding: 2px 6px; border-radius: 4px; color: #1B4F72; font-weight: bold;">
                MyDrive/{drive_folder}/{os.path.basename(area_dir)}
            </code>
        </p>
        <ul style="list-style: none; padding: 0; margin: 0 0 16px 0; background: white; border: 1px solid #D5D8DC; border-radius: 6px;">
            {files_html}
        </ul>
        <div style="margin-top: 14px;">
            <a href="{drive_url}" target="_blank"
               style="display: inline-block; background-color: #27AE60; color: #ffffff; padding: 10px 20px;
                      text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);">
                📁 Abrir Pasta no Google Drive
            </a>
        </div>
    </div>
    """
    display(HTML(card_html))
