# Relatorio da Segunda Auditoria: Implementacao E03

> **Status historico/superado em 2026-06-10.**
>
> Este relatorio registra uma rodada anterior de auditoria. Ele permanece no SDD como
> trilha metodologica, mas suas conclusoes de prontidao e seus achados de seguranca
> nao devem ser lidos como estado atual depois das correcoes posteriores.
>
> Em especial, foram corrigidos posteriormente pontos aqui apontados sobre upload,
> logs de autenticacao, provider, hardening publico, token didatico, Trusted Host,
> transporte seguro, documentacao publica e limites de metadados. Para o estado vigente,
> consultar `RELATORIO_AUDITORIA_FINAL_POS_CORRECAO_E03.md`, a Spec E03, P03, T03,
> README e os testes automatizados atuais.

## 1. Identificacao

- `Tipo`: segunda auditoria metodologica pos-correcao
- `Status`: relatorio conclusivo de auditoria, sem correcao aplicada nesta etapa
- `Data`: 2026-06-10
- `Endpoint principal`: `POST /processed-transcriptions/v1.0.0`
- `Escopo`: verificar correcoes da auditoria anterior, buscar regressões, novos problemas e falsos negativos
- `Documentos confrontados`:
  - `docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/plans/P03_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/tasks/T03_TAREFAS_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/reports/RELATORIO_CORRECAO_AUDITORIA_IMPLEMENTACAO_E03.md`
  - `tests/e03_processed_transcriptions/README.md`

---

## 2. Validacoes Executadas

| Validacao | Resultado | Evidencia |
| --- | --- | --- |
| Sintaxe E03/testes/script | passou | `uv run python -m py_compile ... scripts/benchmark_e03_models.py` sem erro |
| Suite E03 | passou | `35` testes OK |
| Suite geral | passou | `65` testes OK |
| Caixa-preta: `MINDVOX_API_TOKEN` vazio em E02/E03 | passou como rejeicao | Sem token, Bearer vazio e Bearer errado retornaram `401` |
| Caixa-preta: validacao de destino LLM | passou nos casos principais | Provider rejeitou IP privado/localhost; local rejeitou URL publica |
| Caixa-preta: hostname provider nao resolvido | aceito | `https://internal.example/v1` foi aceito por validacao sintatica |
| Caixa-preta: provider sensivel em `MINDVOX_LLM_PROVIDER` | falhou em sanitizacao defensiva | `processing_engine.name` retornou `secret-token-provider-openai-compatible` |
| Logs de autenticacao E03 | parcialmente suficiente | 401 foi logado como `processed_transcription_auth_failed reason=missing_credentials`, sem status/duracao |

Aviso recorrente nao bloqueante:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

Esse aviso nao decorre das correcoes da E03 e nao quebrou a suite.

---

## 3. Matriz de Validacao das Correcoes

| Falha original | Status na segunda auditoria | Evidencia | Observacao |
| --- | --- | --- | --- |
| F01: logs nao cobriam erros controlados de validacao do handler | corrigida no handler, com lacuna adjacente | `test_controlled_validation_errors_are_logged_without_sensitive_values` passou; `src/routers/processed_transcriptions.py` captura `HTTPException` no handler | Autenticacao ocorre antes do handler e ainda nao usa o mesmo formato status/duracao; ver FN-02 |
| F02: cliente LLM sem limite de tokens/resposta | corrigida | `test_llm_client_sends_max_tokens_and_limits_response_size` e `test_llm_client_rejects_excessive_response_body` passaram | Tambem existe fallback para `MINDVOX_LLM_MAX_OUTPUT_TOKENS=0` |
| F03: sem validacao de destino `provider`/`local` | corrigida nos casos principais | `test_provider_mode_rejects_localhost_endpoint` e `test_local_mode_rejects_public_endpoint` passaram | Validacao nao resolve DNS; ver FN-04 |
| F04: lacunas de testes de borda e falha | corrigida | Suite E03 tem 35 testes, incluindo input invalido, audio ausente, content type, metadado, local indisponivel, saida LLM invalida | Cobertura melhorou materialmente |
| F05: benchmark aceitava chave literal por CLI | corrigida | `scripts/benchmark_e03_models.py` usa quarto argumento como nome de variavel de ambiente | Sem chave literal em argumento CLI |
| F06: schema do benchmark divergia em `processing_notes` | corrigida | Benchmark exige `processing_notes` como lista estruturada | Alinhado ao contrato da E03 |
| F07: rastreabilidade documental incompleta | corrigida | README, E03, P03, T03, README de testes e relatorio de correcao foram atualizados | Segunda auditoria encontrou novos pontos nao cobertos pela primeira auditoria |

Conclusao da matriz: as falhas originais foram corrigidas em seus pontos principais. A segunda auditoria encontrou lacunas adjacentes e falsos negativos, nao uma reversao direta das correcoes.

---

## 4. Novas Falhas Introduzidas Apos a Correcao

Nao foi encontrada regressao funcional direta introduzida pela correcao final.

Houve uma regressao temporaria durante a correcao (`MINDVOX_MAX_UPLOAD_MB=0` deixou de bloquear upload em teste da E02), mas ela foi corrigida antes desta segunda auditoria. A suite geral final passou com `65` testes OK.

---

## 5. Problemas Anteriormente Nao Detectados

### FN-01: Upload e lido integralmente em memoria antes da rejeicao por tamanho

- `Severidade`: Media
- `Tipo`: falso negativo da primeira auditoria
- `Local`:
  - `src/routers/transcriptions.py`, linhas 176-178
  - `src/routers/processed_transcriptions.py`, linhas 345-347
- `Evidencia`:

```text
audio_bytes = await audio_file.read()
_validate_size(...)
```

e:

```text
audio_bytes = await audio_file.read()
_validate_audio_size(...)
```

- `Impacto`: um cliente autenticado, ou alguem com token vazado, pode forcar leitura integral de arquivo grande antes de a aplicacao aplicar o limite configurado. Em ambiente sem limite de corpo no proxy/ASGI, isso pode causar consumo excessivo de memoria.
- `Por que passou antes`: a primeira auditoria verificou a existencia de limite `413`, mas nao auditou se o limite era aplicado antes ou depois de materializar o upload inteiro em memoria.
- `Correcao recomendada`: impor limite de corpo no edge/proxy e, no app, ler `UploadFile` em chunks, abortando quando ultrapassar `MINDVOX_MAX_UPLOAD_MB`.

### FN-02: Logs de autenticacao nao seguem o mesmo padrao de status/duracao

- `Severidade`: Baixa a Media
- `Tipo`: falso negativo / lacuna adjacente a F01
- `Local`:
  - `src/routers/processed_transcriptions.py`, linhas 52-67
  - `src/routers/transcriptions.py`, linhas 39-54
- `Evidencia caixa-preta`: requisicao E03 sem token retornou `401` e logou apenas:

```text
processed_transcription_auth_failed reason=missing_credentials
```

- `Impacto`: nao ha vazamento sensivel, mas a observabilidade fica menos uniforme. Falhas de autenticacao nao trazem `status_code`, `error_code` e `duration_ms`, ao contrario das falhas do handler E03.
- `Por que passou antes`: a correcao se concentrou no `try/except` do handler; dependencias FastAPI executam antes de entrar no handler.
- `Correcao recomendada`: padronizar logs de autenticacao com `status_code=401/503`, `error_code=...` e, se viavel, duracao aproximada ou marcador de fase `auth`.

### FN-03: `MINDVOX_LLM_PROVIDER` pode vazar marcador sensivel em `processing_engine.name`

- `Severidade`: Media
- `Tipo`: falso negativo de sanitizacao de configuracao
- `Local`: `src/services/postprocessing_service.py`, linhas 308-312
- `Evidencia`:

```text
provider = settings.llm_provider.strip() or mode
name=f"{provider}-openai-compatible"
```

- `Teste caixa-preta`: com `MINDVOX_LLM_PROVIDER=secret-token-provider`, a resposta retornou:

```json
{"name": "secret-token-provider-openai-compatible"}
```

- `Impacto`: se o operador configurar equivocadamente um valor sensivel em `MINDVOX_LLM_PROVIDER`, a API o devolve ao cliente. Isso viola a intencao do SDD de nao expor token, chave ou path sensivel em respostas.
- `Por que passou antes`: os testes verificaram token, erro, path e modelo, mas nao provider name. O modelo possui sanitizacao defensiva (`_public_model`), mas o provider nao.
- `Correcao recomendada`: aplicar sanitizacao equivalente ao provider ou restringir provider a padrao publico seguro, com fallback para `configured-provider`.

### FN-04: Validacao de destino `provider` nao resolve DNS

- `Severidade`: Baixa a Media
- `Tipo`: risco residual de defesa em profundidade
- `Local`: `src/services/postprocessing_service.py`, linhas 328-358
- `Evidencia caixa-preta`:

```text
provider_private_ip_https REJECT
provider_loopback_hostname_https REJECT
provider_unknown_hostname_https ACCEPT
```

- `Impacto`: um hostname aparentemente externo, mas resolvido por DNS interno para IP privado, poderia passar pela validacao. Como `MINDVOX_LLM_BASE_URL` vem de ambiente e nao do usuario final, o risco e principalmente de misconfiguracao operacional, nao de exploracao direta por request HTTP.
- `Por que passou antes`: a primeira auditoria validou IPs literais e localhost, mas nao avaliou resolucao DNS.
- `Correcao recomendada`: para modo `provider`, resolver hostname e rejeitar enderecos privados/loopback/link-local resultantes, ou documentar explicitamente que a garantia de DNS/egress e responsabilidade do deploy.

### FN-05: Script de benchmark ainda le resposta HTTP sem limite de bytes

- `Severidade`: Baixa
- `Tipo`: falso negativo em ferramenta auxiliar
- `Local`: `scripts/benchmark_e03_models.py`, linhas 204-205
- `Evidencia`:

```text
response_body = response.read().decode("utf-8")
```

- `Impacto`: se um provider ou servidor local se comportar mal, o script pode ler resposta muito grande em memoria. O risco e menor porque o script e auxiliar, local e grava saidas em `.benchmarks/`, pasta ignorada pelo Git.
- `Por que passou antes`: a auditoria anterior exigiu remover chave literal e alinhar schema, mas nao aplicou ao script o mesmo limite de leitura criado para o cliente da aplicacao.
- `Correcao recomendada`: reaproveitar a regra de limite de bytes do cliente E03 ou adicionar `--max-response-bytes` ao script.

---

## 6. Avaliacao Geral de Conformidade

### E03 / P03 / T03

O codigo final atende substancialmente a E03/P03/T03 quanto a:

- contrato HTTP;
- autenticacao Bearer;
- validacao de entrada principal;
- limites configuraveis;
- cinco entregas publicas;
- modo `contract`;
- modo `provider`;
- modo `local`;
- destino LLM por modo;
- erros controlados;
- OpenAPI;
- testes automatizados;
- logs sanitizados para fluxo de handler;
- ausencia de chave real detectada no repo.

O endpoint ainda nao pode ser fechado canonicamente porque permanecem pendentes:

- prova real humana em modo `local` ou `provider`;
- registro dessa prova real;
- revisao final de Git;
- commit de fechamento.

Esses itens ja aparecem como pendentes no proprio T03/SDD, portanto nao sao desvio oculto.

---

## 7. Prontidao para Producao

`Resultado`: Nao para producao publica; com ressalvas para MVP academico/local.

Motivos:

- O app ainda usa defaults FastAPI com `/docs` e `/openapi.json` expostos, apropriado para demonstracao local, mas nao suficiente para API publica sensivel.
- Nao ha `TrustedHostMiddleware` ou politica equivalente visivel no app.
- Nao ha rate limiting no app.
- Upload e lido integralmente antes da verificacao de tamanho.
- A protecao de corpo maximo, TLS, headers e protecao de Swagger ficam assumidas como responsabilidade de deploy/proxy, conforme risco ja documentado, mas nao implementadas no codigo.

Para a entrega academica local e demonstracao controlada, a E03 esta em bom estado tecnico, desde que a prova real humana seja executada e registrada.

---

## 8. Recomendacoes Finais

1. Corrigir FN-01 antes de qualquer exposicao publica ou uso com usuarios externos.
2. Corrigir FN-03 antes de fechamento se o criterio de "sem vazamento por configuracao" for interpretado de forma estrita.
3. Corrigir FN-02 para uniformizar auditoria operacional e facilitar analise de incidentes.
4. Tratar FN-04 como decisao: resolver DNS no app ou declarar explicitamente no SDD que e responsabilidade de egress/deploy.
5. Tratar FN-05 como baixo risco, mas simples de resolver no script de benchmark.
6. Manter a E03 como `aberta` ate prova real humana em `local` ou `provider`.
