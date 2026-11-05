"""
Módulo de Consulta e Processamento de Sensores Orbitais
======================================================
Núcleo de Geotecnologias (NGEO / IDEFLOR-Bio)
Contém filtros temporais, máscaras espectrais de nuvens (SCL/QA_PIXEL),
composição inteligente por mediana e seleção de melhor imagem para Sentinel, Landsat e SPOT.
"""

import calendar
from typing import Optional, Tuple, List, Callable

import ee
from src.config import SENSOR_CONFIGS
from src.vector_ops import expand_region


# --- Funções de Máscara de Nuvens e Validação ---

def calc_cloud_in_roi_landsat(image: ee.Image, region: ee.Geometry, scale: int = 30) -> ee.Image:
    """Calcula a porcentagem de nuvens na ROI usando QA_PIXEL (Landsat)."""
    qa = image.select('QA_PIXEL')
    cloud_mask = qa.bitwiseAnd(1 << 4).neq(0)
    cloud_pct = cloud_mask.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e6
    ).get('QA_PIXEL')
    return image.set('ROI_CLOUD', cloud_pct)


def apply_cloud_mask_landsat(image: ee.Image) -> ee.Image:
    """Aplica máscara de nuvem, sombra e neve via QA_PIXEL (Landsat)."""
    qa = image.select('QA_PIXEL')
    # Bit 3: sombra de nuvem, Bit 4: nuvem, Bit 5: neve
    mask = qa.bitwiseAnd(1 << 3).eq(0) \
          .And(qa.bitwiseAnd(1 << 4).eq(0)) \
          .And(qa.bitwiseAnd(1 << 5).eq(0))
    return image.updateMask(mask)


def calc_cloud_in_roi_sentinel(image: ee.Image, region: ee.Geometry, scale: int = 10) -> ee.Image:
    """Calcula a porcentagem de nuvens na ROI usando SCL (Sentinel-2)."""
    scl = image.select('SCL')
    # Classes SCL: 7=unclassified, 8=cloud medium, 9=cloud high, 10=cirrus
    cloud_mask = scl.eq(7).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10))
    cloud_pct = cloud_mask.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e6
    ).get('SCL')
    return image.set('ROI_CLOUD', cloud_pct)


def apply_cloud_mask_sentinel(image: ee.Image) -> ee.Image:
    """Aplica máscara de nuvem e sombra via banda SCL (Sentinel-2 Scene Classification)."""
    scl = image.select('SCL')
    # Remove sombra (3) e nuvens (7, 8, 9, 10)
    mask = scl.neq(3).And(scl.neq(7)).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    return image.updateMask(mask)


def mask_zero_pixels(image: ee.Image) -> ee.Image:
    """Mascara pixels com valor zero nas bandas espectrais."""
    all_bands = image.bandNames()
    good_bands = all_bands.filter(ee.Filter.stringContains('item', 'QA').Not()) \
                          .filter(ee.Filter.stringContains('item', 'SCL').Not()) \
                          .filter(ee.Filter.stringContains('item', 'cloud').Not()) \
                          .filter(ee.Filter.stringContains('item', 'CLOUD').Not())
    mask = image.select(good_bands).reduce(ee.Reducer.max()).neq(0)
    return image.updateMask(mask)


def smart_composite(
    collection: ee.ImageCollection,
    region: ee.Geometry,
    calc_cloud_fn: Callable,
    mask_fn: Callable,
    scale: int = 30,
    min_valid_pct: float = 30.0,
    max_images: int = 5
) -> Optional[ee.Image]:
    """
    Composição inteligente: classifica as melhores cenas com menor cobertura de nuvens
    na ROI, aplica máscara de nuvens/sombras e gera a mediana das observações válidas.
    """
    bounds = region.bounds()
    collection_with_roi = collection.map(lambda img: calc_cloud_fn(img, bounds, scale))
    ranked = collection_with_roi.sort('ROI_CLOUD')

    try:
        info_list = ranked.limit(max_images).getInfo().get('features', [])
    except Exception as e:
        print(f"      [AVISO] Erro ao obter metadados das cenas: {e}")
        return None

    if not info_list:
        return None

    valid_images = []
    for idx, feat in enumerate(info_list):
        img_id = feat.get('id')
        if not img_id:
            continue
        properties = feat.get('properties', {})
        roi_cloud = properties.get('ROI_CLOUD')
        if roi_cloud is None:
            continue
        valid_pct = (1.0 - roi_cloud) * 100.0

        if idx == 0:
            img = ee.Image(img_id)
            valid_images.append(mask_zero_pixels(mask_fn(img)))
        else:
            if valid_pct < min_valid_pct:
                continue
            img = ee.Image(img_id)
            valid_images.append(mask_zero_pixels(mask_fn(img)))

    if not valid_images:
        return None

    combined = ee.ImageCollection(valid_images).median()
    return combined


# --- Funções de Consulta Específicas por Sensor ---

def get_sentinel_image(
    region: ee.Geometry,
    year: int,
    start_month: int,
    end_month: int,
    method: str = "median"
) -> Optional[ee.Image]:
    """Obtém imagem do Sentinel-2 SR Harmonized com composição inteligente ou melhor cena."""
    _, last_day = calendar.monthrange(year, end_month)
    start_date = f"{year}-{start_month:02d}-01"
    end_date = f"{year}-{end_month:02d}-{last_day}"

    bounds = region.bounds()
    collection = (
        ee.ImageCollection(SENSOR_CONFIGS["Sentinel"]["collection"])
        .filterBounds(bounds)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt(SENSOR_CONFIGS["Sentinel"]["cloud_field"], SENSOR_CONFIGS["Sentinel"]["cloud_threshold"]))
    )

    count = collection.size().getInfo()
    if count == 0:
        return None

    print(f"    ({count} imagens Sentinel-2 encontradas entre {start_date} e {end_date})")

    if method == "best":
        return collection.sort("CLOUDY_PIXEL_PERCENTAGE").first().select(["B4", "B3", "B2"])

    img = smart_composite(
        collection,
        region,
        calc_cloud_in_roi_sentinel,
        apply_cloud_mask_sentinel,
        scale=10,
        min_valid_pct=30,
        max_images=5
    )
    return img.select(["B4", "B3", "B2"]) if img else None


def get_landsat_image(
    region: ee.Geometry,
    year: int,
    semester: int,
    method: str = "median"
) -> Tuple[Optional[ee.Image], Optional[List[str]]]:
    """Obtém imagem Landsat 5, 7, 8 ou 9 conforme o ano com seleção de semestre."""
    if semester == 1:
        start_date = f"{year}-01-01"
        end_date = f"{year}-06-30"
    else:
        start_date = f"{year}-07-01"
        end_date = f"{year}-12-31"

    if year <= 2011:
        collection_id = "LANDSAT/LT05/C02/T1_L2"
        band_options = ["SR_B5", "SR_B4", "SR_B3"]
    elif year <= 2013:
        collection_id = "LANDSAT/LE07/C02/T1_L2"
        band_options = ["SR_B3", "SR_B2", "SR_B1"]
    elif year <= 2021:
        collection_id = "LANDSAT/LC08/C02/T1_L2"
        band_options = ["SR_B6", "SR_B5", "SR_B4"]
    else:
        collection_id = "LANDSAT/LC09/C02/T1_L2"
        band_options = ["SR_B4", "SR_B3", "SR_B2"]

    bounds = region.bounds()
    collection = (
        ee.ImageCollection(collection_id)
        .filterBounds(bounds)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUD_COVER", 10))
    )

    count = collection.size().getInfo()
    if count == 0:
        return None, None

    if method == "best":
        image = collection.sort("CLOUD_COVER").first()
        return image.select(band_options), band_options

    image = collection.median().select(band_options)
    return image, band_options


def get_spot_2008_image(
    region: ee.Geometry,
    buffer_factor: float = 2.0
) -> Optional[ee.Image]:
    """Obtém mosaico SPOT 2008 (Código Florestal) recortado com expansão."""
    try:
        image = ee.Image(SENSOR_CONFIGS["SPOT"]["asset"])
        expanded = expand_region(region, buffer_factor)
        clipped = image.clip(expanded)
        clipped.getInfo()
        return clipped.select(["R", "G", "B"])
    except Exception as e:
        print(f"  [ERRO] SPOT 2008: {e}")
        return None
