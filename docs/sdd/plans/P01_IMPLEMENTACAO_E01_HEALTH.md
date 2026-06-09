# Plano P01: Implementacao do Endpoint E01 Health

## 1. Identificacao

- `ID`: `P01`
- `Tipo`: `Plano de Implementacao`
- `Status`: `fechado`
- `Spec alvo`: `E01_ENDPOINT_HEALTH.md`
- `Endpoint alvo`: `GET /health`
- `Data`: `2026-06-07`

---

## 2. Objetivo

Implementar o primeiro endpoint real do Mindvox:

```text
GET /health
```

O endpoint deve devolver uma resposta minima, estruturada e segura, sem autenticar usuario, sem acessar STT, sem carregar modelo e sem revelar configuracoes internas.

---

## 3. Estado Atual do Codigo

Arquivos relevantes:

- `src/main.py`
- `src/routers/services.py`
- `src/routers/llm_router.py`
- `src/class.py`
- `src/utils.py`

Situacao atual:

- `src/main.py` ja tenta criar a aplicacao FastAPI;
- `src/main.py` contem erro de sintaxe no bloco `FastAPI(...)`;
- `src/main.py` contem endpoint temporario `POST /items/`, que nao pertence ao MVP;
- `src/routers/services.py` contem ensaio de rota de transcricao, mas ainda nao segue a E02 fechada;
- `src/routers/services.py` esta incompleto e nao deve ser ligado ao app durante a implementacao da E01;
- `src/class.py`, `src/utils.py` e `src/routers/llm_router.py` estao vazios.

Regra:

- corrigir apenas o necessario para E01 funcionar;
- nao implementar E02 neste plano;
- nao instalar dependencias novas neste plano.

---

## 4. Decisoes de Implementacao

Implementacao proposta:

- manter `src/main.py` como ponto de entrada da aplicacao;
- corrigir a criacao de `FastAPI(...)`;
- remover ou substituir o endpoint temporario `POST /items/`;
- criar `src/routers/health.py` para o endpoint `GET /health`;
- registrar o router de health em `src/main.py`;
- usar resposta estruturada com `status`, `service` e `version`;
- evitar qualquer leitura de segredo, token, `.env`, modelo ou servico externo no health.

Resposta esperada:

```json
{
  "status": "ok",
  "service": "mindvox-api",
  "version": "v1.0.0"
}
```

---

## 5. Passos de Implementacao

1. Corrigir `src/main.py` para que a aplicacao FastAPI seja criada com sintaxe valida.
2. Remover o endpoint temporario `POST /items/` ou substitui-lo pelo registro do router real.
3. Criar `src/routers/health.py`.
4. Definir `APIRouter` para `GET /health`.
5. Declarar `summary`, `description`, `status_code` e resposta coerente com a E01.
6. Incluir o router de health em `src/main.py`.
7. Garantir que `src/routers/services.py` nao seja importado enquanto estiver incompleto.
8. Rodar verificacao de sintaxe.
9. Rodar a API localmente.
10. Testar `GET /health`.
11. Testar `POST /health` como metodo nao permitido.
12. Conferir `/docs` no FastAPI.
13. Criar teste automatizado perene cobrindo o contrato do endpoint.

---

## 6. Verificacoes

Comandos previstos:

```bash
uv run python -m py_compile src/main.py src/routers/health.py
```

```bash
uv run fastapi dev src/main.py
```

Teste manual valido previsto:

```bash
curl http://127.0.0.1:8000/health
```

Resposta esperada:

```json
{"status":"ok","service":"mindvox-api","version":"v1.0.0"}
```

Teste manual invalido previsto:

```bash
curl -X POST -i http://127.0.0.1:8000/health
```

Resultado esperado:

```text
405 Method Not Allowed
```

Documentacao:

```text
http://127.0.0.1:8000/docs
```

Teste automatizado perene:

```bash
uv run python -m unittest discover -s tests -v
```

---

## 7. Fora do Escopo Deste Plano

Este plano nao implementa:

- `POST /transcriptions/v1.0.0`;
- autenticacao por `Bearer token`;
- leitura de `MINDVOX_API_TOKEN`;
- leitura de `MINDVOX_MAX_UPLOAD_MB`;
- validacao de audio;
- chamada ao `mlx-whisper`;
- schemas completos da E02;
- testes automatizados completos da E02.

---

## 8. Criterios de Pronto

Este plano estara pronto quando:

- `src/main.py` compilar;
- `GET /health` responder `200 OK`;
- `POST /health` responder `405 Method Not Allowed`;
- a resposta seguir a E01;
- `/docs` listar o endpoint health;
- `tests/e01_health/test_health.py` validar sucesso, metodo invalido e metadados OpenAPI;
- o endpoint nao expuser dados sensiveis;
- o codigo nao importar a rota incompleta de transcricao;
- Adalberto conseguir explicar o que `FastAPI`, `APIRouter`, rota, handler e resposta fazem neste endpoint.

---

## 9. Observacao Didatica

Este endpoint e pequeno de proposito.

Ele serve para fixar o ciclo minimo:

```text
spec -> plano -> implementacao -> execucao -> teste -> explicacao
```

Depois dele, a implementacao da E02 deve repetir o mesmo ciclo com maior complexidade.

---

## 10. Registro de Fechamento

Status atual: `fechado`.

Fechado em: `2026-06-07`.

Motivo do fechamento:

- plano auditado contra a E01 fechada;
- rota, resposta, seguranca, logs, documentacao e testes previstos;
- teste invalido `POST /health` incluido;
- limites de escopo alinhados com a Spec;
- plano suficiente para orientar a implementacao do endpoint E01.
