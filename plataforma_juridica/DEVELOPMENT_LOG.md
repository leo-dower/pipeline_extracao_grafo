# Log de Desenvolvimento do Projeto plataforma_juridica

Este documento registra o histórico de desenvolvimento, as decisões de design, as funcionalidades implementadas e os próximos passos planejados para o projeto `plataforma_juridica`.

## 1. Funcionalidades Implementadas

### 1.1. Módulo de Ingestão Básica (MVP)

*   **Objetivo:** Conectar à API do CNJ DataJud, obter dados, indexá-los no Elasticsearch e implementar a lógica de deduplicação.
*   **Arquivos Chave:**
    *   `cnj_api_client.py`: Cliente Python para a API do CNJ DataJud, responsável por fazer requisições HTTP POST com a chave pública e lidar com a paginação (`search_after`).
    *   `ingest_cnj_data.py`: Script principal de ingestão que utiliza o `cnj_api_client` para buscar dados e o cliente `elasticsearch` para indexá-los. Inclui lógica de deduplicação baseada no `numeroProcesso` e tratamento de erros básicos.
    *   `requirements.txt`: Contém as dependências iniciais (`requests`, `elasticsearch`).
*   **Documentação e Testes:**
    *   `README.md`: Documentação inicial do projeto, setup e uso.
    *   `tests/test_cnj_api_client.py`: Testes unitários para o cliente da API, incluindo sucesso e tratamento de erros de rede/HTTP.
    *   `tests/test_ingest_cnj_data.py`: Testes unitários para o script de ingestão, verificando a criação do índice, ingestão de dados e deduplicação.

### 1.2. Integração com Banco de Dados de Grafo (Neo4j)

*   **Objetivo:** Extrair entidades e relacionamentos dos dados de processos no Elasticsearch e populá-los em um banco de dados de grafo Neo4j.
*   **Arquivos Chave:**
    *   `neo4j_client.py`: Cliente Python para o Neo4j, fornecendo métodos para conexão, execução de queries Cypher, criação/fusão de nós e criação de relacionamentos.
    *   `process_for_graph.py`: Script que lê dados do Elasticsearch, extrai entidades (Processo, Tribunal, Classe Processual, Pessoa Física/Jurídica, Advogado) e relacionamentos (JULGADO_POR, PERTENCE_A_CLASSE, TEM_PARTE, REPRESENTA, ATUA_EM), e os insere no Neo4j.
    *   `requirements.txt`: Adicionada a dependência `neo4j`.
*   **Documentação e Testes:**
    *   `tests/test_neo4j_client.py`: Testes unitários para o cliente Neo4j, verificando a conexão e a execução de queries.
    *   `tests/test_process_for_graph.py`: Testes unitários para o script de processamento de grafo, verificando a extração de entidades e a criação de nós/relacionamentos no Neo4j (com mocks).

### 1.3. Dashboard de Busca Avançada e Análise com IA Externa (Groq API)

*   **Objetivo:** Criar uma interface web para busca avançada nos dados do Elasticsearch e integrar análise de texto via Groq API.
*   **Arquivos Chave:**
    *   `app.py`: Aplicação FastAPI que serve como backend. Inclui endpoints para: `GET /` (root), `POST /search` (busca no Elasticsearch com filtros e paginação), `POST /aggregations` (agregações para filtros), e `POST /ai-analyze` (integração com a Groq API para análise de texto).
    *   `requirements.txt`: Adicionadas as dependências `fastapi`, `uvicorn`, `groq`.
    *   `frontend/`: Diretório contendo a aplicação React (Vite) para o frontend.
        *   `frontend/vite.config.js`: Configuração do Vite com proxy para o backend FastAPI.
        *   `frontend/src/App.jsx`: Componente principal do React com UI para busca, filtros, exibição de resultados e interface para análise de texto com Groq.
        *   `frontend/src/App.css`: Estilos básicos para a interface.

## 2. Próximos Passos e Aprimoramentos Pendentes

### 2.1. Aprimoramento da Ingestão e Enriquecimento de Dados com LLM Local (Ollama no TrueNAS)

*   **Descrição:** Tornar a ingestão de dados mais robusta, abrangente para todos os tribunais e enriquecer os metadados com inteligência artificial local (Ollama).
*   **Tarefas:**
    *   Expandir `ingest_cnj_data.py` para ingestão multi-tribunal com retry e validação de esquema.
    *   Configurar Ollama no TrueNAS e expor um endpoint HTTP.
    *   Integrar o Ollama para sumarização, categorização ou extração de entidades nos dados antes da indexação no Elasticsearch.

### 2.2. Gerenciamento de Usuários e Controle de Acesso

*   **Descrição:** Implementar autenticação e autorização para controlar o acesso aos dados e funcionalidades do sistema.
*   **Tarefas:**
    *   Desenvolver API de autenticação/autorização no backend (e.g., JWT).
    *   Implementar registro, login e gerenciamento de perfis de usuário.
    *   Definir e aplicar papéis de usuário (admin, pesquisador, etc.).
    *   Proteger endpoints da API com base em autenticação e autorização.

### 2.3. Monitoramento em Tempo Real e Sistema de Alertas

*   **Descrição:** Automatizar a ingestão de dados e implementar um sistema robusto de monitoramento e alertas.
*   **Tarefas:**
    *   Configurar agendamento para o script de ingestão (e.g., Celery, APScheduler).
    *   Implementar logging estruturado e coleta de métricas (e.g., Prometheus/Grafana).
    *   Configurar alertas para falhas de ingestão, anomalias de dados ou problemas de performance.

### 2.4. Processamento de Documentos e Análise de Conteúdo com IA

*   **Descrição:** Expandir a capacidade para processar o conteúdo de documentos jurídicos e extrair informações valiosas usando IA.
*   **Tarefas:**
    *   Desenvolver pipeline para ingestão de documentos (se disponíveis via API).
    *   Integrar OCR para documentos não pesquisáveis.
    *   Utilizar LLMs (Ollama ou Groq) para NER, sumarização avançada, classificação e identificação de tópicos em textos de documentos.
    *   Indexar conteúdo e entidades extraídas no Elasticsearch.

### 2.5. Melhorias Gerais e Otimizações

*   **Descrição:** Refinamentos contínuos para performance, segurança e usabilidade.
*   **Tarefas:**
    *   Otimização de queries Elasticsearch e Neo4j.
    *   Melhoria da validação de dados e tratamento de edge cases.
    *   Implementação de cache (e.g., Redis) para endpoints de API frequentemente acessados.
    *   Refinamento da UI/UX do frontend.
    *   Containerização (Docker) para deploy facilitado.

## 3. Implementação de Logging e Coleta de Dados para Debug (Próxima Fase)

Esta seção será preenchida com os detalhes da implementação do sistema de logging, conforme planejado na próxima fase do desenvolvimento.
