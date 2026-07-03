# Educa Mais Dashboard

Dashboard em Streamlit para acompanhar operacao comercial, contratos, parceiros, alunos, bolsas, faturamento, comissoes e previsoes da Educa Mais. O projeto centraliza dados vindos do Google Sheets, normaliza informacoes em memoria e entrega abas analiticas para tomada de decisao.

## Visao Geral

O sistema foi desenhado como um painel operacional. Ele le planilhas do Google Sheets, trata datas, valores, status e identificadores de parceiros, aplica filtros globais e distribui os dados entre abas especializadas.

Principais objetivos:

- Monitorar contratos assinados, aguardando e cancelados.
- Visualizar distribuicao geografica de parceiros.
- Acompanhar faturamento, receita liquida e comissoes.
- Projetar cenarios futuros com modelos de previsao.
- Analisar parceiros, captadores, alunos e bolsas.
- Apoiar decisoes comerciais com indicadores e graficos.

## Abas do Dashboard

### Contratos

Mostra KPIs de contratos, metas por periodo, status dos parceiros, contratos por captador e evolucao mensal. A aba usa deduplicacao por parceiro para evitar contagens infladas quando existem multiplas linhas da mesma instituicao.

### Mapa

Exibe parceiros geocodificados em mapa interativo, com cache local em SQLite para evitar chamadas repetidas ao servico de geocodificacao. Tambem apresenta distribuicao por estado, cidade e regioes do Brasil.

### Faturamento

Centraliza indicadores financeiros, incluindo faturamento total, comissao de parceiros, percentual da equipe, receita liquida, evolucao diaria, comparativos mensais e simulador de faturamento adicional.

### Previsoes

Gera projecoes a partir da serie historica de faturamento. O projeto possui suporte a modelos como Prophet, Holt-Winters e XGBoost, quando as dependencias estao instaladas. Tambem inclui ajustes de pos-processamento e insights automaticos.

### Analise de Oportunidade

Ajuda a identificar oportunidades comerciais com base em dados de contratos, regioes, captadores e desempenho dos parceiros.

### Parceiros

Consolida informacoes por parceiro, permitindo analisar situacao contratual, localizacao, tipo de contrato e desempenho.

### Captadores

Apresenta desempenho dos captadores, com rankings, volumes e indicadores relacionados a contratos e resultados comerciais.

### Analise Unitaria

Permite investigar registros especificos em maior detalhe, util para validacao, diagnostico e acompanhamento individual.

### Alunos

Trabalha dados de alunos oriundos da planilha, com indicadores e filtros especificos para acompanhamento academico/comercial.

### Calculo de Comissoes

Organiza regras e calculos de comissao com base em faturamento, parceiros, captadores e percentuais configurados no fluxo da aplicacao.

### Bolsas

Analisa dados da aba de bolsas, incluindo valores, status, datas e indicadores relevantes para acompanhamento das concessoes.

## Estrutura do Projeto

```text
.
|-- app.py                         # Entrada principal do Streamlit e roteamento das abas
|-- auth.py                        # Autenticacao simples por chave de acesso
|-- constants.py                   # Constantes, nomes de colunas, cores e mapas auxiliares
|-- forecasting.py                 # Modelos e utilitarios de previsao
|-- geocoding_service.py           # Geocodificacao e cache SQLite
|-- logging_config.py              # Configuracao de logs estruturados
|-- requirements.txt               # Dependencias Python
|-- verify_advanced_forecast.py    # Verificacao das dependencias avancadas de previsao
|-- services/
|   |-- data.py                    # Carga, normalizacao e parse dos dados
|   `-- storage.py                 # Persistencia local de snapshots/exports
|-- ui/
|   |-- components.py              # Componentes reutilizaveis de UI
|   |-- contracts_tab.py           # Aba Contratos
|   |-- map_tab.py                 # Aba Mapa
|   |-- financial_tab.py           # Aba Faturamento
|   |-- forecast_tab.py            # Aba Previsoes
|   |-- opportunity_tab.py         # Aba Analise de Oportunidade
|   |-- partners_tab.py            # Aba Parceiros
|   |-- captadores_tab.py          # Aba Captadores
|   |-- unit_analysis_tab.py       # Aba Analise Unitaria
|   |-- alunos_tab.py              # Aba Alunos
|   |-- commissions_tab.py         # Aba Calculo de Comissoes
|   `-- bolsas_tab.py              # Aba Bolsas
|-- tests/                         # Testes automatizados
`-- README.md                      # Documentacao do projeto
```

## Configuracao

Crie um arquivo `.env` na raiz do projeto com as variaveis necessarias:

```env
DEFAULT_SHEET_ID=<id_da_planilha_google>
KEY_API=<chave_de_acesso_do_dashboard>
GOOGLE_API_KEY=<opcional_para_integracoes_google>
```

Observacoes:

- `DEFAULT_SHEET_ID` e usado para montar as URLs de exportacao CSV das abas do Google Sheets.
- `KEY_API` protege o acesso ao dashboard por uma autenticacao simples.
- `GOOGLE_API_KEY` deve ser usada apenas quando algum fluxo especifico exigir API key do Google.
- Nunca versione arquivos `.env` com segredos reais.

## Instalacao

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Instale as dependencias:

```bash
pip install -r requirements.txt
```

## Execucao

```bash
streamlit run app.py
```

Depois, acesse:

```text
http://localhost:8501
```

## Testes e Validacao

Rodar a suite de testes:

```bash
python -B -m pytest -q -p no:cacheprovider
```

Validar parse sintatico dos arquivos Python:

```bash
python -B -m compileall -q .
```

Verificar suporte de previsao avancada:

```bash
python verify_advanced_forecast.py
```

## Modelo de Dados Principal

O projeto espera dados vindos de abas do Google Sheets. As principais sao:

- `DADOS`: contratos, parceiros, captadores, localizacao e status.
- `FATURAMENTO`: datas, valores e percentuais de comissao.
- `Bolsas`: dados relacionados a bolsas concedidas.
- `Alunos`: dados de alunos para acompanhamento especifico.

Durante o carregamento, os dados sao normalizados para colunas internas, como:

- `_dt`: data principal do contrato.
- `_status`: status normalizado do contrato.
- `_captador`: captador responsavel.
- `_estado`: UF normalizada.
- `_cidade`: cidade normalizada.
- `_cep`: CEP.
- `_contract_type`: tipo de contrato.
- `_partner`: nome do parceiro.
- `_pid`: identificador deduplicado do parceiro.
- `_data`: data de faturamento.
- `_valor`: valor financeiro normalizado.
- `_comissao`: comissao em formato decimal.

## Arquivos Locais e Gerados

O projeto pode criar arquivos locais durante a execucao:

- `geocache.db`: cache SQLite de geocodificacao.
- `data/`: snapshots e arquivos persistidos localmente.
- `logs/`: logs da aplicacao, quando habilitados.
- `.pytest_cache/` e `__pycache__/`: caches de ferramentas Python.

Esses arquivos normalmente nao devem ser versionados, exceto quando houver uma razao operacional clara.

## Integracoes Externas

- Google Sheets: origem principal dos dados via exportacao CSV.
- Nominatim/OpenStreetMap: geocodificacao de enderecos e cidades.
- Streamlit: interface web do dashboard.
- Plotly: graficos interativos.
- Prophet, Statsmodels e XGBoost: previsoes, conforme disponibilidade das dependencias.

## Observacoes de Seguranca

- O dashboard pode lidar com dados sensiveis de alunos, parceiros e faturamento.
- Segredos devem ficar em variaveis de ambiente ou `.env` local.
- Evite registrar dados pessoais completos em logs.
- Revise permissoes da planilha Google usada como fonte.
- Para producao, considere autenticar usuarios com um provedor adequado em vez de uma chave unica compartilhada.

## Pontos de Atencao Tecnica

- Manter `requirements.txt` sincronizado com imports reais do projeto.
- Evitar versionar caches, bancos locais e arquivos gerados.
- Centralizar parsers de valores monetarios, percentuais e datas para reduzir divergencias entre abas.
- Revisar o pos-processamento das previsoes para diferenciar valores reais de valores ajustados.
- Adicionar testes para abas mais criticas, especialmente faturamento, comissoes, bolsas e alunos.
- Padronizar tratamento de erros externos, principalmente Google Sheets e geocodificacao.

## Roadmap Recomendado

1. Limpar arquivos gerados do versionamento e reforcar `.gitignore`.
2. Corrigir dependencias ausentes ou opcionais no `requirements.txt`.
3. Fortalecer autenticacao e gestao de segredos.
4. Criar uma camada unica de parse e validacao de dados.
5. Melhorar tratamento de falhas de rede e mensagens para o usuario.
6. Expandir testes automatizados para os fluxos financeiros e comerciais.
7. Separar transformacoes de dados, regras de negocio e camada visual.
8. Documentar o contrato esperado das planilhas Google.
9. Adicionar checks de qualidade em CI.
10. Revisar privacidade e retencao de dados pessoais.

## Status Atual

O projeto ja possui uma base funcional, modularizacao parcial, testes automatizados e varias abas de negocio. Os proximos ganhos mais importantes estao em confiabilidade, seguranca, manutencao das dependencias e cobertura de testes para regras financeiras.
