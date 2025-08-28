# Plano de Implementação: Integração com a API de Dados Abertos da Câmara dos Deputados

**Objetivo:** Enriquecer o grafo de conhecimento jurídico existente com dados detalhados sobre a legislação federal, obtidos diretamente da API da Câmara dos Deputados. O foco inicial será a busca por proposições (projetos de lei) e seus detalhes.

**Branch Git:** `feature/integracao-camara-api`

---

### Fase 1: Exploração e Configuração

1.  **Estudo da Documentação da API:**
    *   **Ação:** Analisar a documentação oficial da API de Dados Abertos da Câmara (https://dadosabertos.camara.leg.br/swagger/api.html).
    *   **Foco:** Entender os *endpoints* principais, especialmente `/proposicoes` e `/proposicoes/{id}`. Identificar os parâmetros de busca (ex: por sigla, número, ano) e a estrutura dos dados de resposta (JSON).
    *   **Resultado Esperado:** Conhecimento claro de como buscar uma lei e obter seus detalhes, como autor, tramitação e texto integral.

2.  **Atualização do Arquivo de Configuração (`config.ini`):**
    *   **Ação:** Adicionar uma nova seção `[API_CAMARA]` ao arquivo `config.ini`.
    *   **Conteúdo:** Adicionar a URL base da API: `BASE_URL = https://dadosabertos.camara.leg.br/api/v2`.
    *   **Resultado Esperado:** Centralizar a URL da API, facilitando futuras manutenções.

---

### Fase 2: Desenvolvimento do Módulo de Acesso à API

1.  **Criação de um Novo Módulo Python:**
    *   **Ação:** Criar um novo arquivo, `plataforma_juridica/api_camara_client.py`.
    *   **Propósito:** Isolar toda a lógica de comunicação com a API da Câmara, mantendo o código principal (`pipeline_extracao_grafo.py`) limpo.

2.  **Implementação da Classe `ApiCamaraClient`:**
    *   **Ação:** Dentro de `api_camara_client.py`, criar uma classe `ApiCamaraClient`.
    *   **Métodos a Implementar:**
        *   `__init__(self, base_url)`: Construtor que recebe a URL base da API.
        *   `_fazer_requisicao(self, endpoint, params=None)`: Um método privado para lidar com as requisições GET, incluindo tratamento de erros (HTTP status codes) e parsing do JSON de resposta.
        *   `buscar_proposicao(self, sigla_tipo, numero, ano)`: Busca por uma proposição específica (ex: PL 123 2022). Este método usará o endpoint `/proposicoes`.
        *   `obter_detalhes_proposicao(self, id_proposicao)`: Busca os detalhes completos de uma proposição usando seu ID (obtido a partir de `buscar_proposicao`). Usará o endpoint `/proposicoes/{id}`.
        *   `obter_autores_proposicao(self, id_proposicao)`: Busca os autores de uma proposição. Usará o endpoint `/proposicoes/{id}/autores`.

---

### Fase 3: Integração com o Pipeline Principal

1.  **Modificação do Pipeline Principal (`pipeline_extracao_grafo.py`):**
    *   **Ação:** Alterar o script principal para usar o novo `ApiCamaraClient`.
    *   **Importação:** Adicionar `from api_camara_client import ApiCamaraClient` no início do arquivo.

2.  **Atualização da Função `main`:**
    *   **Ação:** Instanciar o `ApiCamaraClient` após ler as configurações.
    *   **Código:**
        ```python
        # ... dentro da função main()
        camara_api_url = config['API_CAMARA']['BASE_URL']
        camara_client = ApiCamaraClient(camara_api_url)
        # Passar o 'camara_client' para as funções que precisarão dele
        ```

3.  **Enriquecimento dos Nós no Grafo:**
    *   **Ação:** Modificar a função `extrair_e_popular_grafo` para, após encontrar e normalizar uma entidade do tipo "Lei", usar o `camara_client` para buscar mais dados.
    *   **Lógica:**
        1.  Quando uma `Lei` for extraída (ex: "Lei nº 9.503/1997"), fazer o parsing para extrair o tipo ("Lei"), número ("9503") e ano ("1997").
        2.  Chamar `camara_client.buscar_proposicao()` com esses dados.
        3.  Se a proposição for encontrada, obter seu ID.
        4.  Com o ID, chamar `obter_detalhes_proposicao()` e `obter_autores_proposicao()`.
        5.  **Atualizar o Grafo:**
            *   Adicionar novas propriedades ao nó `:Lei` (ex: `ementa`, `status`).
            *   Criar novos nós para os autores, ex: `MERGE (a:Autor {nome: $nome_autor, tipo: $tipo_autor})`.
            *   Criar a relação `MERGE (a)-[:AUTOR_DE]->(l:Lei {id: $id_lei})`.

---

### Fase 4: Testes e Validação

1.  **Testes Unitários (Sugestão):**
    *   **Ação:** Criar um arquivo de teste `tests/test_api_camara_client.py` para testar o cliente da API de forma isolada.
    *   **Casos de Teste:**
        *   Testar a busca por uma lei conhecida.
        *   Testar o tratamento de erro para uma lei inexistente (HTTP 404).
        *   Testar a extração de autores.

2.  **Teste de Integração:**
    *   **Ação:** Executar o pipeline completo com um PDF de teste que contenha citações de leis federais.
    *   **Verificação:** Consultar o banco de dados Neo4j para confirmar que os nós `:Lei` foram enriquecidos com as novas propriedades e que os nós `:Autor` e as relações `[:AUTOR_DE]` foram criados corretamente.
