# Column Names (Source)
COL_SRC_TIMESTAMP = "TIMESTAMP"
COL_SRC_STATUS = "CONTRATO ASSINADO"
COL_SRC_CAPTADOR = "CAPTADOR"
COL_SRC_STATE = "ESTADO"
COL_SRC_CITY = "CIDADE"
COL_SRC_CEP = "CEP"
COL_SRC_VALOR = "VALOR"
COL_SRC_COMISSAO = "COMISSÃO"
COL_SRC_DATA = "DATA"
COL_SRC_CONTRACT_TYPE = "CONTRACT_TYPE"
COL_SRC_FINANCIAL_TYPE = "TIPO"
COL_SRC_PARTNER = "PARCEIRO"
COL_SRC_STUDENT_NAME = "NOME DO ALUNO"
COL_SRC_COURSE = "CURSO"
COL_SRC_CPF = "CPF"
COL_SRC_DOCUMENTS = "DOCUMENTOS"
COL_SRC_SISTEC = "SISTEC"
COL_SRC_CARD = "CARTEIRINHA"
COL_SRC_ALUNOS_CITY = "CIDADE"    # Coluna J da aba ALUNOS
COL_SRC_ALUNOS_STATE = "ESTADO"   # Coluna K da aba ALUNOS
COL_SRC_GEN_FIRST_NAME = "First Name"
COL_SRC_GEN_LAST_NAME = "Last Name"
COL_SRC_GEN_CPF = "cpf"
COL_SRC_GEN_PHONE = "phone"
COL_SRC_GEN_EMAIL = "email"
COL_SRC_GEN_ZIP = "zip"
COL_SRC_GEN_CITY = "cidade"
COL_SRC_GEN_STATE = "estado"
COL_SRC_GEN_ADDRESS = "endereço"
COL_SRC_GEN_NEIGHBORHOOD = "bairro"
COL_SRC_GEN_COUNTRY = "Country"

# Column Names (Internal)
COL_INT_DT = "_dt"
COL_INT_STATUS = "_status"
COL_INT_CAPTADOR = "_captador"
COL_INT_STATE = "_estado"
COL_INT_CITY = "_cidade"
COL_INT_CEP = "_cep"
COL_INT_VALOR = "_valor"
COL_INT_COMISSAO = "_comissao"
COL_INT_DATA = "_data"
COL_INT_REGION = "_regiao"
COL_INT_CONTRACT_TYPE = "_contract_type"
COL_INT_PARTNER = "_partner"
COL_INT_FINANCIAL_TYPE = "_financial_type"
COL_INT_STUDENT_NAME = "_student_name"
COL_INT_COURSE = "_course"
COL_INT_CPF = "_cpf"
COL_INT_DOCUMENTS = "_documents"
COL_INT_SISTEC = "_sistec"
COL_INT_CARD = "_card"
COL_INT_ALUNOS_CITY = "_alunos_city"    # Cidade do aluno (aba ALUNOS, col J)
COL_INT_ALUNOS_STATE = "_alunos_state"  # Estado do aluno (aba ALUNOS, col K)
COL_INT_GEN_FIRST_NAME = "_gen_first_name"
COL_INT_GEN_LAST_NAME = "_gen_last_name"
COL_INT_GEN_CPF = "_gen_cpf"
COL_INT_GEN_PHONE = "_gen_phone"
COL_INT_GEN_EMAIL = "_gen_email"
COL_INT_GEN_ZIP = "_gen_zip"
COL_INT_GEN_CITY = "_gen_city"
COL_INT_GEN_STATE = "_gen_state"
COL_INT_GEN_ADDRESS = "_gen_address"
COL_INT_GEN_NEIGHBORHOOD = "_gen_neighborhood"
COL_INT_GEN_COUNTRY = "_gen_country"

# Bolsas Financial Columns (Internal)
COL_INT_BOLSA_PARCEIRO = "_bolsa_parceiro"
COL_INT_BOLSA_VALOR = "_bolsa_valor"
COL_INT_BOLSA_COTAS = "_bolsa_cotas"
COL_INT_BOLSA_DATA = "_bolsa_data"

# Bolsas Quantidade Columns (Internal)
COL_INT_BOLSAQTD_NOME = "_bolsaqtd_nome"
COL_INT_BOLSAQTD_QNTD = "_bolsaqtd_qntd"

# Status Values
STATUS_ASSINADO = "ASSINADO"
STATUS_AGUARDANDO = "AGUARDANDO"
STATUS_CANCELADO = "CANCELADO"

# Contract Types
CONTRACT_TYPE_NORMAL = "Contrato Normal"
CONTRACT_TYPE_50 = "Contrato 50%"
CONTRACT_TYPE_POS = "Contrato Pós-Graduação"
CONTRACT_TYPE_BOLSA = "Contrato Bolsa"

# UI Colors
COLOR_PRIMARY = "#2d9fff"
COLOR_SECONDARY = "#ff2d95"
COLOR_BG_DARK = "#0b1437"
COLOR_FORECAST = "#00ff7f"  # Spring Green for forecast

# Map Configuration
MAP_ZOOM_DEFAULT = 3.5
MAP_LAT_DEFAULT = -14.235
MAP_LON_DEFAULT = -51.9253
MAP_STYLE = "mapbox://styles/mapbox/light-v10"

# Regional Data
ESTADO_REGIAO = {
    "AC": "Norte",
    "AL": "Nordeste",
    "AP": "Norte",
    "AM": "Norte",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "DF": "Centro-Oeste",
    "ES": "Sudeste",
    "GO": "Centro-Oeste",
    "MA": "Nordeste",
    "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "MG": "Sudeste",
    "PA": "Norte",
    "PB": "Nordeste",
    "PR": "Sul",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "RJ": "Sudeste",
    "RN": "Nordeste",
    "RS": "Sul",
    "RO": "Norte",
    "RR": "Norte",
    "SC": "Sul",
    "SP": "Sudeste",
    "SE": "Nordeste",
    "TO": "Norte",
}

# Financial Constants
COMMISSION_RATE_TEAM = 0.13  # 13% fixed commission for the team
GOAL_MONTHLY_CONTRACTS = 30  # Default monthly goal for contracts

# Forecasting Algorithms
ALGORITHM_PROPHET = "Prophet (Facebook AI)"
ALGORITHM_HOLT_WINTERS = "Holt-Winters (Sazonal)"
ALGORITHM_XGBOOST = "XGBoost (Gradient Boosting)"

# Forecasting Insights
INSIGHT_GROWTH = "Crescimento acelerado"
INSIGHT_SLOWDOWN = "Desaceleração recente"
INSIGHT_STABLE = "Estabilidade"
INSIGHT_POSITIVE = (
    "O modelo (ajustado com otimismo) prevê uma performance sólida para o período."
)
INSIGHT_NEGATIVE = "O modelo prevê uma leve queda. Verifique campanhas ou sazonalidade."
INSIGHT_NEUTRAL = "A previsão indica manutenção do ritmo atual de vendas."

# Date & Time
MONTH_NAMES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

# Educational Courses & Areas
COURSES = {
    "Área da Saúde": [
        "Técnico em Agente Comunitário de Saúde",
        "Técnico em Análises Clínicas",
        "Técnico em Cuidados de Idosos",
        "Técnico em Enfermagem",
        "Técnico em Equipamentos Biomédicos",
        "Técnico em Estética",
        "Técnico em Farmácia",
        "Técnico em Gerência em Saúde",
        "Técnico em Nutrição e Dietética",
        "Técnico em Química",
        "Técnico em Radiologia",
        "Técnico em Saúde Bucal",
        "Técnico em Veterinária",
    ],
    "Administração e Gestão": [
        "Técnico em Administração",
        "Técnico em Contabilidade",
        "Técnico em Logística",
        "Técnico em Marketing",
        "Técnico em Qualidade",
        "Técnico em Recursos Humanos",
        "Técnico em Secretariado Escolar",
        "Técnico em Segurança do Trabalho",
        "Técnico em Serviços Jurídicos",
        "Técnico em Transações Imobiliárias",
        "Técnico em Vendas",
        "Curso Técnico em Eventos",
    ],
    "Engenharia e Manutenção": [
        "Técnico em Automação Industrial",
        "Técnico em Eletromecânica",
        "Técnico em Eletrotécnica",
        "Técnico em Eletrônica",
        "Técnico em Manutenção de Máquinas Industriais",
        "Técnico em Máquinas Pesadas",
        "Técnico em Metalurgia",
        "Técnico em Refrigeração e Climatização",
        "Técnico em Soldagem",
        "Técnico em Manutenção de Máquinas Navais",
    ],
    "Construção e Infraestrutura": [
        "Técnico em Agrimensura",
        "Técnico em Edificações",
        "Técnico em Mineração",
        "Técnico em Segurança do Trabalho",
        "Técnico em Prevenção e Combate ao Incêndio",
        "Curso Técnico em Defesa Civil",
        "Curso Técnico em Trânsito",
    ],
    "Tecnologia e Informática": [
        "Técnico em Biotecnologia",
        "Técnico em Design Gráfico",
        "Técnico em Desenvolvimento de Sistemas",
        "Técnico em Informática para Internet",
        "Técnico em Redes de Computadores",
        "Técnico em Sistemas de Energia Renovável",
        "Técnico em Telecomunicações",
    ],
    "Meio Ambiente e Agropecuária": [
        "Técnico em Agricultura",
        "Técnico em Agropecuária",
        "Técnico em Agroindústria",
        "Técnico em Aquicultura",
        "Técnico em Meio Ambiente",
    ],
    "Área de Serviços": [
        "Técnico em Gastronomia",
        "Técnico em Óptica",
        "Técnico em Designer de Interiores",
        "Técnico em Guia de Turismo",
    ],
    "EJA": ["EJA Fundamental", "EJA Médio"],
}

AREA_TO_CNAE_LETTER = {
    "Área da Saúde": "Q",
    "Administração e Gestão": "N",
    "Engenharia e Manutenção": "C",
    "Construção e Infraestrutura": "F",
    "Tecnologia e Informática": "J",
    "Meio Ambiente e Agropecuária": "A",
    "Área de Serviços": "S",
    "EJA": "",
}

# UI Labels
APP_TITLE = "Educa Mais Dashboard"
UI_LABEL_TOTAL_REVENUE = "Faturamento total"
UI_LABEL_PARTNER_COMMISSION = "Comissão parceiros"
UI_LABEL_TEAM_COMMISSION = "Comissão equipe"
UI_LABEL_NET_REVENUE = "Líquido empresa"
UI_LABEL_DAILY_REVENUE = "Faturamento diário"
UI_LABEL_MONTHLY_REVENUE = "Faturamento por mês"
UI_LABEL_SIGNED_CONTRACTS = "Contratos assinados"
UI_LABEL_WAITING_CONTRACTS = "Contratos aguardando"
UI_LABEL_SIGNED_MONTH = "Assinados este mês"
UI_LABEL_SIGNED_WEEK = "Assinados esta semana"
UI_LABEL_SIGNED_TODAY = "Assinados hoje"

# UI General
UI_LABEL_ALL = "Todos"
UI_LABEL_CONTRACT_TYPE = "Tipo de Contrato"
UI_LABEL_FILTER_REGION = "Filtrar por Região"
UI_LABEL_FILTER_STATE = "Filtrar por Estado"
UI_LABEL_FILTER_MONTH = "Filtrar por mês"
UI_LABEL_RELOAD_DATA = "Recarregar dados"
UI_LABEL_DATE_RANGE = "Intervalo de datas"

# Contract Types (UI)
CONTRACT_TYPE_UI_TECNICO = "Técnico"
CONTRACT_TYPE_UI_POS = "Pós-Graduação"
CONTRACT_TYPE_UI_BOLSAS = "Bolsas"

# Internal Financial Types
FINANCIAL_TYPE_TECNICO = "TECNICO"
FINANCIAL_TYPE_POS = "POS"

# Tab Names
TAB_NAME_CONTRACTS = "Contratos"
TAB_NAME_MAP = "Mapa"
TAB_NAME_FINANCIAL = "Faturamento"
TAB_NAME_FORECAST = "Previsões"
TAB_NAME_OPPORTUNITY = "Análise de Oportunidade"
TAB_NAME_PARTNERS = "Parceiros"
TAB_NAME_STUDENTS = "Alunos"
TAB_NAME_UNIT_ANALYSIS = "Análise Unitária"
TAB_NAME_COMMISSIONS = "Cálculo de Comissões"
TAB_NAME_BOLSAS = "Bolsas"
TAB_NAME_CAPTADORES = "Captadores"

# Contracts Tab UI
UI_LABEL_CONTRACTS_SIGNED = "Contratos assinados"
UI_LABEL_CONTRACTS_WAITING = "Contratos aguardando"
UI_LABEL_SIGNED_MONTH = "Assinados este mês"
UI_LABEL_SIGNED_WEEK = "Assinados esta semana"
# UI_LABEL_SIGNED_TODAY already exists
UI_LABEL_VS_LAST_WEEK_UP = "Acima vs semana passada"
UI_LABEL_VS_LAST_WEEK_DOWN = "Falta p/ igualar semana passada"
UI_LABEL_VS_LAST_MONTH_UP = "Acima vs mês passado"
UI_LABEL_VS_LAST_MONTH_DOWN = "Falta p/ igualar mês passado"
UI_LABEL_GOAL_MONTHLY = "Meta mensal 30"
UI_LABEL_GOAL_QUARTERLY = "Meta trimestral 90"
UI_LABEL_GOAL_SEMIANNUAL = "Meta semestral 180"
UI_LABEL_CONTRACTS_BY_CAPTADOR = "Contratos por captador"
UI_LABEL_CAPTADOR = "Captador"
UI_LABEL_PARTNERS = "Parceiros"
UI_LABEL_SIGNED_VS_WAITING = "Assinados vs Aguardando"
UI_LABEL_STATUS = "Status"
UI_LABEL_QUANTITY = "Quantidade"
UI_LABEL_SIGNED_BY_MONTH = "Contratos assinados por mês"
UI_LABEL_MONTH = "Mês"
UI_LABEL_CONTRACTS = "Contratos"
UI_LABEL_DAILY_SALES = "Vendas Diárias"

# Financial Tab UI
UI_LABEL_REVENUE_TODAY = "Faturamento hoje"
UI_LABEL_REVENUE_WEEK = "Faturamento essa semana"
UI_LABEL_REVENUE_MONTH = "Faturamento este mês"
# UI_LABEL_TOTAL_REVENUE already exists
# UI_LABEL_PARTNER_COMMISSION already exists
UI_LABEL_TEAM_COMMISSION_BASE = "Comissão equipe"
# UI_LABEL_NET_REVENUE already exists
# UI_LABEL_DAILY_REVENUE already exists
# UI_LABEL_MONTHLY_REVENUE already exists
UI_LABEL_REVENUE_CURRENT_MONTH = "Faturamento mês atual"
UI_LABEL_GOAL_LAST_MONTH = "Meta mês passado"
UI_LABEL_VS_LAST_MONTH_REV_UP = "Acima do mês passado"
UI_LABEL_VS_LAST_MONTH_REV_DOWN = "Falta para igualar mês passado"
UI_LABEL_SIMULATOR_TITLE = "### Simulador de faturamento adicional"
UI_LABEL_SIMULATOR_INPUT = "Valor adicional (R$)"
UI_LABEL_SIMULATOR_TOTAL = "Faturamento total (simulado)"
UI_LABEL_SIMULATOR_PARTNER = "Comissão parceiros (simulado)"
# (simulado) appended dynamically or just base
UI_LABEL_SIMULATOR_TEAM = "Comissão equipe"
UI_LABEL_SIMULATOR_NET = "Líquido empresa (simulado)"
UI_LABEL_SIMULATOR_VS_LAST_UP = "Acima do mês passado (simulado)"
UI_LABEL_SIMULATOR_VS_LAST_DOWN = "Falta p/ igualar mês passado (simulado)"

# Forecast Tab UI
UI_LABEL_ALGORITHM = "Algoritmo"
UI_LABEL_HORIZON = "Horizonte"
UI_LABEL_HORIZON_1W = "1 Semana"
UI_LABEL_HORIZON_2W = "2 Semanas"
UI_LABEL_HORIZON_3W = "3 Semanas"
UI_LABEL_HORIZON_1M = "1 Mês"
UI_LABEL_HORIZON_3M = "3 Meses"
UI_LABEL_HORIZON_6M = "6 Meses"
UI_LABEL_HORIZON_1Y = "1 Ano"
UI_LABEL_NEW_CONTRACTS = "Novos Contratos"
UI_LABEL_TOTAL_EXPECTED = "Total Final Esperado"
UI_LABEL_FORECAST_CONTRACTS_TITLE = "Previsão de Novos Contratos Diários"
UI_LABEL_HISTORY = "Histórico"
UI_LABEL_FORECAST = "Previsão"
UI_LABEL_FORECAST_REVENUE = "Faturamento previsto"
UI_LABEL_FORECAST_REVENUE_TITLE = "Previsão de Faturamento Diário"
UI_LABEL_ERROR_FORECAST = "Erro ao gerar previsão"
UI_LABEL_TIP_INSTALL = (
    "Dica: Verifique se as bibliotecas 'prophet' e 'statsmodels' estão instaladas."
)

# Partners Tab UI
UI_LABEL_ACCESS_KEY = "Chave de acesso"
UI_LABEL_ENTER_KEY_MSG = "Digite a chave de acesso para visualizar a análise."
UI_LABEL_PARTNERS_RANKING_TITLE = "### Ranking de Parceiros por Vendas e Faturamento"
UI_LABEL_NO_REVENUE_DATA = "Nenhum dado de faturamento disponível."
UI_LABEL_NO_PARTNERS_FOUND = "Nenhum parceiro encontrado nos dados."
UI_LABEL_TOP_10_SALES = "Top 10 Parceiros por Número de Vendas"
UI_LABEL_PARTNER = "Parceiro"
UI_LABEL_NUM_SALES = "Número de Vendas"
UI_LABEL_TOP_10_REVENUE = "Top 10 Parceiros por Faturamento Total"
UI_LABEL_TOTAL_REVENUE_CURRENCY = "Faturamento Total (R$)"
UI_LABEL_TOTAL_PARTNERS = "Total de Parceiros"
UI_LABEL_PARTNER_MOST_SALES = "Parceiro com Mais Vendas"
UI_LABEL_PARTNER_MOST_REVENUE = "Parceiro com Maior Faturamento"
UI_LABEL_PARTNERS_DETAILS_TITLE = "### Detalhes dos Parceiros"

# Opportunity Tab UI
UI_LABEL_OPP_TAB_OVERVIEW = "Visão Geral"
UI_LABEL_OPP_TAB_DETAILED = "Análise Detalhada (Geral)"
UI_LABEL_OPP_TAB_COURSE = "Análise por Curso"
UI_LABEL_STATES = "Estados"
UI_LABEL_LOADING_OPP = "Carregando análise de oportunidade..."
UI_LABEL_POP_MIN = "População mínima (2022)"
UI_LABEL_ONLY_MISSING = "Somente cidades sem parceiros"
UI_LABEL_NO_CITIES_FOUND = "Nenhuma cidade encontrada com os filtros atuais."
UI_LABEL_TOTAL_CITIES_CANDIDATE = "Total de cidades candidatas"
UI_LABEL_TOP_30_POP_MISSING = "Top 30 cidades por população sem presença"
UI_LABEL_MAP_GEOCODING = "Cidades no mapa (geocodificação)"
UI_LABEL_MAP_OPP_POP = "Mapa de oportunidade por população"
UI_LABEL_RANKING_CITIES = "### Ranking de cidades"
UI_LABEL_ECON_ANALYSIS_TITLE = "### Análise Econômica Geral"
UI_LABEL_ECON_ANALYSIS_INFO = "Esta análise considera o número total de unidades locais (empresas) como indicador de potencial econômico."
UI_LABEL_GENERAL_AREA = "Geral (Todas as Áreas)"
UI_LABEL_AREA_INTEREST = "Área de Interesse (Peso)"
UI_LABEL_EXECUTE_ANALYSIS = "Executar Análise Detalhada"
UI_LABEL_COLLECTING_INDICATORS = "Coletando indicadores econômicos (pode demorar)..."
UI_LABEL_NO_DATA_SUFFICIENT = "Sem dados suficientes."
UI_LABEL_TOTAL_CITIES_ANALYZED = "Total de cidades analisadas"
UI_LABEL_TOTAL_LOCAL_UNITS = "Total de unidades locais (Brasil/Sel)"
UI_LABEL_TOP_30_ECON_POTENTIAL = "Top 30 cidades por potencial econômico"
UI_LABEL_MARKET_ANALYSIS_TITLE = "### Análise de Mercado por Curso Específico"
UI_LABEL_MARKET_ANALYSIS_SUBTITLE = "Identificação de polos potenciais baseada em densidade populacional e atividade econômica."
UI_LABEL_SELECT_AREA = "Selecione a Área"
UI_LABEL_SELECT_COURSE = "Selecione o Curso"
UI_LABEL_ANALYZE_POTENTIAL = "Analisar Potencial do Curso"
UI_LABEL_ANALYZING_MARKET = (
    "Analisando mercado e gerando insights para {course} ({area})..."
)
UI_LABEL_AI_ANALYSIS_TITLE = "#### 🤖 Análise de Proximidade e Contexto (IA)"
UI_LABEL_TOP_SUGGESTED_CITIES = "#### Top Cidades Sugeridas"
UI_LABEL_COL_POPULATION = "População"
UI_LABEL_COL_TOTAL_COMPANIES = "Empresas Totais"
UI_LABEL_COL_SCORE = "Score"
UI_LABEL_MAP_POTENTIAL_TITLE = "Mapa de Potencial: {course}"
UI_LABEL_GEOCODING_WARNING = "Não foi possível geocodificar as cidades do topo do ranking. Verifique a conexão com o serviço de mapas. ({count} falhas)"

# Geo Clustering
UI_LABEL_CLUSTERING_TITLE = "### Geo Clustering (DBSCAN)"
UI_LABEL_CLUSTERING_DESC = "Identificação de 'polos' naturais de oportunidade agrupando cidades próximas com alto potencial."
UI_LABEL_EPS_KM = "Distância Máxima (km)"
UI_LABEL_MIN_SAMPLES = "Mínimo de Cidades no Cluster"
UI_LABEL_RUN_CLUSTERING = "Executar Clustering"
UI_LABEL_CLUSTERING_MAP_TITLE = "Clusters de Oportunidade"
UI_LABEL_CLUSTERING_NO_DATA = "Nenhum cluster encontrado com os parâmetros atuais."

# Regression Analysis
UI_LABEL_REGRESSION_TITLE = "### Análise de Regressão (Fatores de Venda)"
UI_LABEL_REGRESSION_DESC = "Modelo estatístico para identificar o impacto de População e Empresas no volume de vendas."
UI_LABEL_REGRESSION_R2 = "R² (Poder Explicativo)"
UI_LABEL_REGRESSION_COEF_POP = "Impacto População"
UI_LABEL_REGRESSION_COEF_EMP = "Impacto Empresas"
UI_LABEL_REGRESSION_SCATTER_TITLE = "Regressão Linear: Vendas Reais vs Previstas"
UI_LABEL_OPP_TAB_CLUSTERING = "Geo Clustering"
UI_LABEL_OPP_TAB_REGRESSION = "Análise de Regressão"

# Map Tab UI
UI_LABEL_STATES_PRESENT = "Estados presentes"
UI_LABEL_CITIES_PRESENT = "Cidades presentes"
UI_LABEL_MAP_DISTRIBUTION_TITLE = "Distribuição Geográfica de Contratos Assinados"
UI_LABEL_PARTNERS_BY_STATE = "Parceiros por estado"
UI_LABEL_PARTNERS_BY_CITY = "Parceiros por cidade"
UI_LABEL_PARTNERS_BY_REGION = "Parceiros por região"
UI_LABEL_STATES_WITHOUT_PARTNERS = "### Estados sem parceiros"
UI_LABEL_COL_STATE = "Estado"
UI_LABEL_COL_CITY = "Cidade"
UI_LABEL_COL_REGION = "Região"
UI_LABEL_COL_PARTNERS = "Parceiros"

# Services
SHEET_NAME_DATA = "DADOS"
SHEET_NAME_FINANCIAL = "FATURAMENTO"
SHEET_NAME_STUDENTS = "ALUNOS"
SHEET_NAME_STUDENTS_GENERAL = "ALUNOS_GERAL"
SHEET_NAME_BOLSAS = "CONTRATO BOLSAS - PARCEIRO"
SHEET_NAME_BOLSAS_CONTROLE = "CONTROLE DE BOLSAS"
SHEET_NAME_BOLSAS_QNTD = "QUANTIDADE BOLSAS"
GID_STUDENTS_GENERAL = "1729892597"
GID_STUDENTS = "228156415"
GID_BOLSAS = "1428863701"
GID_BOLSAS_CONTROLE = "1673732423"
GID_BOLSAS_QNTD = "284510609"
DEFAULT_REGION_OTHER = "Outros"
ERR_MSG_MISSING_COLUMNS = "Erro: Colunas faltando na planilha: {columns}"
ERR_MSG_LOADING_SHEET = "Erro ao carregar aba '{sheet_name}': {error}"

# Forecasting
ERR_MSG_PROPHET_NOT_INSTALLED = "Biblioteca Prophet não instalada."
ERR_MSG_STATSMODELS_NOT_INSTALLED = "Biblioteca statsmodels não instalada."
LABEL_FORECAST_TYPE_FORECAST = "Previsão"
LABEL_FORECAST_TYPE_HISTORY = "Histórico"
COL_FORECAST_TYPE = "Type"
MSG_INSUFFICIENT_DATA = "Dados insuficientes para análise detalhada (mínimo 2 semanas)."
MSG_SMART_ANALYSIS_TITLE = "### 🧠 Análise Inteligente\n\n"
MSG_RECENT_TREND = "**Tendência Recente (7 dias):**"
MSG_FORECAST_NEXT_DAYS = "**Previsão para os próximos {horizon_days} dias:**\n"
MSG_ESTIMATED_TOTAL = "**Total estimado:**"
MSG_EXPECTED_DAILY_AVG = "**Média diária esperada:**"
MSG_INSIGHT_PREFIX = "> **Insight:**"
LABEL_NEW_CONTRACTS = "novos contratos"

# API URLs
API_URL_IBGE_MUNICIPIOS = (
    "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
)
API_URL_IBGE_MALHA_MUNICIPO = "https://servicodados.ibge.gov.br/api/v3/malhas/municipios/{id}?formato=application/vnd.geo+json"
API_URL_IBGE_MUNICIPIOS_UF = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios?orderBy=nome"
API_URL_SIDRA_POP_2022 = (
    "https://apisidra.ibge.gov.br/values/t/6579/n6/{ids}/v/9324/p/last"
)
API_URL_SIDRA_POP_2022_ALL = (
    "https://apisidra.ibge.gov.br/values/t/6579/n6/all/v/9324/p/last"
)

# Geocoding
GEO_DB_PATH = "geocache.db"
GEO_USER_AGENT = "educa-mais-dashboard-v2"
GEO_COUNTRY = "Brasil"

# Captadores Tab UI Labels
UI_LABEL_UNIDENTIFIED = "Não identificado"
UI_LABEL_EXCLUDE_UNIDENTIFIED = "Omitir parceiros sem captador cadastrado"
UI_LABEL_CAPTADORES_TAB_HEADER = "Análise de Captadores"
UI_LABEL_CAPTADORES_ACTIVE = "Captadores Ativos"
UI_LABEL_PARTNERS_CAPTURED = "Total Parceiros Captados"
UI_LABEL_CAPTADORES_WAITING = "Contratos Aguardando"
UI_LABEL_AVG_PARTNERS = "Média por Captador"
UI_LABEL_CAPTADORES_PERF_TITLE = "Performance Geral (Parceiros Assinados)"
UI_LABEL_CAPTADORES_PERF_DESC = "Comparativo do número de parceiros únicos captados."
UI_LABEL_CAPTADORES_WAITING_TITLE = "Contratos Aguardando por Captador"
UI_LABEL_CAPTADORES_WAITING_DESC = "Quantidade de contratos aguardando assinatura por captador."
UI_LABEL_CAPTADORES_REVENUE_TITLE = "Faturamento por Captador"
UI_LABEL_CAPTADORES_REVENUE_DESC = "Faturamento total gerado pelos parceiros atribuídos ao captador."
UI_LABEL_NO_DATA_PERIOD = "Sem dados para o período selecionado."
UI_LABEL_CAPTADOR_COLUMN = "Captador"
UI_LABEL_PARTNERS_CAPTURED_COLUMN = "Parceiros Captados"
UI_LABEL_WAITING_CONTRACTS_COLUMN = "Contratos Aguardando"
UI_LABEL_REVENUE_COLUMN = "Faturamento (R$)"
UI_LABEL_PARTNER_UNIQUE = "Parceiros Únicos"
UI_LABEL_REVENUE_TOTAL = "Faturamento Total"

