"""
NGEO Satellite Downloader
=========================
Núcleo de Geotecnologias (NGEO / IDEFLOR-Bio)
Automação de download de imagens Sentinel-2, Landsat, SPOT e CBERS-4A.
"""

from src.config import SENSOR_CONFIGS, DEFAULT_GEE_PROJECT
from src.vector_ops import (
    parse_years,
    expand_region,
    estimate_pixel_count,
    split_region_into_tiles,
    extract_shapefile_from_zip,
    load_shapefile_geometry,
    calculate_aoi_stats
)
from src.sensors import (
    get_sentinel_image,
    get_landsat_image,
    get_spot_2008_image
)
from src.cbers import get_cbers_image_inpe
from src.exporter import run_pipeline, export_to_drive, monitor_task
from src.ui_helpers import render_aoi_card, render_results_cards

__version__ = "2.0.0"
__author__ = "Samuel da Costa dos Santos (NGEO / IDEFLOR-Bio)"
