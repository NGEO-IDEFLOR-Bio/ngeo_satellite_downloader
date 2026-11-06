"""
Modulo de integracao com o catalogo de imagens CBERS-4A (INPE).
Nucleo de Geotecnologias (NGEO, IDEFLOR-Bio).
Realiza consultas na API Cbers4a, download de bandas espectrais,
composicao RGBN e recorte espacial sobre a area de interesse.
"""

import os
import shutil
import datetime
import calendar
from typing import Tuple, List, Optional

import ee


def check_cbers_deps() -> Tuple[bool, str]:
    """Verifica se as dependencias do ecossistema CBERS estao instaladas."""
    try:
        import cbers4asat
        import rasterio
        import geopandas
        import shapely
        return True, ""
    except ImportError as e:
        return False, str(e)


def get_cbers_image_inpe(
    region_ee: ee.Geometry,
    year: int,
    months: List[int],
    output_dir: str,
    scale_factor: float = 2.0,
    inpe_email: Optional[str] = None
) -> Optional[str]:
    """
    Localiza, baixa e processa cenas CBERS-4A via catalogo do INPE.
    Gera composicao multiespectral e recorta nos limites da area de interesse.
    """
    has_deps, err = check_cbers_deps()
    if not has_deps:
        print(f"  [ERRO] Dependencias CBERS ausentes: {err}")
        return None

    if not inpe_email:
        print("  [ERRO] Endereco de e-mail cadastrado no INPE nao informado.")
        return None

    try:
        from cbers4asat import Cbers4aAPI
        from cbers4asat.tools import rgbn_composite, clip as raster_clip
        from shapely.geometry import Polygon
        import geopandas as gpd
        import rasterio as rio

        bounds = region_ee.bounds().coordinates().get(0).getInfo()
        lons = [p[0] for p in bounds]
        lats = [p[1] for p in bounds]
        xmid = (min(lons) + max(lons)) / 2
        ymid = (min(lats) + max(lats)) / 2
        xrange = (max(lons) - min(lons)) * scale_factor / 2
        yrange = (max(lats) - min(lats)) * scale_factor / 2
        bbox = [xmid - xrange, ymid - yrange, xmid + xrange, ymid + yrange]
        poly_aoi = Polygon([
            (bbox[0], bbox[1]), (bbox[2], bbox[1]),
            (bbox[2], bbox[3]), (bbox[0], bbox[3])
        ])

        api = Cbers4aAPI(inpe_email)
        start_date = datetime.date(year, min(months), 1)
        _, last_day = calendar.monthrange(year, max(months))
        end_date = datetime.date(year, max(months), last_day)
        print(f"  [INFO] Consulta ao catalogo CBERS-4A de {start_date} a {end_date}.")

        products = api.query(
            location=bbox,
            initial_date=start_date,
            end_date=end_date,
            cloud=100,
            limit=50,
            collections=['CBERS4A_WPM_L4_DN']
        )

        if not products or not products.get('features'):
            print("  [AVISO] Nenhuma cena CBERS-4A encontrada para o intervalo.")
            return None

        features = products['features']

        def get_cloud(f):
            p = f.get('properties', {})
            return p.get('cloud_cover', p.get('eo:cloud_cover', 100))

        features.sort(key=get_cloud)
        best = features[0]
        scene_id = best['id']
        cloud_val = get_cloud(best)
        date_str = best['properties'].get('datetime', '').split('T')[0]
        print(f"  [INFO] Cena selecionada: {scene_id} ({date_str}, {cloud_val}% de nuvens).")

        bands = ['red', 'green', 'blue', 'nir']
        temp_dir = os.path.join(output_dir, 'temp_cbers')
        os.makedirs(temp_dir, exist_ok=True)

        print("  [INFO] Efetuando download das bandas espectrais...")
        api.download(
            products={'type': 'FeatureCollection', 'features': [best]},
            bands=bands,
            outdir=temp_dir,
            with_folder=True
        )

        scene_subdir = os.path.join(temp_dir, scene_id)
        if not os.path.exists(scene_subdir):
            subdirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
            if subdirs:
                scene_subdir = os.path.join(temp_dir, subdirs[0])

        files_list = os.listdir(scene_subdir)
        b_red = next((os.path.join(scene_subdir, f) for f in files_list if 'BAND3' in f or 'BAND5' in f), None)
        b_green = next((os.path.join(scene_subdir, f) for f in files_list if 'BAND2' in f or 'BAND6' in f), None)
        b_blue = next((os.path.join(scene_subdir, f) for f in files_list if 'BAND1' in f or 'BAND7' in f), None)
        b_nir = next((os.path.join(scene_subdir, f) for f in files_list if 'BAND4' in f or 'BAND8' in f), None)

        if not all([b_red, b_green, b_blue]):
            print("  [ERRO] Falha ao identificar as bandas espectrais necessarias.")
            return None

        composite_path = os.path.join(output_dir, f'CBERS_{scene_id}_STACK.tif')
        print("  [INFO] Gerando empilhamento de bandas RGBN...")
        rgbn_composite(
            red=b_red, green=b_green, blue=b_blue, nir=b_nir,
            filename=os.path.basename(composite_path), outdir=output_dir
        )

        final_filename = f'CBERS_{year}_{scene_id[:10]}.tif'
        final_path = os.path.join(output_dir, final_filename)
        print("  [INFO] Aplicando mascara de recorte sobre a area de interesse...")

        try:
            with rio.open(composite_path) as src:
                raster_crs = src.crs or 'EPSG:3857'
            gdf_aoi = gpd.GeoDataFrame(index=[0], crs='EPSG:4326', geometry=[poly_aoi])
            gdf_aoi = gdf_aoi.to_crs(raster_crs)
            poly_mask = gdf_aoi.geometry.iloc[0]
            raster_clip(
                raster=composite_path, mask=poly_mask,
                filename=final_filename, outdir=output_dir
            )
        except Exception as e:
            print(f"  [AVISO] Recorte reprojetado falhou ({e}). Aplicando recorte geografico padrao...")
            raster_clip(
                raster=composite_path, mask=poly_aoi,
                filename=final_filename, outdir=output_dir
            )

        try:
            shutil.rmtree(temp_dir)
            if os.path.exists(composite_path):
                os.remove(composite_path)
        except Exception:
            pass

        return final_path
    except Exception as e:
        print(f"  [ERRO] Falha durante a execucao do fluxo CBERS: {e}")
        return None
