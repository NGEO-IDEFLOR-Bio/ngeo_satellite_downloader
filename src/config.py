"""
Módulo de Configurações e Constantes Operacionais
================================================
Núcleo de Geotecnologias (NGEO / IDEFLOR-Bio)
Define coleções do Earth Engine, resoluções espaciais, bandas espectrais
e limites de divisão em tiles.
"""

from pathlib import Path

# Diretórios base
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

# Configuração Padrão do Google Earth Engine
DEFAULT_GEE_PROJECT = "sentinel-landsat-download"
FALLBACK_GEE_PROJECT = "ee-samuelsantosambientalcourse"

# Sistema de Referência Espacial
CRS_WGS84 = "EPSG:4326"

# Resoluções e Parâmetros dos Sensores
SENSOR_CONFIGS = {
    "Sentinel": {
        "label": "Sentinel-2 MSI (10m)",
        "scale": 10,
        "collection": "COPERNICUS/S2_SR_HARMONIZED",
        "bands": ["B4", "B3", "B2"],
        "cloud_field": "CLOUDY_PIXEL_PERCENTAGE",
        "cloud_threshold": 80,
    },
    "Landsat": {
        "label": "Landsat 5/7/8/9 (30m)",
        "scale": 30,
        "collections": {
            "L5": {"id": "LANDSAT/LT05/C02/T1_L2", "bands": ["SR_B5", "SR_B4", "SR_B3"], "max_year": 2011},
            "L7": {"id": "LANDSAT/LE07/C02/T1_L2", "bands": ["SR_B3", "SR_B2", "SR_B1"], "max_year": 2013},
            "L8": {"id": "LANDSAT/LC08/C02/T1_L2", "bands": ["SR_B6", "SR_B5", "SR_B4"], "max_year": 2021},
            "L9": {"id": "LANDSAT/LC09/C02/T1_L2", "bands": ["SR_B4", "SR_B3", "SR_B2"], "max_year": 9999},
        },
        "cloud_field": "CLOUD_COVER",
        "cloud_threshold": 10,
    },
    "SPOT": {
        "label": "SPOT 2008 - Código Florestal (5m)",
        "scale": 5,
        "asset": "GOOGLE/BRAZIL_FOREST_2008/V1/VISUAL",
        "bands": ["R", "G", "B"],
        "year": 2008,
    },
    "CBERS": {
        "label": "CBERS-4A WPM/MUX (2m)",
        "scale": 2,
        "collection": "CBERS4A_WPM_L4_DN",
        "bands": ["red", "green", "blue", "nir"],
    }
}

# Limites Operacionais para Divisão de Tiles
MAX_PIXELS_DIRECT = 5_000_000
MAX_PIXELS_GEE_EXPORT = 1e13
DEFAULT_BUFFER_FACTOR = 2.0
DEFAULT_DRIVE_FOLDER = "Satellite_Downloads"
