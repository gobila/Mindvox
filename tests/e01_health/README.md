# Testes da E01: `GET /health`

Esta pasta contem os testes automatizados perenes da Spec E01.

O objetivo destes testes e garantir que o endpoint tecnico de saude da API continue funcionando antes de avancarmos para endpoints mais complexos.

## Hipoteses verificadas

### 1. A API responde ao health check

Teste:

```python
test_get_health_returns_expected_status_payload
```

Verifica que:

- `GET /health` retorna `200 OK`;
- a resposta segue exatamente o contrato da E01;
- a API devolve `status`, `service` e `version`;
- nenhum dado sensivel aparece na resposta.

Resposta esperada:

```json
{
  "status": "ok",
  "service": "mindvox-api",
  "version": "v1.0.0"
}
```

### 2. Metodo HTTP errado nao e aceito

Teste:

```python
test_post_health_is_not_allowed
```

Verifica que:

- `POST /health` nao e aceito;
- o FastAPI devolve `405 Method Not Allowed`;
- o endpoint permanece limitado ao metodo `GET`, como definido na E01.

Isso confirma que `/health` nao e um endpoint para envio de dados. Ele e apenas uma verificacao simples de disponibilidade da API.

### 3. A resposta nao expoe campos sensiveis

Teste:

```python
test_health_response_exposes_only_public_fields
```

Verifica que:

- a resposta contem somente `status`, `service` e `version`;
- a resposta nao contem termos como token, senha, segredo, `.env`, audio, transcricao, modelo ou path local.

Este teste nao prova todos os vazamentos laterais possiveis de um sistema em producao, mas certifica que o contrato executavel da E01 nao devolve dados sensiveis no corpo da resposta.

### 4. A documentacao OpenAPI registra o endpoint

Teste:

```python
test_openapi_documents_health_endpoint
```

Verifica que:

- `/openapi.json` contem a rota `/health`;
- o metodo `GET` aparece na documentacao;
- o `summary` do endpoint e `Health Check`;
- a `description` documentada e `Returns a minimal health status for the Mindvox API.`.

Isso garante que a documentacao automatica do FastAPI esta refletindo o contrato aprovado na Spec E01.

### 5. O contrato nao declara dados na URL nem body

Teste:

```python
test_openapi_declares_no_url_parameters_and_no_body
```

Verifica que:

- o OpenAPI nao declara parametros de path;
- o OpenAPI nao declara parametros de query;
- o OpenAPI nao declara corpo de requisicao.

Isso confirma que, pelo contrato oficial da API, o endpoint `/health` nao precisa receber informacao pela URL nem pelo corpo.

## Como executar

Na raiz do projeto:

```bash
uv run python -m unittest discover -s tests -v
```

Para executar apenas os testes da E01:

```bash
uv run python -m unittest discover -s tests/e01_health -v
```

## Relacao com a Spec

Estes testes verificam a parte executavel da Spec:

```text
docs/sdd/specs/E01_ENDPOINT_HEALTH.md
```

Eles nao substituem a Spec. A Spec define o contrato; estes testes confirmam que o codigo continua obedecendo a esse contrato.
