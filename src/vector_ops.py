"""
Modulo de operacoes vetoriais e processamento espacial.
Nucleo de Geotecnologias (NGEO, IDEFLOR-Bio).
Realiza a descompactacao de shapefiles, validacao topologica,
reprojecao para EPSG:4326, conversao bidimensional e calculo de metricas de area.
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
import shapely
from src.config import CRS_WGS84, MAX_PIXELS_DIRECT, DEFAULT_BUFFER_FACTOR


def parse_years(text: Union[str, int]) -> List[int]:
    """Converte expressao textual de anos em lista de numeros inteiros."""
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
    """Aplica fator multiplicador sobre os limites retangulares da geometria."""
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
    """Calcula a estimativa numerica de pixels na resolucao informada."""
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
    """Segmenta a area em grade regular caso a contagem de pixels exceda o limite operacional."""
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
    """Extrai arquivo compactado em formato ZIP e localiza o arquivo com extensao .shp."""
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
        for root, _, files in os.walk(extract_dir):
            for file in files:
                if file.lower().endswith('.shp'):
                    return os.path.join(root, file)
        raise FileNotFoundError("Nenhum arquivo com extensao .shp foi localizado no arquivo ZIP.")

    return os.path.join(extract_dir, shp_files[0])


def load_shapefile_geometry(shp_path: str) -> Tuple[ee.Geometry, gpd.GeoDataFrame]:
    """
    Carrega o shapefile, padroniza as coordenadas em 2D para WGS-84 (EPSG:4326)
    e converte para objeto ee.Geometry compativel com a API do Earth Engine.
    """
    gdf = gpd.read_file(shp_path)
    if gdf.crs is None:
        gdf = gdf.set_crs(CRS_WGS84)
    elif gdf.crs.to_string() != CRS_WGS84:
        gdf = gdf.to_crs(CRS_WGS84)

    # Forcar geometrias estritamente bidimensionais para conformidade com a validacao do Earth Engine
    gdf.geometry = shapely.force_2d(gdf.geometry)
    gdf.geometry = shapely.make_valid(gdf.geometry)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notnull()].copy()

    if gdf.empty:
        raise ValueError("O shapefile informado nao possui registros geometricos validos.")

    geometry = None

    # Tentativa 1: geemap.shp_to_ee quando disponivel
    try:
        import geemap
        fc = geemap.shp_to_ee(shp_path)
        if fc is not None:
            geometry = fc.geometry()
    except Exception:
        geometry = None

    # Tentativa 2: conversao via GeoJSON tratado em duas dimensoes
    if geometry is None:
        try:
            geojson_dict = json.loads(gdf.to_json())
            fc = ee.FeatureCollection(geojson_dict)
            geometry = fc.geometry()
        except Exception:
            geometry = None

    # Tentativa 3: uniao geometrica direta convertida via dicionario GeoJSON
    if geometry is None:
        try:
            if hasattr(gdf.geometry, 'union_all'):
                geom_union = shapely.force_2d(shapely.make_valid(gdf.geometry.union_all()))
            else:
                geom_union = shapely.force_2d(shapely.make_valid(gdf.unary_union))
            mapping_dict = shapely.geometry.mapping(geom_union)
            geometry = ee.Geometry(mapping_dict)
        except Exception as e:
            raise ValueError(f"Falha na conversao da geometria para o Earth Engine: {e}")

    return geometry, gdf


def calculate_aoi_stats(region: ee.Geometry, gdf: Optional[gpd.GeoDataFrame] = None) -> Dict[str, Any]:
    """Calcula estatisticas operacionais de extensao geografica e estimativa de amostragem."""
    bounds = region.bounds().coordinates().get(0).getInfo()
    xs = [pt[0] for pt in bounds]
    ys = [pt[1] for pt in bounds]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    area_ha = 0.0
    area_km2 = 0.0
    if gdf is not None and not gdf.empty:
        try:
            gdf_metric = gdf.to_crs("EPSG:5880")
            area_m2 = gdf_metric.geometry.area.sum()
            area_ha = area_m2 / 10000.0
            area_km2 = area_m2 / 1000000.0
        except Exception:
            lat_mid = (ymin + ymax) / 2
            m_lon = 111320 * math.cos(math.radians(lat_mid)) * (xmax - xmin)
            m_lat = 110540 * (ymax - ymin)
            area_km2 = (m_lon * m_lat) / 1000000.0
            area_ha = area_km2 * 100.0
    else:
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
