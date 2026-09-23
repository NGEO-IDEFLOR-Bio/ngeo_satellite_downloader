# NGEO Satellite Downloader

<p align="center">
  <a href="ngeo_satellite_downloader.ipynb">
    <img src="https://jupyter.org/assets/homepage/main-logo.svg" alt="Abrir o notebook Jupyter" width="150">
  </a>
</p>

<p align="center">
  <strong><a href="ngeo_satellite_downloader.ipynb">Abrir o notebook principal</a></strong>
</p>

**Descrição curta do repositório:** notebook para o Google Colab que automatiza a aquisição de imagens Sentinel-2, Landsat, CBERS-4A e SPOT 2008 sobre áreas definidas por shapefile, com composição, máscara de nuvens, divisão automática em tiles e exportação em GeoTIFF para o Google Drive.

## Finalidade

Este repositório contém um notebook operacional para apoiar fluxos de geotecnologias aplicadas ao território. O notebook recebe uma área de interesse em shapefile, consulta coleções de imagens, seleciona períodos e métodos de composição, trata áreas extensas por meio de tiles e cria tarefas de exportação para o Google Drive.

A ferramenta foi organizada no contexto do **Núcleo de Geotecnologias (NGEO) do Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Pará (IDEFLOR-Bio)**. A página institucional de contatos do IDEFLOR-Bio identifica o NGEO e registra Samuel da Costa dos Santos como seu coordenador [1].

## Conteúdo do repositório

O repositório é intencionalmente mínimo:

- `ngeo_satellite_downloader.ipynb`: notebook principal para execução no Google Colab.
- `LICENSE`: licença MIT.
- `README.md`: documentação e créditos.

## Execução

Abra o [notebook principal](ngeo_satellite_downloader.ipynb), execute as células na ordem e autorize o Google Earth Engine e o Google Drive quando solicitado. Depois, envie um arquivo ZIP contendo o shapefile da área de interesse. O pacote vetorial deve incluir, no mínimo, os arquivos `.shp`, `.shx` e `.dbf`; a inclusão do `.prj` é recomendada.

Na interface, selecione o sensor, informe um ano, uma faixa de anos ou uma lista de anos, escolha o período e o método de composição quando disponíveis e defina a pasta de saída. O botão **INICIAR DOWNLOAD** cria as tarefas de exportação. Os resultados são gravados como GeoTIFF no Google Drive.

Para áreas grandes, o notebook calcula uma estimativa de pixels e divide a extensão em tiles quando necessário. A área exportada também pode ser expandida pelo parâmetro **Buffer**. Esses mecanismos alteram o volume de dados; portanto, a escolha deve ser registrada junto com os produtos gerados.

## Sensores disponíveis

| Sensor | Resolução de exportação | Particularidade |
|---|---:|---|
| Sentinel-2 | 10 m | Composição por semestre ou análise anual por meses. |
| Landsat 5/7/8/9 | 30 m | Seleção de primeiro semestre, segundo semestre ou ambos. |
| CBERS-4A (MUX/WPM) | 2 m | Requer credenciais do portal do INPE durante a sessão. |
| SPOT 2008 — Código Florestal | 5 m | Mosaico específico de 2008. |

## Requisitos e observações

É necessário ter uma conta com acesso ao Google Colab, ao Google Earth Engine e ao Google Drive. O projeto Earth Engine configurado no notebook deve estar acessível à conta que fará a autenticação. O tempo de execução depende da extensão da área, da quantidade de anos e do número de tarefas.

As credenciais do INPE, quando necessárias para CBERS-4A, devem ser digitadas apenas na interface do notebook. Não salve senhas no arquivo, não as registre em logs e não faça commit de credenciais.

Os produtos gerados devem passar por controle de qualidade antes de uso analítico ou publicação. Verifique cobertura espacial, continuidade entre tiles, presença de nuvens e sombras, datas, bandas, resolução, sistema de referência, valores nodata e compatibilidade com o objetivo do estudo.

## Créditos

Desenvolvimento e coordenação: **Samuel da Costa dos Santos** — [samuelsantos.site](https://samuelsantos.site/).

Apoio institucional: **Núcleo de Geotecnologias (NGEO) do IDEFLOR-Bio**, unidade institucional identificada na página oficial de contatos do Instituto [1]. O IDEFLOR-Bio é o Instituto de Desenvolvimento Florestal e da Biodiversidade do Estado do Pará.

## Licença

Este projeto é distribuído sob a [Licença MIT](LICENSE). A licença autoriza uso, cópia, modificação e distribuição, desde que o aviso de copyright e o texto da licença sejam preservados.

## Referências

[1]: https://ideflorbio.pa.gov.br/telefones/ "Página oficial de contatos do IDEFLOR-Bio — identificação do Núcleo de Geotecnologias (NGEO)"
