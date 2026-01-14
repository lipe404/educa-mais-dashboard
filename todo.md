# Checklist de Melhorias e Implementações - Educa Mais Dashboard

Este documento contém uma lista exaustiva de sugestões de melhorias para o sistema, categorizadas por área de atuação e páginas específicas. O objetivo é elevar o nível do projeto em termos de usabilidade, performance, segurança e funcionalidades.

## 1. UX (Experiência do Usuário)

| #  | Item                            | Estado Atual                                                       | Como Melhorar                                                                                      | Estado Pós-Implementação                                                                 |
| -- | ------------------------------- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| 1  | Feedback de Carregamento Global | Carregamento de abas pesadas pode parecer travado.                 | Implementar `st.spinner()` ou placeholders (skeletons) granulares em cada aba.                   | Usuário sabe exatamente qual componente está carregando.                                  |
| 2  | Persistência de Filtros        | Filtros resetam ao recarregar a página (F5).                      | Utilizar `st.query_params` para salvar estado dos filtros na URL.                                | Usuário pode compartilhar links com filtros aplicados e não perde contexto ao recarregar. |
| 3  | Tratamento de Erros Amigável   | Erros de Python (tracebacks) podem aparecer na tela.               | Envolver renderizações em blocos `try-except` e mostrar mensagens amigáveis com `st.error`. | Usuário vê "Erro ao carregar dados" em vez de `KeyError: 'coluna'`.                     |
| 4  | Tooltips Explicativos           | Métricas e gráficos carecem de contexto detalhado.               | Adicionar parâmetro `help="Explicação..."` em métricas e inputs.                             | Usuário entende o significado de cada KPI ao passar o mouse.                               |
| 5  | Navegação por Teclado         | Foco e navegação via Tab não otimizados.                        | Revisar ordem dos widgets e usar `st.form` onde aplicável para submissão em lote.              | Acessibilidade e agilidade para power users.                                                |
| 6  | Empty States (Estados Vazios)   | Gráficos podem quebrar ou ficar estranhos sem dados.              | Verificar `if df.empty:` antes de renderizar e mostrar `st.info("Sem dados para o período")`. | Interface limpa e informativa mesmo sem dados.                                              |
| 7  | Responsividade Mobile           | Sidebar ocupa muito espaço em telas pequenas.                     | Testar e ajustar layout para colunas colapsarem corretamente em mobile (`st.columns`).           | Melhor experiência em smartphones e tablets.                                               |
| 8  | Filtros Contextuais             | Todos os filtros estão na sidebar global, mesmo os específicos.  | Mover filtros específicos de aba (ex: "Visualização do Mapa") para dentro da própria aba.      | Interface menos poluída e filtros onde são necessários.                                  |
| 9  | Botão de Reset de Filtros      | Não há forma fácil de limpar todos os filtros.                  | Criar botão na sidebar que limpa `st.session_state` dos filtros.                                | Facilidade para reiniciar a análise.                                                       |
| 10 | Documentação Integrada        | O usuário precisa adivinhar regras de negócio.                   | Criar ícones de `?` ou expanders com "Como interpretar esta tela".                              | Auto-serviço de aprendizado do sistema.                                                    |
| 11 | Feedback de Ação              | Botões (ex: "Recarregar") não dão feedback claro de conclusão. | Usar `st.toast("Dados atualizados com sucesso!")` após ações.                                 | Confirmação visual de que a ação funcionou.                                             |
| 12 | Formatação de Números        | Moedas e percentuais podem variar na formatação.                 | Padronizar funções de formatação (R$, %, casas decimais) em `utils.py`.                      | Consistência visual em todos os KPIs.                                                      |
| 13 | Agrupamento de Informações    | Páginas longas exigem muito scroll.                               | Usar `st.expander` para seções secundárias ou tabelas detalhadas.                             | Visão geral limpa com detalhes sob demanda.                                                |
| 14 | Atalhos de Data                 | DatePicker exige muitos cliques.                                   | Adicionar botões rápidos: "Hoje", "Ontem", "Este Mês", "Últimos 30 dias".                      | Seleção de período muito mais rápida.                                                   |
| 15 | Consistência de Linguagem      | Mistura de termos (ex: "Faturamento" vs "Receita").                | Revisar `constants.py` para garantir terminologia única.                                        | Menor carga cognitiva para o usuário.                                                      |
| 16 | Indicadores de Tendência       | Métricas mostram apenas valor atual.                              | Adicionar delta (setinha verde/vermelha) comparando com período anterior.                         | Contexto imediato de melhora ou piora.                                                      |
| 17 | Download de Dados               | Tabelas não possuem exportação clara.                           | Adicionar botão de download CSV/Excel acima de cada dataframe exibido.                            | Facilidade para trabalhar dados fora do sistema.                                            |
| 18 | Personalização de Visão      | Usuário vê todas as colunas sempre.                              | Adicionar `st.multiselect` para escolher colunas visíveis em tabelas grandes.                   | Foco apenas no que importa para o usuário.                                                 |
| 19 | Modo de Leitura                 | Gráficos Plotly podem ter muitos botões de controle.             | Configurar `config={'displayModeBar': False}` ou simplificar toolbar.                            | Visual mais limpo e focado nos dados.                                                       |
| 20 | Onboarding                      | Novos usuários ficam perdidos.                                    | Criar um modal de boas-vindas na primeira visita explicando o sistema.                             | Curva de aprendizado reduzida.                                                              |

## 2. UI (Interface do Usuário)

| #  | Item                            | Estado Atual                                       | Como Melhorar                                                                        | Estado Pós-Implementação                       |
| -- | ------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------- |
| 1  | Paleta de Cores Consistente     | Cores hardcoded em vários arquivos.               | Centralizar paleta em `constants.py` ou tema `config.toml`.                      | Identidade visual sólida e fácil manutenção.  |
| 2  | Estilização de Cards          | Métricas usam estilo padrão do Streamlit.        | Criar CSS customizado para cards com sombra e bordas arredondadas.                   | Visual mais profissional e moderno "App-like".    |
| 3  | Tipografia                      | Fonte padrão do Streamlit (Sans-serif genérica). | Importar fonte corporativa via Google Fonts no CSS.                                  | Alinhamento com a marca da empresa.               |
| 6  | Espaçamento (Whitespace)       | Elementos podem estar muito colados.               | Usar `st.container` com padding ou divisores `st.divider()`.                     | Layout mais respirável e fácil de escanear.     |
| 7  | Hierarquia Visual               | Títulos e subtítulos com pesos parecidos.        | Definir tamanhos claros para H1, H2, H3 e labels de métricas.                       | Leitura guiada pela importância da informação. |
| 8  | Tabelas Estilizadas             | Dataframes padrão do Pandas.                      | Usar `st.dataframe` com `column_config` para barras de progresso e formatação. | Tabelas ricas e interativas visualmente.          |
| 9  | Gráficos Gauge                 | Gráficos de velocímetro ocupam muito espaço.    | Ajustar margens e tamanho no Plotly layout.                                          | Melhor aproveitamento do espaço na tela.         |
| 10 | Botões Primários/Secundários | Botões têm a mesma cor.                          | Usar `type="primary"` para ações principais e `secondary` para outras.         | Call-to-action claro para o usuário.             |
| 11 | Tema Escuro/Claro               | Depende da configuração do sistema do usuário.  | Forçar um tema ou criar toggle de tema personalizado.                               | Controle total sobre a apresentação visual.     |
| 12 | Animações Sutis               | Transições de abas são bruscas.                 | (Limitado no Streamlit) Usar CSS para fade-in em elementos carregados.               | Sensação de fluidez na interface.               |
| 13 | Rodapé Personalizado           | Rodapé padrão "Made with Streamlit".             | Ocultar padrão e criar rodapé com copyright e versão do sistema.                  | Aparência de software proprietário.             |
| 14 | Alinhamento de Gráficos        | Gráficos podem desencontrar em colunas.           | Forçar altura fixa nos gráficos Plotly (`height=400`).                           | Grid perfeito e alinhado.                         |
| 15 | Inputs Estilizados              | Caixas de seleção padrão.                       | Personalizar bordas e cores de foco via CSS injection.                               | Inputs integrados ao design system.               |
| 16 | Imagens de Placeholder          | Falta de imagens em perfis vazios.                 | Usar avatares gerados (ex: iniciais) para parceiros sem foto.                        | Interface mais humana e acabada.                  |
| 17 | Mapas Temáticos                | Mapas usam tiles padrão do OSM.                   | Usar tiles do CartoDB Positron ou Dark Matter.                                       | Mapas mais limpos que destacam os dados.          |
| 18 | Alertas Visuais                 | Sucesso/Erro usam caixas padrão.                  | Estilizar `st.success/warning` para combinar com a paleta.                         | Feedback visual integrado ao tema.                |
| 19 | Scrollbar Personalizada         | Barra de rolagem padrão do navegador.             | Estilizar scrollbar (fina, cores do tema) via CSS `::-webkit-scrollbar`.           | Detalhe de acabamento refinado.                   |

## 3. Performance

| #  | Item                       | Estado Atual                                     | Como Melhorar                                                                                                     | Estado Pós-Implementação                                |
| -- | -------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 1  | Cache de Dados             | `load_sheet` cacheado, mas processamento não. | Cachear resultado de `get_dados` após processamento pesado.                                                    | Carregamento instantâneo após primeira carga.            |
| 2  | Formato de Dados           | Leitura direta de Google Sheets (lento).         | Implementar job noturno que salva em Parquet/CSV e app lê do arquivo.                                            | Redução drástica no tempo de I/O (de segundos para ms). |
| 3  | Geocodificação Síncrona | `time.sleep(1.1)` trava a execução.          | Mover geocodificação para script separado/background ou usar API paga/batch.                                    | Interface não trava aguardando coordenadas.               |
| 4  | Otimização Pandas        | Uso de loops ou apply em dataframes.             | Vetorizar todas as operações (usar funções nativas do numpy/pandas).                                          | Processamento de dados muito mais rápido.                 |
| 5  | Lazy Loading de Abas       | Todas as abas podem estar processando dados.     | Carregar dados pesados apenas dentro do `if` da aba ativa (se possível na arquitetura).                        | Inicialização do app mais rápida.                       |
| 6  | Redução de GeoJSON       | Arquivos de fronteiras IBGE pesados.             | Simplificar polígonos (TopplogyPreserveSimplification) antes de salvar.                                          | Renderização do mapa muito mais leve.                    |
| 7  | Cache de Consultas API     | Consultas repetidas a APIs externas.             | Aumentar TTL do cache para dados que mudam pouco (ex: CNAE, IBGE).                                                | Menos chamadas de rede e maior resiliência.               |
| 8  | Profiling                  | Sem métricas de performance.                    | Adicionar decorador de timing nas funções principais e logar tempo.                                             | Identificação precisa de gargalos.                       |
| 9  | Tipagem de Dados Pandas    | Strings usam muita memória.                     | Converter colunas categóricas para `category` dtype e inteiros menores (`int32`).                            | Redução de uso de RAM pelo servidor.                     |
| 10 | Limpeza de Cache           | Cache pode crescer indefinidamente.              | Configurar `max_entries` no `st.cache_data`.                                                                  | Prevenção de estouro de memória no servidor.            |
| 11 | Renderização de Mapa     | Plotar milhares de pontos trava o navegador.     | Usar `ClusterMarker` no Folium ou mudar para PyDeck (GPU accelerated).                                          | Mapas fluidos mesmo com 10k+ pontos.                       |
| 12 | Compressão de Assets      | Imagens/logos carregados full-size.              | Otimizar/comprimir imagens na pasta `assets` ou `static`.                                                     | Menor transferência de dados.                             |
| 13 | Imports Otimizados         | Imports pesados no topo do arquivo.              | Importar bibliotecas pesadas apenas dentro das funções que as usam.                                             | Startup time do script reduzido.                           |
| 14 | Query em Planilha          | Baixa planilha inteira para filtrar depois.      | Se usar API de banco, filtrar no SQL (`WHERE`). Se Sheets, usar `gspread` com range específico se possível. | Menor tráfego de dados.                                   |
| 15 | Gerenciamento de Conexão  | Conexões abertas e fechadas repetidamente.      | Usar `st.connection` para gerenciar pool de conexões (se migrar para DB).                                      | Reuso eficiente de conexões.                              |
| 16 | Paralelismo                | Tarefas independentes sequenciais.               | Usar `concurrent.futures` para chamadas de API independentes (com cuidado no Streamlit).                        | Tempo total reduzido para tarefas I/O bound.               |
| 17 | Pré-cálculo de Métricas | Métricas calculadas em tempo de execução.     | Pré-calcular KPIs diários e salvar em tabela agregada.                                                          | Dashboard exibe números instantaneamente.                 |
| 18 | Debounce em Inputs         | Filtros de texto disparam reload a cada letra.   | Usar `st.form` ou componentes com debounce.                                                                     | Menos reprocessamentos desnecessários.                    |
| 19 | Upgrade Bibliotecas        | Versões antigas do Pandas/Streamlit.            | Atualizar para Pandas 2.0 (PyArrow backend) e Streamlit recente.                                                  | Ganhos de performance gratuitos do motor.                  |
| 20 | Monitoramento de Memória  | Sem visibilidade de uso de RAM.                  | Adicionar script simples para logar uso de memória do processo.                                                  | Detecção proativa de vazamentos de memória.             |

## 4. Segurança

| #  | Item                          | Estado Atual                                           | Como Melhorar                                                                                   | Estado Pós-Implementação                                              |
| -- | ----------------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 1  | Gerenciamento de Segredos     | Senhas podem estar no código ou `.env` exposto.     | Usar `st.secrets` (TOML) exclusivamente e garantir `.gitignore`.                            | Credenciais seguras e fora do controle de versão.                       |
| 2  | Autenticação Robusta        | Validação simples de string `API_KEY`.             | Implementar `streamlit-authenticator` com hash de senhas.                                     | Login seguro, criptografado e multi-usuário.                            |
| 3  | Controle de Acesso (RBAC)     | Todos veem tudo (ou bloqueio simples).                 | Criar níveis de permissão (Admin, Gestor, Parceiro) e renderizar abas condicionalmente.       | Usuários acessam apenas o que devem.                                    |
| 4  | Sanitização de Inputs       | Entradas de texto confiadas cegamente.                 | Validar e sanitizar inputs antes de processar ou usar em queries.                               | Proteção contra injeção (se houver SQL) e XSS.                       |
| 5  | Logs de Auditoria             | Ninguém sabe quem acessou o quê.                     | Logar acessos e ações críticas (quem filtrou o que, quem baixou dados).                      | Rastreabilidade de uso do sistema.                                       |
| 6  | Timeout de Sessão            | Sessão fica aberta indefinidamente.                   | Implementar verificação de inatividade e logout automático.                                  | Proteção contra acesso não autorizado em computadores compartilhados. |
| 7  | Proteção de Rotas           | Arquivos `.py` podem ser executados individualmente? | Garantir que sub-páginas verifiquem estado de autenticação no topo.                          | Prevenção de bypass de login.                                          |
| 8  | Dependências Vulneráveis    | Bibliotecas podem ter CVEs.                            | Rodar `pip-audit` ou `safety` no CI/CD.                                                     | Código livre de vulnerabilidades conhecidas.                            |
| 9  | Exposição de Erros          | Tracebacks mostram caminhos de arquivo.                | Suprimir tracebacks em produção (`client.showErrorDetails = false` no config).              | Atacantes não veem estrutura interna do servidor.                       |
| 10 | Rate Limiting                 | Sem limite de requisições.                           | Implementar lógica simples para bloquear IPs com excesso de refresh (se exposto publicamente). | Proteção básica contra DoS.                                           |
| 11 | Validação de Dados Externos | Dados do Sheets confiados cegamente.                   | Validar schema estrito (Pandera) ao carregar dados.                                             | Proteção contra dados maliciosos ou corrompidos na fonte.              |
| 12 | HTTPS                         | Depende do deploy.                                     | Forçar HTTPS no nível do servidor/proxy reverso.                                              | Comunicação criptografada.                                             |
| 13 | Backup de Dados               | Depende do Google Sheets.                              | Script de backup automático dos dados para S3/Local diariamente.                               | Recuperação de desastres garantida.                                    |
| 14 | Mascaramento de Dados         | Dados sensíveis (CPFs, nomes) expostos.               | Mascarar dados pessoais na visualização se não for estritamente necessário (LGPD).          | Conformidade com leis de proteção de dados.                            |
| 15 | Headers de Segurança         | Headers HTTP padrão.                                  | Configurar headers (HSTS, X-Frame-Options) se usar container customizado.                       | Proteção contra clickjacking e outros vetores web.                     |
| 16 | Hardcoded Values              | Metas e regras hardcoded.                              | Mover lógica de negócio para config/banco seguro.                                             | Menor risco de manipulação de regras no código.                       |
| 17 | Separação Dev/Prod          | Mesmo ambiente para tudo.                              | Criar ambientes distintos com credenciais distintas.                                            | Testes não afetam dados reais.                                          |
| 18 | Revisão de Código           | Commit direto na main.                                 | Exigir Pull Requests com aprovação para mudanças em arquivos críticos.                      | Controle de qualidade e segurança no código.                           |
| 19 | API Keys de Terceiros         | Chaves de mapas/geocoding expostas no front?           | Garantir que chaves sejam usadas apenas no backend (Python) e não vazem pro JS.                | Proteção de cotas de serviços pagos.                                  |
| 20 | Política de Senhas           | Senha única ou fraca.                                 | Exigir complexidade mínima e rotação de senhas.                                              | Dificultar força bruta.                                                 |

## 5. Novas Páginas Sugeridas

| #  | Item                         | Descrição                                                                      | Valor para o Negócio                                    |
| -- | ---------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------- |
| 1  | Dashboard Executivo (Home)   | Visão "One-pager" com os 5 principais KPIs de todo o negócio.                  | Visão rápida da saúde da empresa sem navegar em abas. |
| 2  | Gestão de Usuários         | CRUD de usuários, redefinição de senha e atribuição de perfis.              | Autonomia para o administrador do sistema.               |
| 3  | Configurações do Sistema   | Interface para editar metas, datas de corte e parâmetros globais.               | Flexibilidade sem precisar editar código.               |
| 4  | Logs e Auditoria             | Visualizador de logs do sistema (quem fez o que e quando).                       | Segurança e monitoramento de uso.                       |
| 5  | Upload de Dados              | Interface para upload de CSV/Excel complementar (ex: metas manuais).             | Independência de fontes de dados automáticas.          |
| 6  | Análise de Concorrência    | Página para registrar e comparar dados de concorrentes por região.             | Inteligência de mercado centralizada.                   |
| 7  | Relatórios Personalizados   | Ferramenta para montar um relatório PDF escolhendo gráficos.                   | Facilidade para criar apresentações de resultados.     |
| 8  | Central de Ajuda             | Tutoriais em vídeo e FAQ sobre o uso do dashboard.                              | Redução de dúvidas e suporte.                         |
| 9  | Status do Sistema            | Página técnica mostrando status das integrações (API Sheets, Geocoding).     | Diagnóstico rápido de problemas.                       |
| 10 | Perfil do Parceiro (Detalhe) | Página "Ficha" dedicada a um único parceiro com histórico completo.           | Visão 360º do relacionamento.                          |
| 11 | Simulador de Comissões      | Calculadora para prever ganhos baseados em cenários de vendas.                  | Engajamento e motivação para parceiros/vendedores.     |
| 12 | Mapa de Calor (Heatmap)      | Página dedicada apenas a visualização de densidade (vendas, leads).           | Identificação visual rápida de zonas quentes.         |
| 13 | Funil de Vendas              | Visualização clássica de funil (Lead -> Contato -> Proposta -> Fechado).      | Identificação de gargalos no processo comercial.       |
| 14 | Análise de Churn            | Página focada em cancelamentos e motivos de saída.                             | Retenção de clientes e receita.                        |
| 15 | Comparativo Regional         | Ferramenta para colocar duas regiões lado a lado e comparar KPIs.               | Benchmarking interno.                                    |
| 16 | Notificações               | Central de alertas (ex: "Meta atingida", "Dados desatualizados").                | Proatividade na gestão.                                 |
| 17 | Análise de Produtos         | Performance detalhada por tipo de curso/produto.                                 | Otimização de portfólio.                              |
| 18 | Gamificação                | Ranking interativo com medalhas e conquistas para parceiros.                     | Estímulo à competição saudável.                     |
| 19 | Exportação de Dados        | Página centralizada para baixar dumps de dados brutos permitidos.               | Facilidade para analistas de dados.                      |
| 20 | Playground de IA             | Interface de chat (LLM) para fazer perguntas aos dados ("Qual melhor região?"). | Insights exploratórios via linguagem natural.           |

## 6. Ferramentas e Infraestrutura

| #  | Item                             | Estado Atual                           | Como Melhorar                                                                | Estado Pós-Implementação                               |
| -- | -------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------- |
| 1  | Linting                          | Código pode ter estilo inconsistente. | Configurar `ruff` ou `flake8`.                                           | Código padronizado e limpo.                              |
| 2  | Formatação                     | Formatação manual.                   | Configurar `black` ou `ruff format` no save.                             | Fim das discussões sobre estilo de código.              |
| 3  | Type Checking                    | Tipagem dinâmica pura.                | Adicionar type hints e rodar `mypy`.                                       | Menos bugs de tipo em tempo de execução.                |
| 4  | Testes Unitários                | Sem testes visíveis.                  | Criar testes com `pytest` para funções de `services/`.                 | Confiança para refatorar sem quebrar lógica.            |
| 5  | CI/CD                            | Deploy manual?                         | Configurar GitHub Actions para lint, test e deploy.                          | Processo de entrega automatizado e seguro.                |
| 6  | Containerização                | `.devcontainer` existe, mas e prod?  | Criar `Dockerfile` otimizado para produção (multi-stage).                | Ambiente idêntico em dev e prod.                         |
| 7  | Gerenciamento de Dependências   | `requirements.txt` simples.          | Migrar para `poetry` ou `uv`.                                            | Resolução de dependências determinística e lockfile.  |
| 8  | Pre-commit Hooks                 | Commits podem quebrar o build.         | Configurar `pre-commit` para rodar linter antes do commit.                 | Repositório sempre saudável.                            |
| 9  | Documentação de Código        | Docstrings variadas.                   | Adicionar docstrings padrão Google/NumPy em todas as funções.             | Código auto-explicativo.                                 |
| 10 | Monitoramento de Erros           | Logs no console.                       | Integrar Sentry.                                                             | Alertas em tempo real sobre erros no front dos usuários. |
| 11 | Analytics de Uso                 | Sem métricas de acesso.               | Integrar Streamlit Analytics ou PostHog.                                     | Entender quais abas são mais usadas.                     |
| 12 | Versionamento Semântico         | Versões ad-hoc.                       | Adotar SemVer e criar tags no Git.                                           | Controle claro de releases.                               |
| 13 | Banco de Dados                   | Planilhas Google (frágil).            | Migrar para PostgreSQL ou SQLite (se local).                                 | Robustez, integridade e performance de dados.             |
| 14 | Editor Config                    | Configuração depende do editor.      | Padronizar `.editorconfig`.                                                | Identação consistente entre editores diferentes.        |
| 15 | Virtual Environment              | Manual.                                | Automatizar criação de venv no Makefile ou Taskfile.                       | Setup de ambiente rápido para novos devs.                |
| 16 | Estrutura de Pastas              | Arquivos na raiz.                      | Mover `app.py` e outros para `src/` e modularizar mais.                  | Organização escalável.                                 |
| 17 | Gestão de Configuração        | Variáveis espalhadas.                 | Usar `pydantic-settings` para validar variáveis de ambiente.              | Erro rápido se configuração estiver faltando.          |
| 18 | Scripts de Manutenção          | Comandos manuais.                      | Criar `Makefile` com comandos `make run`, `make test`, `make clean`. | Padronização de comandos operacionais.                  |
| 19 | Backup de Código                | GitHub.                                | Garantir redundância ou mirror se crítico.                                 | Segurança do ativo intelectual.                          |
| 20 | Análise Estática de Segurança | Nenhuma.                               | Rodar `bandit` no código.                                                 | Detecção automática de falhas de segurança comuns.    |

## 7. Página: Contratos

| #  | Item                          | Estado Atual                              | Como Melhorar                                                     | Estado Pós-Implementação                      |
| -- | ----------------------------- | ----------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------ |
| 1  | Metas Dinâmicas              | Metas (30, 90, 180) hardcoded no código. | Criar inputs na sidebar ou config para ajustar metas.             | Flexibilidade para ajustar objetivos sem deploy. |
| 2  | Gráfico de Evolução        | Visão estática acumulada.               | Adicionar gráfico de linha temporal (assinaturas por dia/mês).  | Visualização da tendência de crescimento.     |
| 3  | Drill-down de Status          | Gráfico de pizza estático.              | Tornar fatias clicáveis para filtrar a tabela abaixo.            | Interatividade para investigar gargalos.         |
| 4  | Tabela Detalhada              | Pode não existir ou ser simples.         | Adicionar `st.dataframe` com busca e ordenação dos contratos. | Acesso rápido aos detalhes de cada contrato.    |
| 5  | KPIs de Conversão            | Apenas contagem absoluta.                 | Calcular taxa de conversão (Assinados / Total).                  | Medição de eficiência comercial.              |
| 6  | Tempo Médio de Ciclo         | Não existe.                              | Calcular tempo entre "Enviado" e "Assinado".                      | Identificação de lentidão no processo.        |
| 7  | Análise por Captador         | Gráfico de barras simples.               | Adicionar ranking com foto e % de atingimento da meta individual. | Gamificação e reconhecimento.                  |
| 8  | Filtro de Valor               | Sem filtro por valor de contrato.         | Adicionar slider de range de valor (se houver dado financeiro).   | Foco em contratos de alto valor (High Ticket).   |
| 9  | Comparativo Período Anterior | Sem comparação.                         | Adicionar indicador "vs Mês Passado" nos Big Numbers.            | Contexto de performance imediato.                |
| 10 | Previsão de Fechamento       | Baseado apenas no passado.                | Estimar contratos a fechar com base no funil atual.               | Previsibilidade de curto prazo.                  |
| 11 | Exportação Filtrada         | Download genérico.                       | Botão "Baixar Lista Filtrada" da tabela de contratos.            | Dados prontos para trabalho operacional.         |
| 12 | Alerta de Estagnação        | Contratos parados não destacados.        | Destacar em vermelho contratos parados há > X dias.              | Ação proativa para destravar vendas.           |
| 13 | Distribuição Geográfica    | Sem mapa nesta aba.                       | Pequeno mapa de bolhas mostrando origem dos contratos.            | Correlação visual geografia x vendas.          |
| 14 | Ticket Médio                 | Não visível.                            | Card com valor médio dos contratos assinados.                    | Monitoramento de qualidade da venda.             |
| 15 | Sazonalidade                  | Análise mensal simples.                  | Heatmap de dias da semana/horários de assinatura.                | Entender melhor momento de fechamento.           |
| 16 | Motivos de Perda              | Se houver dados de recusa.                | Gráfico de Pareto de motivos de não-fechamento.                 | Plano de ação para objeções.                 |
| 17 | Filtro por Produto            | Mistura todos os contratos.               | Filtro para ver desempenho por tipo de curso.                     | Análise específica de portfólio.              |
| 18 | Assinaturas Digitais          | Apenas status.                            | Se possível, link direto para o documento (DocuSign/etc).        | Agilidade na conferência.                       |
| 19 | Responsividade de Gráficos   | Gráficos podem ficar espremidos.         | Usar `use_container_width=True` em todos os charts Plotly.      | Layout adaptável a qualquer tela.               |
| 20 | Anotações                   | Gráficos sem contexto de eventos.        | Permitir adicionar marcos (ex: "Início Campanha Black Friday").  | Correlação causa-efeito visual.                |

## 8. Página: Mapa

| #  | Item                          | Estado Atual                       | Como Melhorar                                                         | Estado Pós-Implementação                           |
| -- | ----------------------------- | ---------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------- |
| 1  | Performance de Renderização | Lento com muitos pontos.           | Implementar clusterização de marcadores (MarkerCluster).            | Mapa carrega rápido e agrupa pontos automaticamente. |
| 2  | Filtro de Raio                | Não existe.                       | Ferramenta para desenhar círculo e filtrar parceiros dentro de X km. | Análise de cobertura local precisa.                  |
| 3  | Camadas de Dados              | Apenas parceiros.                  | Adicionar camadas toggleáveis (Escolas, Concorrentes, População).  | Cruzamento visual de dados ricos.                     |
| 4  | Heatmap                       | Apenas pinos.                      | Adicionar camada de mapa de calor baseada em densidade de vendas.     | Visualização imediata de zonas quentes.             |
| 5  | Popup Rico                    | Informações básicas no clique.  | Popup HTML formatado com mini-gráficos e links.                      | Decisão rápida sem sair do mapa.                    |
| 6  | Busca de Endereço            | Geocoding lento/básico.           | Autocomplete de endereço na busca (via API).                         | UX fluida para encontrar locais.                      |
| 7  | Legenda Clara                 | Pinos podem confundir.             | Legenda flutuante explicativa (cores/ícones).                        | Entendimento imediato do que é o quê.               |
| 8  | Tela Cheia                    | Mapa confinado no layout.          | Botão para expandir mapa para tela cheia.                            | Imersão total na análise geográfica.               |
| 9  | Filtro Cruzado                | Mapa não filtra outros gráficos. | Seleção no mapa (Lasso select) filtra tabelas abaixo.               | Integração total entre mapa e dados.                |
| 10 | Rotas (Futuro)                | Sem roteirização.                | Ferramenta simples de "Traçar Rota" entre parceiros selecionados.    | Planejamento de visitas.                              |
| 11 | Mapa de Coroplético          | Fronteiras simples.                | Pintar municípios baseado em vendas/população (Choropleth).        | Análise macro-regional visual.                       |
| 12 | Ícones Personalizados        | Pinos padrão.                     | Ícones distintos para tipos de parceiro (Ouro, Prata, Bronze).       | Diferenciação visual de valor.                      |
| 13 | Controle de Zoom              | Zoom manual.                       | "Auto-fit" bounds para mostrar todos os pontos filtrados.             | Mapa sempre centralizado nos dados relevantes.        |
| 14 | Exportação de Imagem        | Print screen manual.               | Botão "Salvar Mapa como PNG".                                        | Facilidade para relatórios.                          |
| 15 | Modo Satélite                | Apenas mapa de rua.                | Toggle para visão de satélite.                                      | Contexto físico/geográfico (zona rural vs urbana).  |
| 16 | Dados Demográficos           | Sem contexto populacional.         | Tooltip no município mostrando população/PIB (dados IBGE).         | Contexto de mercado potencial.                        |
| 17 | Análise de Proximidade       | Visual.                            | Calcular e mostrar "Parceiro mais próximo" de um ponto.              | Suporte logístico.                                   |
| 18 | Histórico no Mapa            | Estático atual.                   | Slider temporal para ver evolução da expansão no mapa.             | Animação do crescimento da rede.                    |
| 19 | Geocoding Reverso             | Coordenadas manuais.               | Ao clicar no mapa, preencher endereço no form de novo parceiro.      | Facilidade de cadastro.                               |
| 20 | Cache de Tiles                | Recarregamento constante.          | Configurar cache local de tiles do mapa.                              | Navegação no mapa mais suave.                       |

## 9. Página: Faturamento

| #  | Item                         | Estado Atual                      | Como Melhorar                                                             | Estado Pós-Implementação                      |
| -- | ---------------------------- | --------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------ |
| 1  | Visão Anual vs Mensal       | Gráficos podem misturar visões. | Toggle claro "Ano/Mês" que adapta todos os gráficos.                    | Análise na granularidade correta.               |
| 2  | Comparativo YoY              | Linha única.                     | Adicionar linha do ano anterior (sombra ou tracejada) no gráfico mensal. | Comparação direta de crescimento sazonal.      |
| 3  | Margem de Lucro              | Apenas receita bruta.             | Se houver dados de custo, adicionar linha de margem/lucro.                | Visão de saúde financeira real.                |
| 4  | Top Clientes                 | Tabela simples.                   | Gráfico de barras horizontais dos Top 10 pagadores.                      | Foco nos clientes chave (Pareto).                |
| 5  | Inadimplência               | Não visível.                    | KPI e gráfico de valores vencidos vs pagos.                              | Controle de saúde do caixa.                     |
| 6  | Ticket Médio Histórico     | Valor estático.                  | Gráfico de linha da evolução do ticket médio.                         | Identificação de tendências de valorização. |
| 7  | Projeção de Fim de Mês    | Valor atual.                      | Tracejado projetando o fechamento do mês baseado na média diária.      | Antecipação de resultados.                     |
| 8  | Breakdown por Fonte          | Receita total.                    | Donut chart: Cartão vs Boleto vs Pix (se disponível).                   | Inteligência de meios de pagamento.             |
| 9  | Receita Recorrente           | Misturada.                        | Separar MRR (Recorrente) de One-off (Pontual).                            | Avaliação da estabilidade da receita.          |
| 10 | Tabela Dinâmica (Pivot)     | Tabela fixa.                      | Usar `pivot_table` interativa (linhas/colunas configuráveis).          | Análise ad-hoc poderosa.                        |
| 11 | Exportação Financeira      | CSV simples.                      | Exportar em formato pronto para contabilidade (Excel formatado).          | Ganho de tempo no backoffice.                    |
| 12 | Análise de Coorte           | Não existe.                      | Gráfico de retenção de receita por safra (cohort).                     | Entendimento da qualidade das safras de vendas.  |
| 13 | Alertas de Desvio            | Visual.                           | Destacar meses com desvio > 20% da média.                                | Atenção imediata a anomalias.                  |
| 14 | Custo de Aquisição (CAC)   | Não calculado.                   | Se houver dados de mkt, cruzar para mostrar CAC.                          | Visão de eficiência de investimento.           |
| 15 | LTV (Lifetime Value)         | Não calculado.                   | Estimar LTV baseada na média histórica.                                 | Visão de valor de longo prazo.                  |
| 16 | Gráfico Cascata (Waterfall) | Não existe.                      | Mostrar composição do resultado (Vendas Novas + Renovação - Churn).   | Entendimento claro da movimentação financeira. |
| 17 | Sazonalidade Financeira      | Análise visual.                  | Boxplot dos meses para mostrar variância histórica.                     | Previsibilidade estatística.                    |
| 18 | Conversão de Moeda          | Apenas BRL.                       | Se houver internacional, toggle BRL/USD.                                  | Preparo para expansão.                          |
| 19 | Metas Financeiras            | Linha fixa.                       | Barra de progresso " % da Meta de Faturamento".                           | Foco no objetivo financeiro.                     |
| 20 | Detalhamento de Impostos     | Bruto = Líquido?                 | Simular descontos de impostos para visão líquida estimada.              | Realismo financeiro.                             |

## 10. Página: Previsões

| #  | Item                       | Estado Atual                   | Como Melhorar                                                                  | Estado Pós-Implementação                         |
| -- | -------------------------- | ------------------------------ | ------------------------------------------------------------------------------ | --------------------------------------------------- |
| 1  | Seleção de Modelo        | Prophet padrão.               | Permitir escolher entre Prophet, ARIMA, Holt-Winters via UI.                   | Flexibilidade para encontrar o melhor ajuste.       |
| 2  | Ajuste de Hiperparâmetros | Automático/Hardcoded.         | Sliders para ajustar sazonalidade, changepoints, alpha/beta/gamma.             | Tuning fino por cientistas de dados/analistas.      |
| 3  | Intervalos de Confiança   | Fixo ou oculto.                | Permitir ajustar intervalo (80%, 90%, 95%) e visualizar a faixa.               | Gestão de risco baseada na incerteza.              |
| 4  | Backtesting Visual         | Gráfico estático.            | Mostrar corte de treino/teste e erro no período de teste visualmente.         | Validação visual da confiança do modelo.         |
| 5  | Métricas de Erro          | Texto simples.                 | Exibir tabela comparativa de MAPE, RMSE, MAE para cada modelo.                 | Decisão técnica baseada em números.              |
| 6  | Regressores Externos       | Apenas série temporal.        | Permitir upload/input de variáveis externas (ex: investimento mkt).           | Modelos causais mais robustos.                      |
| 7  | Cenários (What-If)        | Linha única.                  | Criar cenários Otimista, Realista e Pessimista.                               | Planejamento estratégico completo.                 |
| 8  | Explicação do Modelo     | Caixa preta.                   | Plotar componentes da decomposição (Tendência, Sazonalidade Anual/Semanal). | Entendimento do "porquê" da previsão.             |
| 9  | Exportação de Forecast   | Visual.                        | Botão para baixar CSV com as datas futuras e valores previstos.               | Uso dos dados em orçamentos externos.              |
| 10 | Ajuste Manual              | Modelo matemático puro.       | Permitir "override" manual de pontos futuros (ex: saber que haverá feriado).  | Inteligência humana + IA.                          |
| 11 | Detecção de Outliers     | Dados sujos entram no modelo.  | Opção para remover/suavizar outliers antes de treinar.                       | Previsões não contaminadas por eventos atípicos. |
| 12 | Comparação Multi-modelo  | Um por vez.                    | Plotar linhas de 3 modelos diferentes no mesmo gráfico.                       | Competição de modelos visual.                     |
| 13 | Histórico de Previsões   | Previsão atual.               | Guardar previsões passadas e comparar com o realizado ("Forecast Accuracy").  | Aprendizado sobre a qualidade das previsões.       |
| 14 | Feriados                   | Padrão do Prophet (se ativo). | Interface para adicionar/remover feriados customizados que afetam o negócio.  | Ajuste fino de calendário.                         |
| 15 | Simulação de Metas       | Previsão passiva.             | Input "Meta Desejada" e cálculo reverso do crescimento necessário.           | Ferramenta de planejamento de metas.                |
| 16 | Performance de Treino      | Sem feedback.                  | Mostrar tempo de treinamento e avisos de convergência.                        | Transparência computacional.                       |
| 17 | Validação Cruzada        | Split simples.                 | Implementar Time Series Cross-Validation (janelas deslizantes).                | Robustez estatística da validação.               |
| 18 | Dicas de Interpretação   | Gráficos complexos.           | Texto dinâmico explicando "A tendência é de alta de X%...".                 | Acessibilidade para não-estatísticos.             |
| 19 | Salvar Modelo              | Treina toda vez.               | Botão para serializar (pickle) e salvar o modelo treinado.                    | Reuso rápido sem retreinar.                        |
| 20 | Alertas de Tendência      | Visual.                        | Aviso automático se a previsão indicar queda brusca.                         | Radar de problemas futuros.                         |

## 11. Página: Análise de Oportunidade

| #  | Item                       | Estado Atual                 | Como Melhorar                                                                       | Estado Pós-Implementação               |
| -- | -------------------------- | ---------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------- |
| 1  | Clusterização Interativa | Parâmetros fixos.           | Sliders para `eps` e `min_samples` do DBSCAN visíveis.                         | Exploração dinâmica de agrupamentos.   |
| 2  | Filtros de Mercado         | Filtros básicos.            | Adicionar filtros por PIB per capita, IDH, População (dados IBGE).                | Segmentação de mercado qualificada.     |
| 3  | Score de Oportunidade      | Sem ranking.                 | Criar algoritmo de scoring (População * Renda / Concorrência) e rankear cidades. | Lista priorizada de onde atacar.          |
| 4  | Mapa de Brancos            | Visual.                      | Destacar claramente municípios sem parceiros mas com alto potencial.               | Identificação imediata de Blue Oceans.  |
| 5  | Análise de Saturação    | Sem indicador.               | Calcular penetração (Vendas / População) e alertar saturação.                 | Evitar canibalização.                   |
| 6  | Dados de CNAE              | Integração quebrada/lenta. | Corrigir integração ou usar dados estáticos cacheados de empresas por setor.     | Visão B2B real.                          |
| 7  | Comparação de Clusters   | Visual.                      | Tabela comparando média de métricas entre os clusters encontrados.                | Perfilamento dos grupos de oportunidade.  |
| 8  | Exportação de Leads      | Visualização.              | Botão "Gerar Lista de Prospecção" das cidades selecionadas.                      | Ação comercial direta.                  |
| 9  | Integração CRM           | Dados isolados.              | (Futuro) Botão para enviar cidades/regiões para pipeline do CRM.                  | Conexão Marketing -> Vendas.             |
| 10 | Análise SWOT Automática  | Não existe.                 | Gerar quadrantes Forças/Fraquezas baseados em dados da região.                    | Insight estratégico automatizado.        |
| 11 | Ficha do Município        | Dados dispersos.             | Ao clicar na cidade, abrir ficha completa (População, Escolas, Empresas, PIB).    | Dossiê completo do alvo.                 |
| 12 | Raio de Influência        | Ponto único.                | Desenhar raio de influência estimado de uma nova unidade.                          | Planejamento de cobertura territorial.    |
| 13 | Custo de Entrada           | Não estimado.               | Se houver dados, estimar custo de setup em nova região.                            | Análise de viabilidade econômica.       |
| 14 | Tendência Demográfica    | Estático.                   | Mostrar se a cidade está crescendo ou encolhendo (Censo).                          | Aposta em mercados em expansão.          |
| 15 | Concorrência Visual       | Não mapeada.                | Se houver dados, plotar concorrentes no mapa de oportunidades.                      | Inteligência competitiva.                |
| 16 | Relatório PDF             | Tela.                        | Gerar "Estudo de Viabilidade" em PDF para a região selecionada.                    | Material para reuniões de expansão.     |
| 17 | Filtro de Distância       | Qualquer lugar.              | Filtrar oportunidades a X km de um centro de distribuição/escritório.            | Otimização logística.                  |
| 18 | Feedback do Usuário       | Apenas dados.                | Permitir usuário marcar cidade como "Descartada" ou "Em Negociação".             | Gestão simples de pipeline de expansão. |
| 19 | Camada de Educação       | Dados gerais.                | Focar em dados de escolas/alunos (Censo Escolar) se o nicho for educação.         | Dados super-relevantes para o setor.      |
| 20 | Importação de Dados      | Apenas sistema.              | Permitir upload de lista de cidades alvo para análise em lote.                     | Análise de listas externas.              |

## 12. Página: Parceiros

| #  | Item                         | Estado Atual      | Como Melhorar                                                                   | Estado Pós-Implementação                |
| -- | ---------------------------- | ----------------- | ------------------------------------------------------------------------------- | ------------------------------------------ |
| 1  | Ranking Gamificado           | Tabela simples.   | Criar pódio visual (1º, 2º, 3º) com fotos/logos.                            | Estímulo visual à competição.          |
| 2  | Scorecard do Parceiro        | Dados dispersos.  | Criar cartão resumo com nota geral (0-100) baseada em múltiplos KPIs.         | Avaliação holística rápida.            |
| 3  | Histórico de Performance    | Snapshot atual.   | Sparklines (mini gráficos) na tabela mostrando tendência últimos 6 meses.    | Visão de momento (subindo/caindo).        |
| 4  | Comparativo (Benchmarking)   | Isolado.          | Permitir selecionar 2 parceiros e comparar lado a lado.                         | Análise de gaps de performance.           |
| 5  | Classificação ABC          | Não existe.      | Classificar automaticamente em Curva ABC (Pareto) e adicionar tag visual.       | Foco na gestão dos parceiros 'A'.         |
| 6  | Mapa da Rede                 | Geral.            | Mapa específico desta aba mostrando apenas a rede de parceiros com status.     | Visão geográfica da força de vendas.    |
| 7  | Análise de Churn            | Não visível.    | Lista de parceiros inativos há X meses (Risco de Churn).                       | Ação de retenção proativa.             |
| 8  | Funil do Parceiro            | Geral.            | Mostrar funil de vendas individual agregado.                                    | Diagnóstico de onde o parceiro trava.     |
| 9  | Documentação               | Não existe.      | Indicador de status de documentação (Pendente/Ok).                            | Compliance em dia.                         |
| 10 | Treinamentos                 | Não rastreado.   | Se houver dados, mostrar % de certificação/treinamento da equipe do parceiro. | Correlação Capacitação x Vendas.       |
| 11 | Metas Individuais            | Geral.            | Visualizar meta vs realizado de cada parceiro.                                  | Cobrança assertiva.                       |
| 12 | Notas de Reunião            | Não existe.      | Pequeno campo de texto ou log para anotar último contato.                      | CRM leve integrado.                        |
| 13 | Data de Aniversário         | Não existe.      | Mostrar "Tempo de Casa" e alertar aniversários de parceria.                    | Relacionamento e fidelização.            |
| 14 | Contatos Chave               | Não visível.    | Mostrar nome/email/telefone do responsável principal no card.                  | Ação rápida de contato.                 |
| 15 | Potencial de Mercado         | Igual para todos. | Cruzar vendas do parceiro com potencial da região dele (Market Share local).   | Avaliação justa de desempenho.           |
| 16 | Badge de Destaque            | Nenhum.           | Ícones automáticos: "Maior Crescimento", "Novo Entrante", "Consistente".      | Reconhecimento automático.                |
| 17 | Exportação de Contatos     | Não existe.      | Baixar VCard ou CSV para mailing.                                               | Integração com ferramentas de email mkt. |
| 18 | Status Financeiro            | Não visível.    | Indicador de inadimplência do próprio parceiro (se aplicável).               | Risco financeiro.                          |
| 19 | Feedback do Parceiro         | Unilateral.       | (Futuro) Espaço para registrar NPS do parceiro com a empresa.                  | Ouvir a ponta.                             |
| 20 | Clusterização de Parceiros | Lista plana.      | Agrupar por perfil (ex: "Hunters", "Farmers", "Novatos").                       | Estratégias de gestão diferenciadas.     |

## 13. Página: Análise Unitária

| #  | Item                        | Estado Atual        | Como Melhorar                                                                         | Estado Pós-Implementação                      |
| -- | --------------------------- | ------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------ |
| 1  | Seletor de Unidade          | Selectbox simples.  | Transformar em um "Search" robusto com autocomplete por nome/cidade/código.          | Encontrar unidade rapidamente.                   |
| 2  | Dashboard Resumo            | Métricas soltas.   | Layout "Cockpit": Uma tela com tudo que importa sobre a unidade.                      | Visão 360º instantânea.                       |
| 3  | DRE da Unidade              | Financeiro geral.   | Demonstrativo de Resultado simplificado da unidade (Receita - Impostos - Comissões). | Visão de rentabilidade real.                    |
| 4  | Comparativo com Média      | Números absolutos. | Adicionar linha de referência "Média da Rede" em todos os gráficos.                | Saber se a unidade está acima/abaixo da média. |
| 5  | Análise de Produtos        | Geral.              | Mix de produtos vendidos por essa unidade (Pizza chart).                              | Entender vocação da unidade.                   |
| 6  | Histórico Completo         | Limitado.           | Gráfico de linha desde o início da operação (Lifetime).                           | Análise de ciclo de vida.                       |
| 7  | Mapa Local                  | Não existe.        | Mini-mapa mostrando a unidade e seus clientes ao redor.                               | Contexto geográfico micro.                      |
| 8  | Metas Específicas          | Genéricas.         | Mostrar metas customizadas dessa unidade.                                             | Acompanhamento personalizado.                    |
| 9  | Equipe                      | Não visível.      | Listar vendedores/atendentes vinculados à unidade.                                   | Gestão de pessoas na ponta.                     |
| 10 | Tickets de Suporte          | Não integrado.     | (Se houver) Mostrar contagem de chamados abertos pela unidade.                        | Saúde operacional.                              |
| 11 | Log de Alterações         | Não existe.        | Histórico de mudanças de status ou dados cadastrais.                                | Auditoria.                                       |
| 12 | Radar Chart                 | Não existe.        | Gráfico de radar comparando 5 pilares (Vendas, Qualidade, Financeiro, Mkt, Ops).     | Diagnóstico visual de equilíbrio.              |
| 13 | Previsão Local             | Geral.              | Rodar modelo de previsão apenas com dados dessa unidade.                             | Forecast específico e acurado.                  |
| 14 | Plano de Ação             | Não existe.        | Campo para gerente regional escrever "Próximos Passos" para a unidade.               | Gestão orientada a ação.                      |
| 15 | Fotos/Evidências           | Não existe.        | Galeria para fotos da fachada/equipe (se houver link).                                | Auditoria visual de padronização.              |
| 16 | Índice de Satisfação     | Não visível.      | Mostrar NPS dos clientes dessa unidade.                                               | Foco na qualidade do atendimento.                |
| 17 | Campanhas Ativas            | Não visível.      | Listar quais campanhas de mkt estão rodando na região.                              | Alinhamento comercial-marketing.                 |
| 18 | Download Relatório Unidade | Não existe.        | Botão "Gerar PDF da Unidade" para envio ao parceiro.                                 | Feedback estruturado para o parceiro.            |
| 19 | Alerta de Risco             | Visual.             | Badge "Risco de Churn" se métricas caírem muito.                                    | Intervenção rápida.                           |
| 20 | Dados Cadastrais            | Texto simples.      | Layout de cartão de visita com botão "Copiar Dados" e links para WhatsApp/Maps.     | Facilidade operacional.                          |

## 14. Página: Alunos

| #  | Item                     | Estado Atual        | Como Melhorar                                                                           | Estado Pós-Implementação                |
| -- | ------------------------ | ------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------ |
| 1  | Filtros Avançados       | Básico.            | Filtros combinados: Curso + Status + Data Matrícula + Origem.                          | Segmentação precisa de base.             |
| 2  | Jornada do Aluno         | Status atual.       | Visualização de pipeline horizontal (Inscrito -> Matriculado -> Cursando -> Formado). | Entendimento do fluxo do aluno.            |
| 3  | Análise de Evasão      | Não explícita.    | Gráfico focado em Dropouts (quando e por que saem).                                    | Retenção e LTV.                          |
| 4  | Perfil Demográfico      | Tabelas.            | Gráficos de pirâmide etária e distribuição de gênero/região.                     | Conheça seu cliente (KYC).                |
| 5  | Mapa de Calor de Notas   | Se houver notas.    | Heatmap de desempenho acadêmico por curso/turma.                                       | Monitoramento pedagógico.                 |
| 6  | Financeiro do Aluno      | Não visível.      | Indicador de adimplência e valor total pago (LTV individual).                          | Saúde financeira da carteira.             |
| 7  | Engajamento              | Não medido.        | (Se houver LMS) Dados de frequência/acessos à plataforma.                             | Previsão de evasão por falta de uso.     |
| 8  | Origem da Matrícula     | Não visível.      | Gráfico de canais de aquisição (Orgânico, Pago, Indicação).                       | Eficiência de marketing.                  |
| 9  | Satisfação (NPS)       | Não visível.      | Mostrar última nota de NPS dada pelo aluno.                                            | Monitoramento de experiência.             |
| 10 | Histórico de Cursos     | Curso atual.        | Linha do tempo de todos os cursos feitos pelo aluno (Upsell/Cross-sell).                | Visão de fidelidade.                      |
| 11 | Exportação para MKT    | Não existe.        | Botão "Exportar para Email Mkt" (segmento filtrado).                                   | Ação de reengajamento.                   |
| 12 | Certificados             | Status.             | Indicador visual se certificado foi emitido/entregue.                                   | Controle de finalização.                 |
| 13 | Suporte ao Aluno         | Não integrado.     | Listar últimos chamados abertos pelo aluno.                                            | Visão 360 do atendimento.                 |
| 14 | Coorte de Retenção     | Não existe.        | Tabela de retenção por mês de entrada (Cohort Analysis).                             | Métrica chave de SaaS/Assinatura.         |
| 15 | Previsão de Formatura   | Data fixa.          | Alertar alunos próximos da formatura para ação de renovação/pós.                  | Ciclo de vida estendido.                   |
| 16 | Distribuição por Curso | Pizza simples.      | Treemap para visualizar cursos com mais alunos vs receita.                              | Análise de popularidade vs rentabilidade. |
| 17 | Alunos em Risco          | Não identificados. | Algoritmo que marca alunos com faltas/notas baixas/pagamento atrasado.                  | Ação preventiva de retenção.           |
| 18 | Busca Global             | Filtro.             | Barra de busca rápida por Nome/CPF/Email no topo.                                      | Atendimento rápido.                       |
| 19 | Bulk Actions             | Um a um.            | Checkbox na tabela para ações em massa (ex: Enviar Msg).                              | Produtividade operacional.                 |
| 20 | Integração WhatsApp    | Texto.              | Link "Click to Chat" no número do celular do aluno.                                    | Contato imediato.                          |
