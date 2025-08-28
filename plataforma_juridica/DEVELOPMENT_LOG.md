## 4. Operações Git e Fluxo de Desenvolvimento

### 4.1. Criação e Envio do Branch `feature/api-ingestao-basica`

*   **Data:** 28 de agosto de 2025
*   **Ação:** Criação do branch `feature/api-ingestao-basica` para desenvolver as funcionalidades de ingestão da API CNJ, integração Neo4j, e o dashboard web com Groq API.
*   **Comando:** `git checkout -b feature/api-ingestao-basica`
*   **Resultado:** Branch criado e ativado localmente.

*   **Data:** 28 de agosto de 2025
*   **Ação:** Envio do branch `feature/api-ingestao-basica` para o repositório remoto (`origin`).
*   **Comando:** `git push --set-upstream origin feature/api-ingestao-basica`
*   **Resultado:** Branch `feature/api-ingestao-basica` e seus commits (incluindo a implementação inicial da ingestão, Neo4j, FastAPI/React e o sistema de logging) enviados para o GitHub.

### 4.2. Mesclagem do Branch `feature/api-ingestao-basica` no `main`

*   **Data:** 28 de agosto de 2025
*   **Objetivo:** Integrar as novas funcionalidades desenvolvidas no `feature/api-ingestao-basica` no branch principal `main`.
*   **Passos a Serem Executados:**
    1.  Mudar para o branch `main`.
    2.  Puxar as últimas alterações de `origin/main` para garantir que o `main` local esteja atualizado.
    3.  Mesclar o branch `feature/api-ingestao-basica` no `main`.
    4.  Enviar o branch `main` atualizado para o `origin`.
    5.  (Opcional) Excluir o branch `feature/api-ingestao-basica` localmente e remotamente.