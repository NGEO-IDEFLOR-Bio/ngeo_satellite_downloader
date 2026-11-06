# NGEO Satellite Downloader

<p align="left">
  <a href="https://colab.research.google.com/github/NGEO-IDEFLOR-Bio/ngeo_satellite_downloader/blob/main/ngeo_satellite_downloader.ipynb" target="_blank" style="text-decoration: none;">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab" height="32">
  </a>
</p>

Ambiente operacional automatizado para o Google Colab desenvolvido pelo Nucleo de Geotecnologias (NGEO) do Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Para (IDEFLOR-Bio). O sistema executa a aquisicao de imagens orbitais dos programas Sentinel-2, Landsat, CBERS-4A e SPOT 2008 sobre limites territoriais fornecidos em formato shapefile, aplicando mascaras de nuvens, composicao por mediana estatistica, particionamento em grade de tiles e exportacao em GeoTIFF para o Google Drive.

A interface do notebook utiliza formularios nativos do Google Colab com codigo oculto por padrao e painel reativo condicional, disponibilizando campos de selecao parametrica fechada para operacao direta por tecnicos e analistas ambientais.

## Finalidade Institucional

A ferramenta atende as demandas de analise pericial, elaboracao de relatorios tecnicos, instrucao processual e monitoramento territorial no Estado do Para, sob coordenacao de Samuel da Costa dos Santos no Nucleo de Geotecnologias do IDEFLOR-Bio [1].

## Sensores Orbitais e Especificacoes

| Sensor | Resolucao Espacial | Colecao e Catalogo | Caracteristicas Tecnicas |
|---|---:|---|---|
| Sentinel-2 MSI | 10 m | COPERNICUS/S2_SR_HARMONIZED | Composicao semestral ou mensal com mascara de nuvens via banda SCL. |
| Landsat 5, 7, 8 e 9 | 30 m | LANDSAT/Collection 2/Tier 1/Level 2 | Series temporais calibradas em reflectancia de superficie com mascara QA_PIXEL. |
| CBERS-4A (WPM e MUX) | 2 m | Catalogo INPE (API Cbers4a) | Aquisicao de alta resolucao espacial com composicao multiespectral RGBN. |
| SPOT 2008 | 5 m | GOOGLE/BRAZIL_FOREST_2008/V1/VISUAL | Mosaico de cobertura florestal historica de referencia do Codigo Florestal. |

## Roteiro de Execucao

1. Acesso ao notebook: abra o arquivo ngeo_satellite_downloader.ipynb no ambiente Google Colab por meio do link institucional.
2. Etapa 1 (Instalacao): execute a celula de preparacao para instalacao silenciosa das bibliotecas geoespaciais e sincronizacao automatica do nucleo de processamento.
3. Etapa 2 (Autenticacao): informe o identificador do projeto no Google Earth Engine e autorize a integracao com o Google Drive.
4. Etapa 3 (Entrada vetorial): envie o arquivo ZIP contendo os componentes do shapefile (.shp, .shx, .dbf, .prj). O fluxo executa a reprojecao automatica para WGS-84 (EPSG:4326), a higienizacao de geometrias bidimensionais e o calculo de metricas espaciais.
5. Etapa 4 (Painel integrado): selecione o sensor orbital no painel reativo, ajuste os parametros condicionais de periodo e buffer, e clique no botao INICIAR DOWNLOAD integrado para iniciar o processamento e acompanhar a exportacao dos arquivos GeoTIFF.

## Estrutura do Repositorio

```text
ngeo_satellite_downloader/
├── src/                          # Modulos do motor de processamento
│   ├── __init__.py               # Definicoes do pacote e exportacoes
│   ├── config.py                 # Constantes de sensores e limites operacionais
│   ├── vector_ops.py             # Leitura, conversao 2D e particionamento em tiles
│   ├── sensors.py                # Consultas ao Earth Engine e mascaras de nuvens
│   ├── cbers.py                  # Integracao com a API e catalogo CBERS (INPE)
│   ├── exporter.py               # Orquestrador de tarefas e gravacao no Drive
│   └── ui_helpers.py             # Painel reativo condicional e relatorios
├── ngeo_satellite_downloader.ipynb # Notebook com interface de formulario
├── requirements.txt              # Relacao de dependencias tecnicas
├── LICENSE                       # Termos da Licenca MIT
└── README.md                     # Documentacao tecnica
```

## Controle de Qualidade

1. Sistema de referencia: os produtos gerados adotam coordenadas geograficas no datum WGS-84 / SIRGAS 2000 (EPSG:4326).
2. Sazonalidade de nebulosidade: para areas localizadas na Amazonia durante o periodo chuvoso (janeiro a maio), recomenda-se utilizar a analise anual com selecao especifica dos meses secos (julho a outubro).
3. Particionamento espacial: areas com extensao superior a 5 milhoes de pixels sao subdivididas automaticamente em grade regular para assegurar a preservacao da resolucao nativa do sensor.

## Creditos e Vinculacao Institucional

Desenvolvimento e coordenacao: Samuel da Costa dos Santos (samuelsantos.site).

Nucleo de Geotecnologias (NGEO), Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Para (IDEFLOR-Bio) [1].

## Licenca

Este projeto e disponibilizado sob os termos da Licenca MIT.

## Referencias

[1]: https://ideflorbio.pa.gov.br/telefones/ "Pagina oficial de contatos do IDEFLOR-Bio: identificacao do Nucleo de Geotecnologias (NGEO)"
