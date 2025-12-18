# Educa Mais Dashboard

Dashboard em `Streamlit` para acompanhar contratos, mapa de parceiros, faturamento e previsões, com estrutura modular e deduplicação por parceiro para métricas consistentes.

## Visão Geral

- Origem dos dados via Google Sheets (CSV export) usando `DEFAULT_SHEET_ID`.
- Abas: `Contratos`, `Mapa`, `Faturamento`, `Previsões`.
- Cache de dados e geocodificação (SQLite) para performance estável.
- Visualizações com `Plotly`, KPIs e simuladores.
- Botão de `Recarregar dados` no menu lateral para limpar cache e recarregar.

## Principais Funcionalidades

- `Contratos`
  - Métricas: `Contratos assinados`, `Contratos aguardando`, `Assinados hoje`, `Assinados este mês`, `Assinados esta semana`.
  - Metas: indicadores `mensal`, `trimestral`, `semestral` com dedup por parceiro.
  - Gráficos: pizza por captador e barras mensais com contagem de parceiros únicos.
  - Status por parceiro com prioridade (`ASSINADO` > `AGUARDANDO` > `CANCELADO`).
- `Mapa`
  - Geocodificação com `Nominatim` e cache `geocache.db`.
  - Dedup por parceiro nos contadores e nos gráficos; tabela de “Estados sem parceiros”.
- `Faturamento`
  - KPIs: total, comissão parceiros, equipe (13%), líquido.
  - Gráficos: linha de faturamento diário e barras por mês.
  - Comparativo: mês atual vs mês passado e simulador de faturamento adicional.
- `Previsões`
  - Modelos: `Prophet (Facebook AI)` e `Holt-Winters (Sazonal)`.
  - Horizonte configurável (1 semana a 1 ano), insights automáticos e ajustes de sustentabilidade.

## Estrutura Modular

```
app.py                        # Orquestra as abas e filtros
constants.py                  # Constantes de colunas, cores e mapas
geocoding_service.py          # Geocodificação com cache SQLite
forecasting.py                # Previsões e insights

services/
  data.py                     # Carregamento/parse de planilhas e utilitários

ui/
  components.py               # Componentes (ex.: gauge)
  contracts_tab.py            # Aba Contratos (KPIs, metas e gráficos)
  map_tab.py                  # Aba Mapa (mapa e gráficos dedup)
  financial_tab.py            # Aba Faturamento (gráficos e simulador)
  forecast_tab.py             # Aba Previsões (modelos e insights)

requirements.txt              # Dependências
verify_advanced_forecast.py   # Verificação rápida de libs de previsão
```

## Modelo de Dados

- Aba `Dados` (→ Interno):
  - `TIMESTAMP` → `'_dt'` (datetime)
  - `CONTRATO ASSINADO` → `'_status'` (`ASSINADO`/`AGUARDANDO`/`CANCELADO`)
  - `CAPTADOR` → `'_captador'`
  - `ESTADO` → `'_estado'`
  - `CIDADE` → `'_cidade'`
  - `CEP` → `'_cep'`
  - `CONTRACT_TYPE` → `'_contract_type'`
  - `COLUNA A (nome do parceiro)` → `'_partner'`
  - Dedup por parceiro: chave `'_pid'` com prioridade `'_partner'` → `'_cep'` → `'_cidade|_estado'`.
- Aba `FATURAMENTO` (→ Interno):
  - `DATA` → `'_data'` (datetime)
  - `VALOR` → `'_valor'` (float)
  - `COMISSÃO` → `'_comissao'` (fração, ex.: 10% → 0.10)

## Instalação

1. Criar ambiente virtual
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
2. Instalar dependências
   ```bash
   pip install -r requirements.txt
   ```

## Configuração

- Criar `.env` na raiz:
  ```env
  DEFAULT_SHEET_ID=<ID_da_sua_planilha_google>
  ```
- Geocodificação: `Nominatim` (OpenStreetMap) com cache `geocache.db` (~1 req/s).

## Execução

```bash
streamlit run app.py
```

- Abra `http://localhost:8501`.

## Filtros e Lógica Temporal

- Menu lateral: intervalo de datas e, opcionalmente, mês (ex.: `10`, `11`, `12`).
- Botão `Recarregar dados`: limpa cache e recarrega todas as abas.
- Semana considera `segunda–domingo` ancorado em `end_date`.

## Previsões

- Séries diárias agregadas, geração de horizontes e insights.
- Ajustes: viés moderado (+5%), piso de sustentabilidade (~40%) e ruído orgânico.

## Boas Práticas

- Não versionar segredos; use `.env`.
- Verificar datas inconsistentes; respeitar limites da Nominatim.

## Verificação Rápida

```bash
python verify_advanced_forecast.py
```

## Cores e Mapa

- Paleta principal: `constants.py` (`COLOR_PRIMARY`, `COLOR_SECONDARY`).
- Mapa `open-street-map` sem token.

## Regiões do Brasil

- UF → Região em `constants.py` (`ESTADO_REGIAO`).

## Notas sobre Datas

- Parser tolerante a `dd/mm/aaaa HH:MM:SS`.
- Datas fora de faixa podem ser saneadas conforme `todo.md`.

## Roadmap

- Consulte `todo.md` para evolução e otimizações.

---

Feito com ❤️ para acelerar decisões e dar visibilidade ao desempenho comercial.
