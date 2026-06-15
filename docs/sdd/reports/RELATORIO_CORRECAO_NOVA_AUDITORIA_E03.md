# Relatorio de Correcao da Nova Auditoria Pos-Correcao E03

## 1. Identificacao

- `Data`: 2026-06-10
- `Origem`: `RELATORIO_NOVA_AUDITORIA_POS_CORRECAO_E03.md`
- `Escopo`: correcao das falhas `PA-01`, `PA-02`, `PA-03` e `PA-04`
- `Endpoint principal`: `POST /processed-transcriptions/v1.0.0`
- `Endpoint tambem afetado`: `POST /transcriptions/v1.0.0`, por compartilhar metadados e token

## 2. Sumario Executivo

As falhas apontadas pela nova auditoria foram corrigidas com alteracoes em codigo, testes e documentacao.

As correcoes principais foram:

- limite de tamanho para `course`, `discipline` e `class_title`;
- rejeicao de placeholder de `MINDVOX_API_TOKEN`;
- modo de deploy publico com docs desabilitados por padrao e `TrustedHostMiddleware`;
- allowlist de hostnames para provider LLM externo.

Emenda de hardening publico em `2026-06-10`:

- `dev-token` passou a ser tratado como token ausente quando `MINDVOX_PUBLIC_DEPLOYMENT=true`;
- `MINDVOX_TRUSTED_HOSTS=*` passou a impedir inicializacao quando `MINDVOX_PUBLIC_DEPLOYMENT=true`;
- E02 e E03 passaram a exigir que a aplicacao receba scheme `https` nos endpoints de negocio protegidos em deploy publico, retornando `403 Forbidden` quando isso nao ocorrer;
- a aplicacao nao confia em `X-Forwarded-Proto` enviado livremente pelo cliente; se TLS terminar em proxy, o proxy e o servidor ASGI devem repassar o scheme `https` de modo confiavel.

## 3. Matriz de Falhas e Correcoes

| Falha | Criticidade | Causa raiz | Correcao aplicada | Evidencia de validacao |
| --- | --- | --- | --- | --- |
| `PA-01`: metadados opcionais aceitavam texto excessivo | Media | `course`, `discipline` e `class_title` eram apenas limpos por `strip`, sem limite | Criado `routers/metadata_validation.py` com limites compartilhados: `course=160`, `discipline=120`, `class_title=200`; E02/E03 passaram a usar o helper | `test_post_transcriptions_rejects_oversized_metadata_text`; `test_oversized_optional_metadata_returns_422` |
| `PA-02`: hardening insuficiente para producao publica | Media em producao | `FastAPI(...)` usava defaults de docs e nao havia validacao de Host header | Criado `create_app`; `MINDVOX_PUBLIC_DEPLOYMENT=true` exige `MINDVOX_TRUSTED_HOSTS`; docs ficam desabilitados por padrao; `TrustedHostMiddleware` e aplicado quando hosts sao configurados | `test_public_deployment_requires_trusted_hosts`; `test_public_deployment_disables_docs_and_enforces_trusted_hosts` |
| `PA-03`: placeholder de `MINDVOX_API_TOKEN` podia virar token real | Baixa/Media | `get_settings` lia qualquer valor textual como token valido | `settings._read_api_token` passa a tratar vazio, `replace-with-local-token` e `<set-real-token-only-in-local-env>` como token ausente | `test_post_transcriptions_rejects_placeholder_api_token_configuration`; `test_placeholder_api_token_configuration_returns_503` |
| `PA-04`: risco residual de provider DNS/check-then-use | Baixa/Media | O provider era validado por URL/DNS, mas qualquer host externo configurado podia ser usado | `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` restringe hostnames aceitos; em deploy publico com provider a allowlist e obrigatoria | `test_provider_mode_rejects_hostname_outside_allowed_list`; `test_provider_mode_accepts_hostname_inside_allowed_list` |

Complemento das falhas `PA-02` e `PA-03`:

| Falha complementar | Criticidade | Causa raiz | Correcao aplicada | Evidencia de validacao |
| --- | --- | --- | --- | --- |
| Wildcard em `MINDVOX_TRUSTED_HOSTS` neutralizava Trusted Host | Media em deploy publico | A configuracao aceitava `*` mesmo em modo publico | `create_app` rejeita wildcard quando `MINDVOX_PUBLIC_DEPLOYMENT=true` | `test_public_deployment_rejects_wildcard_trusted_hosts` em E02/E03 |
| `dev-token` continuava valido em modo publico | Media em deploy publico | O token didatico nao era tratado como placeholder contextual | `_read_api_token(public_deployment=True)` trata `dev-token` como ausente | `test_post_transcriptions_rejects_dev_token_in_public_deployment`; `test_dev_token_configuration_returns_503_in_public_deployment` |
| Transporte seguro nao era exigido pelos endpoints de negocio | Media em deploy publico | O modo publico protegia docs/Host, mas nao recusava HTTP nos endpoints protegidos | E02/E03 chamam `require_secure_transport_for_public_request`; HTTP retorna `403` quando `request.url.scheme != "https"` | `test_post_transcriptions_requires_https_in_public_deployment`; `test_public_deployment_requires_https_for_processed_transcriptions`; testes positivos com scheme `https` |

## 4. Arquivos Alterados

Codigo:

- `src/settings.py`
- `src/main.py`
- `src/routers/endpoint_security.py`
- `src/routers/metadata_validation.py`
- `src/routers/transcriptions.py`
- `src/routers/processed_transcriptions.py`
- `src/services/postprocessing_service.py`

Testes:

- `tests/e02_transcriptions/test_transcriptions.py`
- `tests/e03_processed_transcriptions/test_processed_transcriptions.py`
- `tests/e03_processed_transcriptions/README.md`

Documentacao:

- `.env.example`
- `README.md`
- `docs/sdd/specs/E02_ENDPOINT_TRANSCRIPTIONS.md`
- `docs/sdd/plans/P02_IMPLEMENTACAO_E02_TRANSCRIPTIONS.md`
- `docs/sdd/tasks/T02_TAREFAS_IMPLEMENTACAO_E02_TRANSCRIPTIONS.md`
- `docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`
- `docs/sdd/plans/P03_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`
- `docs/sdd/tasks/T03_TAREFAS_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`

## 5. Evidencias de Validacao

Comando de sintaxe:

```bash
uv run python -m py_compile src/main.py src/settings.py src/routers/metadata_validation.py src/routers/transcriptions.py src/routers/processed_transcriptions.py src/services/postprocessing_service.py tests/e02_transcriptions/test_transcriptions.py tests/e03_processed_transcriptions/test_processed_transcriptions.py
```

Resultado: passou sem erros.

Comando de regressao geral:

```bash
uv run python -m unittest discover -s tests -v
```

Resultado:

```text
Ran 79 tests ... OK
```

Validacao complementar da emenda de hardening publico em `2026-06-10`:

```bash
uv run python -m py_compile src/main.py src/settings.py src/routers/endpoint_security.py src/routers/transcriptions.py src/routers/processed_transcriptions.py tests/e02_transcriptions/test_transcriptions.py tests/e03_processed_transcriptions/test_processed_transcriptions.py scripts/benchmark_e03_models.py
uv run python -m unittest tests.e02_transcriptions.test_transcriptions tests.e03_processed_transcriptions.test_processed_transcriptions tests.e03_processed_transcriptions.test_e03_test_plan -v
uv run python -m unittest discover -s tests -v
git diff --check
```

Resultado:

```text
py_compile: OK
E02/E03/teste documental: Ran 82 tests ... OK
suite geral: Ran 87 tests ... OK
git diff --check: OK
```

## 6. Revisao de Seguranca

A correcao seguiu os pontos aplicaveis da skill `security-best-practices`:

- entradas de formulario agora possuem limites tambem nos metadados opcionais;
- erro de metadado grande e controlado e nao ecoa o valor recebido;
- token de exemplo nao e mais aceito como credencial real;
- docs publicas podem ser desligadas por configuracao segura de producao;
- Host header pode ser restringido por `TrustedHostMiddleware`;
- provider externo pode ser restringido por allowlist de hostname;
- modo `provider` continua rejeitando URL local/privada e hostname que resolva para IP local/privado.

## 7. Riscos Residuais

Ainda permanecem como responsabilidades de deploy publico:

- TLS;
- rate limiting;
- limite maximo de corpo no proxy/edge;
- egress policy/firewall para defesa adicional contra DNS malicioso.

Esses pontos nao bloqueiam o MVP academico local, mas devem ser tratados antes de exposicao publica real.

## 8. Conclusao

As falhas `PA-01`, `PA-02`, `PA-03` e `PA-04` foram corrigidas no nivel apropriado para o escopo atual do Mindvox.

A E03 continua exigindo prova real humana em modo `local` ou `provider` antes do fechamento canonico e do commit final.
