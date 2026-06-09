# Tarefas T01: Implementacao do Endpoint E01 Health

## 1. Identificacao

- `ID`: `T01`
- `Tipo`: `Tarefas de Implementacao`
- `Status`: `concluida`
- `Spec alvo`: `E01_ENDPOINT_HEALTH.md`
- `Plano alvo`: `P01_IMPLEMENTACAO_E01_HEALTH.md`
- `Endpoint alvo`: `GET /health`
- `Data`: `2026-06-07`

---

## 2. Objetivo

Executar a implementacao do endpoint E01 Health conforme a Spec E01 fechada e o Plano P01 fechado.

---

## 3. Tarefas

| ID | Status | Tarefa | Criterio de conclusao |
| --- | --- | --- | --- |
| T01.01 | concluida | Corrigir a criacao de `FastAPI(...)` em `src/main.py` | `src/main.py` compila |
| T01.02 | concluida | Substituir o endpoint temporario `POST /items/` pelo endpoint real `GET /health` | O codigo nao deve mais declarar `/items/`; deve declarar a rota correta `/health` conforme a E01 |
| T01.03 | concluida | Criar `src/routers/health.py` | arquivo existe e declara router de health |
| T01.04 | concluida | Implementar `GET /health` | rota retorna `status`, `service` e `version` |
| T01.05 | concluida | Registrar o router de health em `src/main.py` | app inclui a rota `/health` |
| T01.06 | concluida | Garantir que `src/routers/services.py` nao seja importado ainda | rota incompleta de transcricao nao quebra a API |
| T01.07 | concluida | Verificar sintaxe Python | `py_compile` passa para arquivos da E01 |
| T01.08 | concluida | Rodar API localmente | servidor FastAPI sobe sem erro |
| T01.09 | concluida | Testar `GET /health` | retorna `200 OK` e JSON esperado |
| T01.10 | concluida | Testar `POST /health` | retorna `405 Method Not Allowed` |
| T01.11 | concluida | Conferir `/docs` | endpoint health aparece na documentacao |
| T01.12 | concluida | Explicar o endpoint implementado | Adalberto consegue explicar `FastAPI`, `APIRouter`, rota, handler e resposta |
| T01.13 | concluida | Criar testes automatizados perenes para E01 | `tests/e01_health/test_health.py` cobre sucesso, metodo invalido e OpenAPI |

---

## 3.1 Detalhamento Didatico da T01.02

A tarefa T01.02 existe porque `POST /items/` e apenas um exemplo generico comum em tutoriais de FastAPI. Ele nao pertence ao Mindvox e nao aparece em nenhuma Spec aprovada.

O endpoint correto da E01 e:

```text
GET /health
```

Portanto, ao executar esta tarefa, voce deve trocar a ideia de:

```python
@app.post("/items/")
def create_item():
    return {"message": "Item created"}
```

pela ideia de um endpoint de saude da API:

```python
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "mindvox-api",
        "version": "v1.0.0",
    }
```

O nome `health_check` e adequado porque descreve o que a funcao faz: verificar a saude basica da API. O motivo da substituicao e manter o codigo alinhado com a Spec E01 e impedir que um endpoint de exemplo apareca como se fosse parte real do MVP.

---

## 4. Comandos de Verificacao

Verificacao de sintaxe:

```bash
uv run python -m py_compile src/main.py src/routers/health.py
```

Testes automatizados:

```bash
uv run python -m unittest discover -s tests -v
```

Servidor local:

```bash
uv run fastapi dev src/main.py
```

Teste valido:

```bash
curl http://127.0.0.1:8000/health
```

Teste invalido:

```bash
curl -X POST -i http://127.0.0.1:8000/health
```

Documentacao:

```text
http://127.0.0.1:8000/docs
```

---

## 5. Fora do Escopo

Estas tarefas nao implementam:

- `POST /transcriptions/v1.0.0`;
- autenticacao da E02;
- validacao de audio;
- `mlx-whisper`;
- processamento de memoria;
- busca semantica ou relacional.

---

## 6. Criterio de Encerramento

Estas tarefas poderao ser encerradas quando:

- todas as tarefas estiverem marcadas como `concluida`;
- o endpoint `GET /health` estiver funcionando;
- os testes valido e invalido passarem;
- os testes automatizados perenes passarem;
- a documentacao do FastAPI exibir o endpoint;
- o codigo estiver pronto para iniciar a implementacao da E02.
