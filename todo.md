# Checklist de Melhorias e Implementações - Educa Mais Dashboard

Este documento contém uma lista exaustiva e reescrita de sugestões de melhorias para o sistema, categorizadas por área de atuação. O objetivo é transformar este projeto em um software de nível empresarial.

---

## 1. UX (Experiência do Usuário)

1. Implementar `st.spinner()` granular para cada gráfico que carrega dados pesados.
2. Adicionar "skeletons" (placeholders visuais) enquanto os dados carregam.
3. Criar persistência de filtros na URL (`st.query_params`) para compartilhamento de visões.
4. Adicionar tooltips explicativos (`help=`) em todas as métricas e cabeçalhos.
5. Implementar botão "Voltar ao Topo" em páginas longas.
6. Criar mensagens de erro amigáveis (substituir stack traces por "Dados indisponíveis").
7. Adicionar feedback visual (toasts) após ações como "Recarregar Dados".
8. Melhorar a navegação por teclado (Tab index lógico).
9. Criar um fluxo de "Onboarding" para novos usuários (modal explicativo).
10. Adicionar breadcrumbs para navegação profunda (ex: Oportunidade > Detalhada).
11. Implementar "Empty States" ilustrados quando não houver dados.
12. Permitir colapsar a sidebar em mobile automaticamente.
13. Adicionar botão de "Resetar Filtros" visível e acessível.
14. Criar atalhos de teclado para ações comuns (ex: 'R' para recarregar).
15. Melhorar o texto dos botões para serem orientados a ação (ex: "Gerar Relatório" vs "Ok").
16. Adicionar confirmação antes de ações destrutivas ou pesadas.
17. Permitir que o usuário personalize a ordem dos cards no dashboard (se possível via session state).
18. Adicionar modo de "Foco" que esconde a sidebar e cabeçalhos.
19. Usar linguagem consistente em todo o app (ex: "Receita" vs "Faturamento").
20. Adicionar indicadores de progresso para tarefas longas (ex: Geocodificação).
21. Permitir download de tabelas em múltiplos formatos (CSV, Excel, JSON).
22. Adicionar opção de "Favoritar" filtros ou visões específicas.
23. Melhorar a legibilidade de textos longos com espaçamento adequado.
24. Evitar reloads da página inteira ao alterar filtros secundários (`st.form`).
25. Notificar o usuário quando a sessão expirar.
26. Adicionar links diretos para documentação em pontos de dúvida.

## 2. UI (Interface do Usuário)

1. Centralizar a paleta de cores em `constants.py`.
2. Criar um Design System básico (cores, tipografia, espaçamentos).
3. Estilizar cards de métricas com CSS customizado (bordas arredondadas, sombra).
4. Usar ícones consistentes (Material Icons ou FontAwesome) via CSS/Markdown.
5. Padronizar o tamanho e peso das fontes dos cabeçalhos (H1, H2, H3).
6. Estilizar tabelas (`st.dataframe`) com barras de progresso e heatmaps.
7. Criar rodapé profissional com versão e copyright.
8. Alinhar verticalmente gráficos e métricas em colunas adjacentes.
9. Criar componentes de alerta (`st.info`, `st.warning`) personalizados.
10. Adicionar animações sutis de fade-in ao carregar elementos.
11. Adicionar imagens de fundo sutis ou padrões geométricos em áreas vazias.

## 3. Frontend (Streamlit)

1. Otimizar o uso de `st.columns` para layouts complexos.
2. Substituir `st.radio` por `st.pills` (novo componente) onde apropriado.
3. Usar `st.data_editor` para permitir edições rápidas (se permitido).
4. Implementar callbacks (`on_change`) para inputs para reatividade imediata.
5. Usar `st.container(height=...)` para áreas com scroll interno.
6. Criar componentes customizados (Custom Components) se necessário (ex: Navbar).
7. Gerenciar cache de recursos estáticos (imagens).
8. Implementar lógica de "rerun" controlada para evitar loops.
9. Usar `st.status` para logs de processos longos.
10. Refatorar sidebar para usar `st.sidebar` context managers.
11. Implementar upload de arquivos drag-and-drop robusto.
12. Usar `st.chat_input` se adicionar funcionalidades de IA.
13. Adicionar suporte a temas dinâmicos via `config.toml`.
14. Otimizar a renderização de dataframes grandes (paginação no backend).
15. Usar `st.image` com otimização de largura.
16. Implementar "Tabs" aninhadas com cuidado para não poluir a UI.
17. Usar `st.code` para exibir logs ou JSONs de debug.
18. Capturar exceções de frontend e exibir em container dedicado.
19. Adicionar suporte a query parameters para deeplinking.
20. Usar `st.toast` para notificações não intrusivas.
21. Implementar layout fluido (`layout="wide"`) como padrão configurável.
22. Criar wrappers para widgets comuns para padronizar parâmetros.
23. Evitar uso de `st.write` genérico, preferir componentes específicos.
24. Implementar `st.metric` com deltas automáticos.
25. Usar `st.logo` (novo) para gestão de marca.

## 4. Segurança

1. Mover todas as credenciais para `st.secrets` (TOML).
2. Implementar autenticação robusta (Login/Senha) com hash.
3. Configurar RBAC (Controle de Acesso Baseado em Função).
4. Sanitizar todos os inputs de usuário contra Injection/XSS.
5. Implementar timeout de sessão por inatividade.
6. Proteger rotas/abas baseadas no nível de usuário.
7. Logar tentativas de login falhas.
8. Mascarar dados sensíveis (PII) nas tabelas (ex: CPF parcial).
9. Garantir HTTPS em produção (configuração de infra).
10. Não commitar `.env` ou arquivos de segredos (revisar gitignore).
11. Rodar scanner de vulnerabilidades (`pip-audit`) no CI/CD.
12. Implementar Rate Limiting se exposto publicamente.
13. Validar tipos e formatos de arquivos no upload.
14. Desabilitar stack traces detalhados em produção.
15. Criptografar dados sensíveis em repouso (se salvar localmente).
16. Implementar política de senhas fortes.
17. Adicionar cabeçalhos de segurança HTTP (via proxy reverso).
18. Bloquear acesso de IPs suspeitos (se possível na infra).
19. Realizar auditoria de código focado em segurança periodicamente.
20. Manter dependências (`requirements.txt`) atualizadas.
21. Usar `st.secrets` para chaves de API externas (Google, OpenAI).
22. Implementar logs de auditoria (quem fez o quê e quando).
23. Proteger endpoints de webhook se houver.
24. Validar integridade dos dados vindos do Google Sheets.
25. Evitar `eval()` ou `exec()` no código.
26. Limitar o tamanho de uploads para evitar DoS.
27. Isolar o ambiente de execução (Docker container).
28. Revisar permissões da conta de serviço Google (Least Privilege).
29. Implementar 2FA (Autenticação de Dois Fatores) se crítico.
30. Criar plano de resposta a incidentes de segurança.

## 5. Infraestrutura

1. Dockerizar a aplicação (`Dockerfile` e `docker-compose`).
2. Configurar ambiente de Staging e Produção.
3. Usar Redis para cache distribuído (substituir cache em memória local).
4. Configurar CI/CD (GitHub Actions) para deploy automático.
5. Implementar monitoramento de uptime (Health Checks).
6. Configurar logs centralizados (ex: CloudWatch, Datadog).
7. Usar servidor WSGI robusto se sair do Streamlit Cloud.
8. Configurar CDN para assets estáticos se necessário.
9. Automatizar backups de dados locais (`geocache.db`).
10. Configurar variáveis de ambiente de forma segura no host.
11. Implementar Autoscaling (se deploy em nuvem elástica).
12. Monitorar uso de CPU/RAM do container.
13. Configurar alertas de downtime via email/Slack.
14. Usar volumes persistentes para dados que não podem ser perdidos.
15. Configurar proxy reverso (Nginx) para SSL e cache.
16. Documentar arquitetura de infraestrutura (diagrama).
17. Implementar rotação de logs para não encher o disco.
18. Testar recuperação de desastres (Restore de backup).
19. Isolar rede do banco de dados (se houver).
20. Usar IaC (Terraform/Ansible) para provisionamento.
21. Configurar limites de recursos no Docker (CPU/Memória).
22. Otimizar tamanho da imagem Docker (Multi-stage build).
23. Configurar linting de Dockerfile.
24. Implementar verificação de dependências no pipeline.
25. Configurar DNS e domínios personalizados.
26. Usar gerenciador de versões Python (`pyenv`) no desenvolvimento.
27. Padronizar sistema operacional base (ex: Debian Slim).
28. Configurar Timezone do servidor corretamente.
29. Monitorar custos de infraestrutura.
30. Implementar "Graceful Shutdown" da aplicação.

## 6. Performance

1. Vetorizar operações Pandas (remover `apply` e loops).
2. Converter colunas de string para `category` onde aplicável.
3. Usar `parquet` em vez de CSV para cache local.
4. Implementar carregamento assíncrono para APIs externas.
5. Otimizar queries ao Google Sheets (baixar apenas colunas necessárias).
6. Reduzir tamanho dos GeoJSONs (simplificação de polígonos).
7. Aumentar TTL do cache para dados estáticos (IBGE).
8. Implementar paginação no backend para grandes datasets.
9. Usar `modin` ou `polars` se Pandas for gargalo.
10. Profiling de código (`cProfile`) para identificar gargalos.
11. Otimizar renderização de mapas (Clusterização de marcadores).
12. Evitar recálculo de métricas inalteradas (`st.cache_data`).
13. Minificar CSS e JS injetados.
14. Comprimir imagens antes de exibir.
15. Usar formatos de imagem modernos (WebP).
16. Limitar número de pontos plotados em gráficos de linha.
17. Implementar debounce em filtros de texto.
18. Carregar abas pesadas apenas quando clicadas (Lazy Loading).
19. Otimizar loops de geocodificação (batch processing).
20. Monitorar tempo de resposta das APIs.
21. Reduzir uso de memória global (del variaveis grandes).
22. Usar `st.cache_resource` para conexões e modelos ML.
23. Pré-calcular agregações complexas em job noturno.
24. Otimizar imports (importar dentro da função se raro).
25. Remover bibliotecas não utilizadas do `requirements.txt`.
26. Configurar `max_entries` no cache para evitar OOM.
27. Usar tipos numéricos menores (`int32`, `float32`) se possível.
28. Evitar cópias desnecessárias de DataFrames (`df.copy()`).
29. Otimizar regex em filtros.
30. Testar performance com carga de múltiplos usuários.

## 7. Testes e QA

1. Criar suite de testes unitários (`pytest`) para funções de serviço.
2. Implementar testes de integração para APIs (IBGE, Sheets).
3. Criar testes de interface (E2E) com Playwright ou Selenium.
4. Implementar testes de regressão visual (snapshots).
5. Configurar pre-commit hooks para linting e testes rápidos.
6. Testar validação de dados de entrada (Schema validation).
7. Cobrir casos de borda (datas nulas, arquivos vazios).
8. Implementar testes de carga (Locust) para simular usuários.
9. Testar responsividade em diferentes resoluções.
10. Mockar chamadas de API externas nos testes unitários.
11. Medir cobertura de código (`pytest-cov`) e definir meta (ex: 80%).
12. Testar fluxos de erro (o que acontece se a API cair?).
13. Automatizar testes no GitHub Actions.
14. Testar compatibilidade com diferentes navegadores.
15. Validar consistência dos cálculos financeiros.
16. Testar filtros combinados (Data + Estado + Curso).
17. Verificar acessibilidade automatizada (Pa11y).
18. Testar instalação limpa do projeto (`requirements.txt`).
19. Validar tipos de retorno das funções (Type Checking).
20. Criar dataset de "fixtures" para testes reprodutíveis.
21. Testar geocodificação com endereços inválidos.
22. Verificar comportamento com sessão expirada.
23. Testar upload de arquivos corrompidos.
24. Validar sanitização de inputs (Security testing).
25. Testar performance de renderização de gráficos.
26. Documentar casos de teste manuais.
27. Implementar Smoke Tests para deploy rápido.
28. Testar migração de versões de dependências.
29. Validar internacionalização (formatos de data/número).
30. Criar dashboard de resultados de testes.

## 8. Acessibilidade

1. Adicionar textos alternativos (`alt`) em todas as imagens.
2. Garantir contraste de cores suficiente (Ratio 4.5:1).
3. Permitir navegação completa via teclado.
4. Usar labels descritivos em todos os inputs.
5. Evitar depender apenas de cores para transmitir informação.
6. Usar tags semânticas HTML (via Markdown/Components) onde possível.
7. Testar com leitores de tela (NVDA, VoiceOver).
8. Fornecer descrições textuais para gráficos complexos.
9. Permitir redimensionamento de texto sem quebrar o layout.
10. Evitar animações que causam vertigem ou flash.
11. Implementar foco visível em elementos interativos.
12. Usar linguagem simples e clara.
13. Fornecer legendas ou transcrições para áudio/vídeo (se houver).
14. Organizar conteúdo com hierarquia de cabeçalhos lógica.
15. Evitar timeouts muito curtos sem aviso.
16. Criar atalhos de navegação ("Pular para conteúdo").
17. Usar padrões ARIA onde necessário.
18. Garantir que mensagens de erro sejam lidas pelo screen reader.
19. Permitir pausar atualizações automáticas de conteúdo.
20. Testar em modo de alto contraste.
21. Fornecer instruções claras para interações complexas.
22. Evitar captchas inacessíveis.
23. Garantir acessibilidade em modais e popups.
24. Usar fontes legíveis (tamanho e tipo).
25. Permitir input de voz (futuro).
26. Validar acessibilidade de PDFs gerados.
27. Fornecer suporte a múltiplos idiomas (se aplicável).
28. Treinar equipe em práticas de acessibilidade.
29. Incluir checklist de acessibilidade no Definition of Done.
30. Disponibilizar mapa do site ou índice de navegação.

## 9. Analytics e BI

1. Definir KPIs claros para cada página (já iniciado, expandir).
2. Implementar análise de Cohort para retenção de alunos.
3. Criar visualização de Funil de Vendas (Oportunidade -> Contrato).
4. Calcular LTV (Lifetime Value) dos parceiros.
5. Analisar Churn Rate (taxa de cancelamento) de contratos.
6. Implementar segmentação RFM (Recência, Frequência, Valor).
7. Criar projeções de crescimento (YoY, MoM).
8. Analisar sazonalidade de vendas/matrículas.
9. Identificar produtos/cursos "Estrela" e "Abacaxi".
10. Cruzar dados demográficos (IBGE) com vendas internas.
11. Implementar análise de Pareto (Curva ABC) de parceiros.
12. Calcular Ticket Médio por região/estado.
13. Monitorar taxa de conversão de leads.
14. Analisar penetração de mercado por município.
15. Criar dashboard executivo (Resumo para C-Level).
16. Comparar desempenho real vs metas estabelecidas.
17. Analisar correlação entre descontos e volume de vendas.
18. Monitorar tempo médio de fechamento de contrato.
19. Identificar regiões saturadas vs inexploradas.
20. Analisar performance por canal de aquisição (se houver dados).
21. Calcular ROI de campanhas ou parceiros.
22. Implementar detecção de anomalias em faturamento.
23. Criar relatórios de exceção (o que saiu do padrão).
24. Analisar tendências de longo prazo (Moving Averages).
25. Clusterizar parceiros por comportamento.
26. Simular cenários ("E se aumentarmos o preço em 10%?").
27. Acompanhar evolução do market share.
28. Analisar satisfação do cliente (NPS) se houver dados.
29. Monitorar inadimplência.
30. Integrar dados de concorrentes (se disponíveis).

## 10. Notificações

1. Implementar central de notificações na UI.
2. Criar alertas de "Meta Batida" (toasts/confetti).
3. Notificar sobre dados desatualizados.
4. Alerta de anomalia em faturamento (queda brusca).
5. Notificar erros de integração com APIs.
6. Lembretes de renovação de contratos próximos.
7. Alerta de novos parceiros cadastrados.
8. Notificações por email (integração SMTP/SendGrid).
9. Alertas via Slack/Teams/WhatsApp (Webhooks).
10. Notificar término de processamentos longos.
11. Permitir usuário configurar preferências de notificação.
12. Histórico de notificações lidas/não lidas.
13. Alerta de vencimento de API Keys.
14. Notificar atualizações do sistema (Changelog).
15. Alertas de segurança (login em novo dispositivo).
16. Notificações de tarefas pendentes.
17. Alerta de performance (servidor sobrecarregado).
18. Notificar exportações concluídas.
19. Lembretes de follow-up com parceiros.
20. Alertas de datas comemorativas para campanhas.
21. Notificações push (se evoluir para PWA).
22. Agrupar notificações similares.
23. Ações rápidas na notificação (ex: "Ver Detalhes").
24. Sons de notificação (opcional/configurável).
25. Indicador visual (badge) no ícone de notificações.
26. Notificações de feedback de usuário.
27. Alerta de limite de cota de API atingido.
28. Digest diário/semanal por email.
29. Notificar alterações em contratos importantes.
30. Testar sistema de notificações em staging.

## 11. Qualidade do Código

1. Adicionar Type Hints (mypy) em todo o projeto.
2. Configurar linter rigoroso (Ruff ou Pylint).
3. Formatar código automaticamente (Black ou Ruff format).
4. Remover código morto e imports não usados.
5. Reduzir complexidade ciclomática (refatorar funções grandes).
6. Padronizar nomes de variáveis e funções (snake_case).
7. Documentar todas as funções (Docstrings Google/NumPy style).
8. Usar constantes para "Magic Numbers" e strings repetidas.
9. Modularizar arquivos grandes (`app.py`, `ui/*.py`).
10. Implementar tratamento de exceções específico (evitar `except Exception`).
11. Usar Dataclasses ou Pydantic para modelos de dados.
12. Revisar e melhorar comentários de código.
13. Seguir princípios SOLID.
14. Desacoplar lógica de negócio da interface (UI).
15. Implementar injeção de dependência onde útil.
16. Usar caminhos relativos/absolutos de forma consistente (`pathlib`).
17. Revisar uso de variáveis globais.
18. Padronizar estrutura de diretórios.
19. Eliminar código duplicado (DRY).
20. Usar f-strings consistentemente.
21. Garantir que todo arquivo tenha newline no final.
22. Ordenar imports (isort).
23. Usar Enums para opções fixas (status, tipos).
24. Revisar lógica booleana complexa.
25. Adicionar `__init__.py` onde necessário.
26. Usar context managers (`with`) para recursos.
27. Evitar mutação de argumentos padrão.
28. Revisar nomenclatura de arquivos.
29. Implementar logging estruturado.
30. Realizar Code Reviews periódicos.

## 12. Documentação

1. Criar `README.md` detalhado (instalação, uso, arquitetura).
2. Documentar API interna (se houver endpoints).
3. Criar Wiki ou `docs/` com guias de negócio.
4. Documentar dicionário de dados (o que é cada coluna).
5. Criar guia de contribuição (`CONTRIBUTING.md`).
6. Manter `CHANGELOG.md` atualizado.
7. Documentar variáveis de ambiente necessárias (`.env.example`).
8. Criar diagramas de arquitetura (C4 model ou UML).
9. Documentar fluxo de deploy.
10. Criar FAQ para usuários finais.
11. Documentar decisões de design (ADRs).
12. Criar tutoriais em vídeo ou GIF.
13. Documentar dependências e suas licenças.
14. Comentar trechos de código complexos ("Why", not "What").
15. Criar mapa de navegação do app.
16. Documentar processos manuais (ex: atualização de planilha).
17. Criar glossário de termos do domínio (Educação/Vendas).
18. Documentar configurações do VS Code (`.vscode`).
19. Criar templates de Issue e PR no GitHub.
20. Documentar testes (como rodar, o que cobrem).
21. Manter lista de melhorias (`todo.md`) atualizada e priorizada.
22. Documentar roles e permissões de usuários.
23. Criar manual do usuário em PDF/HTML exportável.
24. Documentar estrutura do banco de dados/planilhas.
25. Criar badges de status no README (Build, Coverage).
26. Documentar atalhos de teclado.
27. Traduzir documentação se houver equipe internacional.
28. Versionar a documentação junto com o código.
29. Usar ferramentas como MkDocs ou Sphinx.
30. Documentar plano de rollback.

## 13. IA (Inteligência Artificial)

1. Implementar previsão de demanda com Prophet/NeuralProphet.
2. Criar chatbot (LLM) para "conversar" com os dados ("Qual faturamento de ontem?").
3. Usar NLP para analisar sentimentos em feedbacks de alunos.
4. Implementar recomendação de cursos para regiões baseada em similaridade.
5. Detecção automática de anomalias (Isolation Forest).
6. Classificação automática de leads (Hot/Cold).
7. Otimização de rotas para visitas a parceiros.
8. Clustering de municípios (K-Means/DBSCAN) para expansão.
9. Gerar insights automáticos ("Você vendeu 20% a mais que a média").
10. Resumir relatórios longos com LLMs.
11. Prever Churn de parceiros.
12. Analisar correlação semântica entre cursos e mercado de trabalho local.
13. Implementar OCR para leitura de contratos digitalizados (se houver).
14. Usar IA para limpeza e normalização de dados (fuzzy matching de nomes).
15. Prever inadimplência.
16. Gerar personas de clientes baseadas em dados.
17. Otimizar mix de produtos por região.
18. Analisar elasticidade de preço.
19. Implementar busca semântica na documentação.
20. Usar Vision AI para analisar fotos de fachada de parceiros.
21. Prever impacto de campanhas de marketing.
22. Gerar textos de marketing personalizados para parceiros.
23. Analisar concorrência via scraping e IA.
24. Implementar assistente virtual de onboarding.
25. Explicar o "porquê" de uma previsão (Explainable AI).
26. Ajustar hiperparâmetros de modelos automaticamente.
27. Monitorar drift de modelos (Data Drift).
28. Usar IA generativa para criar cenários de simulação.
29. Implementar análise de causa raiz de problemas.
30. Validar ética e viés dos modelos utilizados.

## 14. Página de Contratos

1. Visualizar funil de status (Enviado -> Assinado -> Pago).
2. Adicionar filtros avançados (Data, Valor, Responsável).
3. Permitir busca textual por nome do contrato/ID.
4. Exibir KPIs de tempo médio em cada etapa.
5. Criar visualização de calendário de vencimentos.
6. Adicionar botão para visualizar PDF do contrato (se link disponível).
7. Implementar edição de metadados do contrato (se permitido).
8. Visualizar histórico de alterações do contrato.
9. Agrupar contratos por parceiro/cliente.
10. Adicionar tags coloridas para tipos de contrato.
11. Exportar lista filtrada para Excel.
12. Calcular valor total em carteira vs realizado.
13. Gráfico de evolução de assinaturas por dia/mês.
14. Identificar contratos estagnados (sem mudança há X dias).
15. Comparar desempenho entre vendedores/captadores.
16. Adicionar alertas de contratos próximos ao vencimento.
17. Visualizar distribuição geográfica dos contratos.
18. Implementar paginação na tabela de contratos.
19. Adicionar colunas customizáveis na tabela.
20. Linkar contrato à página do parceiro.
21. Gráfico de dispersão (Valor vs Tempo de Fechamento).
22. Analisar motivos de perda/cancelamento.
23. Visualizar ticket médio dos contratos assinados.
24. Adicionar comentários/anotações aos contratos.
25. Integração com assinatura digital (Docusign/ClickSign status).
26. Checklist de documentos pendentes por contrato.
27. Visualizar hierarquia (Contrato Mãe/Filho).
28. Simulador de comissões baseado nos contratos.
29. Indicador de contratos com pendências financeiras.
30. Relatório de renovações automáticas.

## 15. Página de Mapas

1. Implementar clusterização de marcadores (MarkerCluster) para performance.
2. Adicionar camadas (Layers) alternáveis (Satélite, Rua, Dark).
3. Filtrar pontos visíveis por raio ou desenho livre.
4. Colorir marcadores dinamicamente por métrica (Valor, Status).
5. Adicionar popups ricos (HTML/Gráficos) ao clicar no marcador.
6. Implementar mapa de calor (Heatmap) de densidade de vendas.
7. Visualizar fronteiras de estados/municípios (GeoJSON).
8. Adicionar busca de endereço com zoom automático.
9. Permitir exportar área visível como imagem.
10. Calcular rotas ou distâncias entre pontos.
11. Adicionar legenda clara para cores e tamanhos.
12. Filtrar mapa interativamente com outros gráficos.
13. Mostrar localização do usuário (Geolocalização).
14. Visualizar territórios de vendas.
15. Animar evolução temporal no mapa (Time Slider).
16. Adicionar camada de dados demográficos (IBGE) sobreposta.
17. Otimizar carregamento de GeoJSONs pesados.
18. Implementar minimapa de contexto.
19. Permitir seleção de múltiplos pontos para ação em lote.
20. Visualizar concorrentes no mapa.
21. Adicionar ferramenta de medição de área/distância.
22. Suporte a mapas 3D (PyDeck) para visualização de altura (ex: faturamento).
23. Persistir estado do mapa (zoom/centro) ao navegar.
24. Customizar ícones dos marcadores.
25. Adicionar camada de trânsito ou fluxo (se relevante).
26. Visualizar raio de atuação de cada parceiro.
27. Integrar com Street View.
28. Adicionar tooltips ao passar o mouse (hover).
29. Resetar visão para enquadrar todos os pontos.
30. Análise de "espaços em branco" (White space analysis).

## 16. Página de Faturamento

1. Adicionar comparativo Ano contra Ano (YoY).
2. Implementar gráfico de cascata (Waterfall) para explicar resultado líquido.
3. Visualizar composição da receita por categoria (Pie/Treemap).
4. Adicionar linhas de tendência e média móvel.
5. Permitir drill-down (Ano -> Mês -> Dia -> Transação).
6. Calcular e exibir margem de lucro/contribuição.
7. Gráfico de Pareto de produtos/serviços.
8. Simulador de faturamento (como já implementado, mas expandir cenários).
9. Analisar sazonalidade mensal/semanal.
10. Visualizar inadimplência e contas a receber.
11. Exportar relatório financeiro formatado (PDF).
12. Adicionar indicadores de meta (Gauges/Bullets).
13. Comparar faturamento Realizado vs Orçado.
14. Analisar Ticket Médio ao longo do tempo.
15. Visualizar fluxo de caixa (Entradas vs Saídas).
16. Adicionar anotações em picos ou quedas (ex: "Black Friday").
17. Tabela detalhada com Sparklines.
18. Analisar faturamento por forma de pagamento.
19. Calcular CAC (Custo de Aquisição) se houver dados de custo.
20. Visualizar distribuição de faturamento por estado/região.
21. Gráfico de "Corrida de Barras" (Bar Chart Race) temporal.
22. Analisar concentração de receita em clientes (Risco).
23. Ajustar valores pela inflação (IPCA) para comparação real.
24. Previsão de fechamento do mês atual.
25. Destaque para "Melhor dia" e "Pior dia".
26. Análise de coorte de receita (Vintage Analysis).
27. Visualizar descontos concedidos vs Receita Bruta.
28. Integração com API bancária para saldo real (futuro).
29. Alertas de desvios significativos do padrão.
30. Dashboard específico para comissões.
