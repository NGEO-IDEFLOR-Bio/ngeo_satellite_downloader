# 🛰️ NGEO Satellite Downloader

<p align="left">
  <a href="https://colab.research.google.com/github/NGEO-IDEFLOR-Bio/ngeo_satellite_downloader/blob/main/ngeo_satellite_downloader.ipynb" target="_blank" style="text-decoration: none;">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab" height="32">
  </a>
</p>

Pipeline operacional automatizado para o **Google Colab** desenvolvido pelo **Núcleo de Geotecnologias (NGEO / IDEFLOR-Bio)** para download de imagens de satélite (**Sentinel-2**, **Landsat**, **CBERS-4A** e **SPOT 2008**) sobre áreas de interesse definidas por Shapefile, com aplicação automática de máscara de nuvens, composição por mediana inteligente, divisão em quadrículas (tiles) e exportação em GeoTIFF para o Google Drive.

> 💡 **Interface Moderna e Amigável:** O notebook adota formulários nativos do Google Colab com **código 100% oculto por padrão** (`cellView: "form"`), permitindo que técnicos e analistas ambientais operem todo o fluxo apenas preenchendo os parâmetros visuais essenciais.

---

## 🏛️ Contexto e Finalidade

Desenvolvido para subsidiar rotinas periciais, relatórios técnicos, vistorias remotas e monitoramento territorial no âmbito do **Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Pará (IDEFLOR-Bio)**, sob coordenação de **Samuel da Costa dos Santos** (NGEO/IDEFLOR-Bio) [1].

---

## 🛰️ Sensores Orbitais e Especificações

| Sensor | Resolução Espacial | Coleção / Fonte | Características Principais |
|---|---:|---|---|
| **Sentinel-2 MSI** | 10 m | `COPERNICUS/S2_SR_HARMONIZED` | Composição semestral ou mensal; máscara de nuvens e cirrus via SCL. |
| **Landsat 5 / 7 / 8 / 9** | 30 m | `LANDSAT/*/C02/T1_L2` | Séries históricas de reflectância de superfície com máscara QA_PIXEL. |
| **CBERS-4A (WPM/MUX)** | 2 m | Catálogo INPE (API Cbers4a) | Alta resolução espacial nacional com composição RGBN e recorte exato. |
| **SPOT 2008** | 5 m | `GOOGLE/BRAZIL_FOREST_2008/V1/VISUAL` | Mosaico histórico oficial do Código Florestal Brasileiro (MMA/SFB). |

---

## 🚀 Passo a Passo de Execução

1. **Abra o notebook no Colab** clicando no botão [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/NGEO-IDEFLOR-Bio/ngeo_satellite_downloader/blob/main/ngeo_satellite_downloader.ipynb).
2. **Passo 1 (Setup):** Clique no botão Play para instalar as dependências e clonar os módulos essenciais do repositório.
3. **Passo 2 (Autenticação):** Insira o ID do seu projeto Google Cloud habilitado no Earth Engine e autorize a montagem do Google Drive.
4. **Passo 3 (Área de Estudo):** Envie um arquivo `.zip` contendo o Shapefile (`.shp`, `.shx`, `.dbf`, `.prj`). O sistema validará a extensão, calculará a área em hectares e apresentará um cartão com estimativa de pixels.
5. **Passo 4 (Parâmetros):** Selecione o sensor, informe os anos desejados, defina o método de composição (mediana inteligente ou melhor cena) e o fator de buffer.
6. **Passo 5 (Execução):** Clique em Play para iniciar o processamento integrado e acompanhar o envio das tarefas para o Earth Engine.
7. **Passo 6 (Resultados):** Visualize o resumo das imagens exportadas com botão direto para acessar a pasta no Google Drive.

---

## 📂 Estrutura do Repositório

```text
ngeo_satellite_downloader/
├── src/                          # Motor modular do downloader
│   ├── __init__.py               # Versão do pacote e exports principais
│   ├── config.py                 # Constantes, coleções do GEE e resoluções
│   ├── vector_ops.py             # Leitura de shapefiles, reprojeção e divisão em tiles
│   ├── sensors.py                # Consultas GEE, máscaras de nuvens e mediana
│   ├── cbers.py                  # Integração com o catálogo e API CBERS (INPE)
│   ├── exporter.py               # Orquestrador do pipeline e tarefas para o Drive
│   └── ui_helpers.py             # Cartões visuais HTML e relatórios
├── ngeo_satellite_downloader.ipynb # Notebook com código oculto (Colab Forms)
├── requirements.txt              # Dependências do ecossistema geoespacial
├── LICENSE                       # Licença MIT
└── README.md                     # Documentação oficial
```

---

## 🛡️ Controle de Qualidade e Boas Práticas

- **Projeção e Datum:** Os produtos são gerados em conformidade com o sistema SIRGAS 2000 / WGS-84 (EPSG:4326).
- **Cobertura de Nuvens:** Em regiões da Amazônia com alta nebulosidade (Janeiro a Maio), recomenda-se utilizar o modo **Análise Anual** restringindo a busca aos meses mais secos (Junho a Outubro).
- **Grandes Áreas:** Se a área de interesse ultrapassar o limiar de 5 milhões de pixels, a rotina aplica automaticamente a divisão em tiles regulares, assegurando a resolução nativa sem perda de fidelidade espectral.

---

## 👨‍💻 Créditos e Apoio Institucional

- **Desenvolvimento e Coordenação:** [Samuel da Costa dos Santos](https://samuelsantos.site/)
- **Instituição:** Núcleo de Geotecnologias (NGEO) — Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Pará (IDEFLOR-Bio) [1].

## 📜 Licença

Distribuído sob a [Licença MIT](LICENSE).

---

[1]: https://ideflorbio.pa.gov.br/telefones/ "Página oficial de contatos do IDEFLOR-Bio — identificação do Núcleo de Geotecnologias (NGEO)"
