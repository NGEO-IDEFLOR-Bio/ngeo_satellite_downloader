"""
Módulo de Exportação e Execução do Pipeline
==========================================
Núcleo de Geotecnologias (NGEO / IDEFLOR-Bio)
Responsável por disparar tarefas assíncronas do GEE para o Google Drive,
fazer download em tiles quando aplicável e gerenciar o loop completo de download.
"""

import os
import time
import requests
from typing import Dict, Any, List, Optional, Callable

import ee
from src.config import MAX_PIXELS_GEE_EXPORT, DEFAULT_DRIVE_FOLDER
from src.vector_ops import expand_region, split_region_into_tiles
from src.sensors import get_sentinel_image, get_landsat_image, get_spot_2008_image
from src.cbers import get_cbers_image_inpe


def export_to_drive(
    image: ee.Image,
    description: str,
    folder: str,
    region: ee.Geometry,
    scale: int = 30
) -> ee.batch.Task:
    """Dispara uma task do Google Earth Engine para exportação GeoTIFF direta no Google Drive."""
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        region=region,
        scale=scale,
        maxPixels=MAX_PIXELS_GEE_EXPORT,
        fileFormat='GeoTIFF'
    )
    task.start()
    print(f"    [TASK INICIADA] {description} -> Pasta Drive: {folder}")
    return task


def monitor_task(task: ee.batch.Task, description: str, timeout_min: int = 30) -> bool:
    """Monitora o status de execução de uma tarefa do Earth Engine até conclusão ou erro."""
    start = time.time()
    while True:
        status = task.status()
        state = status.get('state')

        if state == 'COMPLETED':
            print(f"    [OK] Concluído com sucesso: {description}")
            return True
        elif state in ('FAILED', 'CANCELLED'):
            error_msg = status.get('error_message', 'Erro desconhecido')
            print(f"    [FALHA] Tarefa cancelada ou com erro: {error_msg}")
            return False

        elapsed = (time.time() - start) / 60
        if elapsed > timeout_min:
            print(f"    [TIMEOUT] Tempo limite atingido ({timeout_min}min). A tarefa continuará em segundo plano.")
            return False

        print(f"    [PROCESSANDO] Status: {state}... ({elapsed:.1f}min decorridos)")
        time.sleep(25)


def get_download_or_export(
    image: ee.Image,
    region: ee.Geometry,
    scale: int,
    output_path: str,
    buffer_factor: float = 2.0,
    drive_folder: str = DEFAULT_DRIVE_FOLDER,
    wait_completion: bool = True
) -> bool:
    """Exporta para o Google Drive respeitando buffer e retorna status."""
    expanded = expand_region(region, buffer_factor)
    filename = os.path.basename(output_path).replace('.tif', '')
    task = export_to_drive(image, filename, drive_folder, expanded, scale)

    if wait_completion:
        if monitor_task(task, filename):
            print(f"    [CONCLUÍDO] Arquivo registrado no Drive: {drive_folder}/{filename}.tif")
            return True
        return False
    return True


def run_pipeline(
    region: ee.Geometry,
    satellite: str,
    years: List[int],
    mode: str = "Composição por Semestre",
    semester: str = "Ambos",
    months: Optional[List[int]] = None,
    method: str = "median",
    buffer_factor: float = 2.0,
    drive_folder: str = DEFAULT_DRIVE_FOLDER,
    inpe_email: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]:
    """
    Orquestrador operacional do download de imagens orbitais.
    Itera sobre o catálogo, executa as consultas e exporta os resultados.
    """
    if months is None:
        months = [6, 7, 8]

    # Normalizar identificador do satélite
    is_sentinel = "sentinel" in satellite.lower()
    is_landsat = "landsat" in satellite.lower()
    is_cbers = "cbers" in satellite.lower()
    is_spot = "spot" in satellite.lower()

    if is_sentinel:
        scale = 10
        sat_label = "Sentinel-2"
    elif is_landsat:
        scale = 30
        sat_label = "Landsat"
    elif is_spot:
        scale = 5
        sat_label = "SPOT-2008"
    else:
        scale = 2
        sat_label = "CBERS-4A"

    # Preparar pastas de saída
    drive_root = "/content/drive/MyDrive" if os.path.exists("/content/drive/MyDrive") else "."
    output_dir = os.path.join(drive_root, drive_folder)
    os.makedirs(output_dir, exist_ok=True)

    bounds = region.bounds().coordinates().get(0).getInfo()
    xs = [pt[0] for pt in bounds]
    ys = [pt[1] for pt in bounds]
    area_label = f"Area_{min(xs):.2f}_{min(ys):.2f}_{max(xs):.2f}_{max(ys):.2f}"
    area_dir = os.path.join(output_dir, area_label)
    os.makedirs(area_dir, exist_ok=True)

    # Calcular total de passos planejados
    total_ops = 0
    for _ in years:
        if is_sentinel or is_cbers:
            if mode == "Composição por Semestre":
                total_ops += 2
            else:
                total_ops += len(months)
        elif is_landsat:
            total_ops += 1 if semester != "Ambos" else 2
        elif is_spot:
            total_ops += 1

    current_op = 0
    results_list = []

    print(f"\n=======================================================")
    print(f" 🛰️ INICIANDO OPERAÇÃO DE AQUISIÇÃO ORBITAL")
    print(f" • Sensor: {sat_label} ({scale}m)")
    print(f" • Anos selecionados: {years}")
    print(f" • Modo: {mode}")
    print(f" • Buffer de expansão: {buffer_factor}x | Método: {method}")
    print(f" • Pasta de destino no Google Drive: {drive_folder}/{area_label}")
    print(f" • Total de operações previstas: {total_ops}")
    print(f"=======================================================\n")

    for year in years:
        print(f"\n--- [ANO {year}] ---")

        if is_sentinel:
            if mode == "Composição por Semestre":
                for sem in [1, 2]:
                    current_op += 1
                    start_m, end_m = (1, 6) if sem == 1 else (7, 12)
                    filename = f"Sentinel_{year}_S{sem}.tif"
                    filepath = os.path.join(area_dir, filename)
                    print(f"  -> Sentinel-2 {year} S{sem} (Meses {start_m:02d}-{end_m:02d})...")

                    img = get_sentinel_image(region, year, start_m, end_m, method=method)
                    if img:
                        success = get_download_or_export(img, region, scale, filepath, buffer_factor, drive_folder)
                        results_list.append({"file": filename, "status": "OK" if success else "ERRO", "year": year, "sem": sem})
                    else:
                        print("  [AVISO] Nenhuma imagem Sentinel-2 atendeu aos filtros na ROI.")
                        results_list.append({"file": filename, "status": "SEM_IMAGEM", "year": year, "sem": sem})

                    if progress_callback:
                        progress_callback(current_op, total_ops, f"Sentinel {year} S{sem}")

            else:
                for month in months:
                    current_op += 1
                    filename = f"Sentinel_{year}_{month:02d}.tif"
                    filepath = os.path.join(area_dir, filename)
                    print(f"  -> Sentinel-2 {year} Mês {month:02d}...")

                    img = get_sentinel_image(region, year, month, month, method=method)
                    if img:
                        success = get_download_or_export(img, region, scale, filepath, buffer_factor, drive_folder)
                        results_list.append({"file": filename, "status": "OK" if success else "ERRO", "year": year, "month": month})
                    else:
                        print(f"  [AVISO] Nenhuma imagem Sentinel-2 para o mês {month:02d}.")
                        results_list.append({"file": filename, "status": "SEM_IMAGEM", "year": year, "month": month})

                    if progress_callback:
                        progress_callback(current_op, total_ops, f"Sentinel {year}-{month:02d}")

        elif is_landsat:
            semesters = [1] if "1º" in semester else [2] if "2º" in semester else [1, 2]
            for sem in semesters:
                current_op += 1
                filename = f"Landsat_{year}_S{sem}.tif"
                filepath = os.path.join(area_dir, filename)
                print(f"  -> Landsat {year} S{sem}...")

                img, _ = get_landsat_image(region, year, sem, method=method)
                if img:
                    success = get_download_or_export(img, region, scale, filepath, buffer_factor, drive_folder)
                    results_list.append({"file": filename, "status": "OK" if success else "ERRO", "year": year, "sem": sem})
                else:
                    print("  [AVISO] Nenhuma imagem Landsat disponível.")
                    results_list.append({"file": filename, "status": "SEM_IMAGEM", "year": year, "sem": sem})

                if progress_callback:
                    progress_callback(current_op, total_ops, f"Landsat {year} S{sem}")

        elif is_cbers:
            if mode == "Composição por Semestre":
                for sem in [1, 2]:
                    current_op += 1
                    m_list = [1, 2, 3, 4, 5, 6] if sem == 1 else [7, 8, 9, 10, 11, 12]
                    print(f"  -> CBERS-4A {year} S{sem}...")
                    res = get_cbers_image_inpe(region, year, m_list, area_dir, scale_factor=buffer_factor, inpe_email=inpe_email)
                    status = "OK" if res else "SEM_IMAGEM"
                    results_list.append({"file": os.path.basename(res) if res else f"CBERS_{year}_S{sem}.tif", "status": status, "year": year, "sem": sem})
                    if progress_callback:
                        progress_callback(current_op, total_ops, f"CBERS {year} S{sem}")
            else:
                current_op += 1
                print(f"  -> CBERS-4A {year} (Meses {months})...")
                res = get_cbers_image_inpe(region, year, months, area_dir, scale_factor=buffer_factor, inpe_email=inpe_email)
                status = "OK" if res else "SEM_IMAGEM"
                results_list.append({"file": os.path.basename(res) if res else f"CBERS_{year}.tif", "status": status, "year": year})
                if progress_callback:
                    progress_callback(current_op, total_ops, f"CBERS {year}")

        elif is_spot:
            current_op += 1
            filename = "SPOT2008_2008_CF.tif"
            filepath = os.path.join(area_dir, filename)
            print("  -> Mosaico SPOT 2008 (Código Florestal)...")
            img = get_spot_2008_image(region, buffer_factor)
            if img:
                success = get_download_or_export(img, region, scale, filepath, buffer_factor, drive_folder)
                results_list.append({"file": filename, "status": "OK" if success else "ERRO", "year": 2008})
            else:
                print("  [AVISO] Erro ao recuperar mosaico SPOT 2008.")
                results_list.append({"file": filename, "status": "SEM_IMAGEM", "year": 2008})
            if progress_callback:
                progress_callback(current_op, total_ops, "SPOT 2008")

    # Resumo final
    success_count = sum(1 for r in results_list if r["status"] == "OK")
    return {
        "sensor": sat_label,
        "area_label": area_label,
        "area_dir": area_dir,
        "drive_folder": drive_folder,
        "total_ops": total_ops,
        "success_count": success_count,
        "results": results_list
    }
