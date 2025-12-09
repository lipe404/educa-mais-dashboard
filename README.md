# Educa Mais Dashboard 🚀📊

Um dashboard interativo em `Streamlit` para monitorar contratos, desempenho comercial, distribuição geográfica e faturamento, com previsões assistidas por modelos de série temporal (Prophet e Holt‑Winters).

## ✨ Visão Geral
- Origem dos dados via Google Sheets (CSV export) usando `DEFAULT_SHEET_ID`.
- Abas: `Contratos`, `Mapa`, `Faturamento`, `Previsões`.
- Cache inteligente de dados e geocodificação (SQLite) para performance estável.
- Visualizações com `Plotly` e métricas operacionais de fácil leitura.

## 🧩 Principais Funcionalidades
- `Contratos`
  - Métricas: `Contratos assinados`, `Contratos aguardando`, `Assinados este mês`, `Assinados esta semana`.
  - Metas: indicadores `mensal`, `trimestral`, `semestral`.
  - Gráfico: barras mensais de contratos assinados (sem cancelados), rótulos em PT‑BR.
  - Pizza por `captador` e barras de status (Assinados vs Aguardando).
- `Mapa`
  - Geocodificação com `Nominatim` e cache local `geocache.db`.
  - Mapa `open-street-map` e gráficos por `Estado`, `Cidade` e `Região`.
- `Faturamento`
  - Métricas: total, comissão parceiros, comissão equipe (13%), líquido.
  - Linha de faturamento diário.
- `Previsões`
  - Modelos: `Prophet (Facebook AI)` e `Holt-Winters (Sazonal)`.
  - Horizonte configurável (1 semana a 1 ano).
  - Ajustes de otimismo, piso de sustentabilidade e ruído orgânico.
  - Geração de insights em linguagem natural.

## 🗂️ Estrutura do Projeto
```
app.py                  # App Streamlit principal e UI das abas
constants.py            # Constantes de colunas, cores e mapas de estados
forecasting.py          # Previsão (Prophet / Holt-Winters) e insights
geocoding_service.py    # Serviço de geocodificação com cache SQLite
requirements.txt        # Dependências do projeto
verify_advanced_forecast.py # Script simples para verificar libs de previsão
```

## 🧾 Modelo de Dados
- Aba `Dados`:
  - Fonte → Interno
  - `TIMESTAMP` → `'_dt'` (datetime, `dayfirst=True` com tolerância)
  - `CONTRATO ASSINADO` → `'_status'` (normalizado: `ASSINADO`, `AGUARDANDO`, `CANCELADO`)
  - `CAPTADOR` → `'_captador'`
  - `ESTADO` → `'_estado'`
  - `CIDADE` → `'_cidade'`
- Aba `FATURAMENTO`:
  - `DATA` → `'_data'` (datetime)
  - `VALOR` → `'_valor'` (float)
  - `COMISSÃO` → `'_comissao'` (percentual convertido para fração, ex.: 10% → 0.10)

## 🔧 Instalação
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

## ⚙️ Configuração
- Criar arquivo `.env` na raiz com:
  ```env
  DEFAULT_SHEET_ID=<ID_da_sua_planilha_google>
  ```
- Geocodificação: usa `Nominatim` (OpenStreetMap). Cache local em `geocache.db`.
  - O serviço respeita ~1 requisição/segundo.

## ▶️ Execução
```bash
streamlit run app.py
```
- Abra o link local gerado (tipicamente `http://localhost:8501`).

## 🧭 Filtros e Lógica Temporal
- Filtro lateral de intervalo de datas e, opcionalmente, de mês (ex.: `10`, `11`, `12`).
- Métricas de metas derivam do mês em foco (`end_date` + seleção de mês).
- “Assinados esta semana” considera `segunda–domingo` baseado em `end_date`.

## 📈 Previsões
- `forecasting.py` agrega diariamente e gera datas futuras.
- `Prophet` exige instalação; `Holt‑Winters` usa `statsmodels`.
- Ajustes aplicados:
  - Viés otimista moderado para alinhar à média recente (+5%).
  - Piso de sustentabilidade (~40% da média recente) para horizontes longos.
  - Ruído orgânico para quebrar padrões rígidos.

## 🛡️ Boas Práticas
- Não versionar segredos; use `.env`.
- Verificar entradas de data inconsistentes (ex.: anos inválidos).
- Respeitar limites da Nominatim; evite loops agressivos.

## 🧪 Verificação Rápida
- Checar instalação de bibliotecas de previsão:
  ```bash
  python verify_advanced_forecast.py
  ```

## 📍 Cores e Mapa
- Paleta principal em `constants.py` (`COLOR_PRIMARY`, `COLOR_SECONDARY`).
- Mapa usa `open-street-map` sem token.

## 🗺️ Regiões do Brasil
- Mapeadas via UF → Região em `constants.py` (`ESTADO_REGIAO`).

## 🗓️ Notas sobre Datas
- O parser tolera formatos `dd/mm/aaaa HH:MM:SS`.
- Registros com anos fora de faixa podem ser filtrados no futuro (ver `todo.md`).

## 📚 Roadmap
- Consulte `todo.md` para ideias de evolução e otimizações.

---
Feito com ❤️ para acelerar decisões e dar visibilidade ao desempenho comercial.

