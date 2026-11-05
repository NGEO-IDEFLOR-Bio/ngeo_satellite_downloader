"""
Módulo de Operações Vetoriais e Processamento Espacial
=====================================================
Núcleo de Geotecnologias (NGEO / IDEFLOR-Bio)
Responsável por descompactar shapefiles, validar geometrias,
reprojetar para EPSG:4326, calcular estatísticas e dividir grandes áreas em tiles.
"""

import os
import math
import shutil
import zipfile
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional, Union

import ee
import geopandas as gpd
from src.config import CRS_WGS84, MAX_PIXELS_DIRECT, DEFAULT_BUFFER_FACTOR


def parse_years(text: Union[str, int]) -> List[int]:
    """Converte strings de anos (ex: '2024', '2020-2024', '2020, 2022, 2024') em lista de inteiros."""
    if isinstance(text, int):
        return [text]
    text = str(text).strip()
    if not text:
        return []
    if '-' in text:
        parts = text.split('-')
        start, end = int(parts[0].strip()), int(parts[1].strip())
        return list(range(start, end + 1))
    elif ',' in text:
        return [int(y.strip()) for y in text.split(',') if y.strip()]
    else:
        return [int(text)]


def expand_region(region: ee.Geometry, scale_factor: float = DEFAULT_BUFFER_FACTOR) -> ee.Geometry:
    """Expande a bounding box da geometria pelo fator de escala informado."""
    bounds = region.bounds()
    coords = bounds.coordinates().get(0).getInfo()
    xs = [pt[0] for pt in coords]
    ys = [pt[1] for pt in coords]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    xmid = (xmin + xmax) / 2
    ymid = (ymin + ymax) / 2
    xrange = (xmax - xmin) * scale_factor / 2
    yrange = (ymax - ymin) * scale_factor / 2
    return ee.Geometry.Rectangle([
        xmid - xrange, ymid - yrange,
        xmid + xrange, ymid + yrange
    ])


def estimate_pixel_count(region: ee.Geometry, scale: float) -> int:
    """Estima o número de pixels cobertos pela extensão da geometria na resolução informada."""
    bounds = region.bounds().coordinates().get(0).getInfo()
    xs = [pt[0] for pt in bounds]
    ys = [pt[1] for pt in bounds]
    lat_mid = (min(ys) + max(ys)) / 2
    m_per_deg_lon = 111320 * math.cos(math.radians(lat_mid))
    m_per_deg_lat = 110540
    width_m = (max(xs) - min(xs)) * m_per_deg_lon
    height_m = (max(ys) - min(ys)) * m_per_deg_lat
    return int((width_m / scale) * (height_m / scale))


def split_region_into_tiles(
    region: ee.Geometry,
    scale: float,
    max_pixels: int = MAX_PIXELS_DIRECT
) -> Tuple[List[ee.Geometry], int]:
    """Divide uma região extensa em uma grade de tiles se exceder max_pixels."""
    total_pixels = estimate_pixel_count(region, scale)
    if total_pixels <= max_pixels:
        return [region], total_pixels

    n_tiles_needed = math.ceil(total_pixels / max_pixels)
    n_side = math.ceil(math.sqrt(n_tiles_needed))
    bounds = region.bounds().coordinates().get(0).getInfo()
    xs = [pt[0] for pt in bounds]
    ys = [pt[1] for pt in bounds]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    dx = (xmax - xmin) / n_side
    dy = (ymax - ymin) / n_side

    tiles = []
    for i in range(n_side):
        for j in range(n_side):
            tile = ee.Geometry.Rectangle([
                xmin + j * dx, ymin + i * dy,
                xmin + (j + 1) * dx, ymin + (i + 1) * dy
            ])
            tiles.append(tile)
    return tiles, total_pixels


def extract_shapefile_from_zip(zip_source: Union[str, bytes], extract_dir: str = "shapefile") -> str:
    """Extrai arquivo ZIP e localiza o primeiro arquivo .shp contido nele."""
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)

    if isinstance(zip_source, str):
        with zipfile.ZipFile(zip_source, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    else:
        import io
        with zipfile.ZipFile(io.BytesIO(zip_source), 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

    shp_files = [f for f in os.listdir(extract_dir) if f.lower().endswith('.shp')]
    if not shp_files:
        # Procurar em subdiretórios se houver pasta interna
        for root, _, files in os.walk(extract_dir):
            for file in files:
                if file.lower().endswith('.shp'):
                    return os.path.join(root, file)
        raise FileNotFoundError("Nenhum arquivo .shp foi encontrado dentro do arquivo ZIP fornecido.")

    return os.path.join(extract_dir, shp_files[0])


def load_shapefile_geometry(shp_path: str) -> Tuple[ee.Geometry, gpd.GeoDataFrame]:
    """Carrega shapefile via Geopandas, garante reprojeção para EPSG:4326 e converte para ee.Geometry."""
    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        gdf = gdf.set_crs(CRS_WGS84)
    elif gdf.crs.to_string() != CRS_WGS84:
        gdf = gdf.to_crs(CRS_WGS84)

    # Converter para ee.FeatureCollection / ee.Geometry
    geojson_data = json.loads(gdf.to_json())
    feature_collection = ee.FeatureCollection(geojson_data)
    geometry = feature_collection.geometry()

    return geometry, gdf


def calculate_aoi_stats(region: ee.Geometry, gdf: Optional[gpd.GeoDataFrame] = None) -> Dict[str, Any]:
    """Calcula estatísticas de extensão, bounding box e estimativa de pixels para os sensores."""
    bounds = region.bounds().coordinates().get(0).getInfo()
    xs = [pt[0] for pt in bounds]
    ys = [pt[1] for pt in bounds]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    # Estimativa de área em km² e hectares usando projeção métrica
    area_ha = 0.0
    area_km2 = 0.0
    if gdf is not None and not gdf.empty:
        gdf_metric = gdf.to_crs("EPSG:5880")  # SIRGAS 2000 / Brasil Policonica
        area_m2 = gdf_metric.geometry.area.sum()
        area_ha = area_m2 / 10000.0
        area_km2 = area_m2 / 1000000.0
    else:
        # Cálculo aproximado por bounding box
        lat_mid = (ymin + ymax) / 2
        m_lon = 111320 * math.cos(math.radians(lat_mid)) * (xmax - xmin)
        m_lat = 110540 * (ymax - ymin)
        area_km2 = (m_lon * m_lat) / 1000000.0
        area_ha = area_km2 * 100.0

    sensors_px = {
        "Sentinel (10m)": estimate_pixel_count(region, 10),
        "Landsat (30m)": estimate_pixel_count(region, 30),
        "SPOT (5m)": estimate_pixel_count(region, 5),
        "CBERS (2m)": estimate_pixel_count(region, 2),
    }

    return {
        "bounds": {"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
        "center": [(ymin + ymax) / 2, (xmin + xmax) / 2],
        "area_ha": area_ha,
        "area_km2": area_km2,
        "pixels": sensors_px
    }
