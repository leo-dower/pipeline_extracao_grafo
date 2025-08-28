# plataforma_juridica - Módulo de Ingestão da API CNJ DataJud

Este projeto implementa um módulo básico para ingestão de dados da API Pública do Conselho Nacional de Justiça (CNJ) - DataJud para uma instância do Elasticsearch. Ele permite obter metadados de processos judiciais, armazená-los e garantir a deduplicação.

## Funcionalidades

*   Conexão e requisições à API Pública do CNJ DataJud.
*   Indexação de metadados de processos no Elasticsearch.
*   Lógica de deduplicação baseada no `numeroProcesso` para evitar registros duplicados.
*   Paginação automática para lidar com grandes volumes de dados da API.

## Pré-requisitos

Antes de começar, certifique-se de ter os seguintes softwares instalados:

*   **Python 3.x**
*   **Elasticsearch**: Uma instância do Elasticsearch deve estar rodando e acessível (por padrão, em `http://localhost:9200`).

## Configuração

1.  **Navegue até o diretório do projeto:**
    ```bash
    cd C:\Users\Leonardo\OneDrive\scripts\plataforma_juridica
    ```

2.  **Instale as dependências Python:**
    As bibliotecas necessárias estão listadas no arquivo `requirements.txt`. Instale-as usando pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Verifique a conexão com o Elasticsearch:**
    Certifique-se de que seu servidor Elasticsearch está ativo e acessível na porta configurada (padrão: 9200).

## Uso

Para iniciar a ingestão de dados da API do CNJ para o Elasticsearch, execute o script principal:

```bash
python ingest_cnj_data.py
```

Por padrão, o script tentará ingerir dados do tribunal `api_publica_tjsp/_search`. Você pode modificar o script `ingest_cnj_data.py` para alterar o tribunal ou adicionar outros tribunais.

## Estrutura do Projeto

*   `cnj_api_client.py`: Contém a classe `CNJAPIClient` responsável por encapsular a lógica de comunicação com a API do CNJ, incluindo a chave de acesso e o tratamento de requisições.
*   `ingest_cnj_data.py`: O script principal que orquestra a busca de dados da API e a indexação no Elasticsearch, aplicando a lógica de deduplicação.
*   `requirements.txt`: Lista as dependências Python necessárias para o projeto.

## Testes

Para rodar os testes do projeto, certifique-se de ter o `pytest` instalado (já incluído no `requirements.txt`).

1.  **Navegue até o diretório do projeto:**
    ```bash
    cd C:\Users\Leonardo\OneDrive\scripts\plataforma_juridica
    ```
2.  **Execute o pytest:**
    ```bash
    pytest
    ```

## Próximos Passos

Este módulo é a base para futuras expansões, como:

*   **Interface Web:** Adicionar uma interface web para controlar a ingestão e visualizar o status.
*   **Múltiplos Tribunais:** Expandir a ingestão para cobrir todos os tribunais disponíveis na API.
*   **Análise de Grafo:** Integrar com um banco de dados de grafo (e.g., Neo4j) para análises de relacionamento entre processos e partes.
