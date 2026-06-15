# Testes da E03: `POST /processed-transcriptions/v1.0.0`

Esta pasta concentra os testes automatizados perenes da Spec E03, relativa ao endpoint de pos-processamento de transcricoes.

O objetivo destes testes e verificar o contrato HTTP do endpoint: rota, autenticacao, entrada por audio ou texto bruto, saida estruturada, erros previsiveis, documentacao OpenAPI, seguranca, logs sanitizados e modo `contract`.

## Hipoteses verificadas

- Uma requisicao valida com `Authorization: Bearer <token>`, `input_type=raw_text` e modo `contract` retorna `200 OK`.
- A documentacao OpenAPI deve explicar que `input_type` aceita somente os valores exatos `audio` e `raw_text`, em ingles, minusculos e sem acento.
- O OpenAPI deve tipar `input_type` como `Enum`, permitindo que o Swagger apresente lista de selecao/dropdown com `audio`, `raw_text` e o alias `raw_text_file`.
- A documentacao OpenAPI deve explicar que, ao enviar texto ja transcrito, o usuario deve usar `input_type=raw_text`, preencher `raw_text` ou anexar `raw_text_file` em `.txt`, e deixar `audio_file` vazio.
- Por ergonomia do Swagger, a API aceita `input_type=raw_text_file` como alias de `raw_text` quando o usuario anexar uma transcricao `.txt`.
- A documentacao OpenAPI deve explicar que `raw_text_file` permite reiniciar o pos-processamento de uma transcricao ja existente sem repetir STT.
- Campos textuais opcionais devem iniciar vazios no OpenAPI/Swagger; se cliente antigo ou tela cacheada enviar o literal `string`, o backend deve tratar esse valor como ausente.
- A documentacao OpenAPI deve explicar que, ao enviar audio, o usuario deve usar `input_type=audio`, preencher `audio_file` e deixar `raw_text` e `raw_text_file` vazios.
- A resposta de sucesso contem as cinco entregas publicas: `raw_text`, `didactic_text`, `themes`, `technical_terms` e `technology_mentions`.
- A resposta de sucesso tambem contem `processing_notes`, `metadata`, `source` e `processing_engine`.
- Quando a entrada for `raw_text`, `source.input_origin` deve ser `raw_text`, `source.raw_text_origin` deve ser `provided_by_client` e `source.transcription` deve ser `null`.
- Quando viavel em modo `contract`, uma requisicao com `input_type=audio` deve simular o fluxo audio -> transcricao interna -> pos-processamento e retornar as cinco entregas.
- Quando `input_type=audio`, a transcricao bruta interna deve salvar automaticamente JSON tecnico em `MINDVOX_TRANSCRIPTION_OUTPUT_DIR` e TXT humano em `MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR`.
- Quando `input_type=audio`, a transcricao bruta interna deve entrar em fila local antes do pos-processamento, permitindo retry sem reenviar audio.
- Quando o pos-processamento conclui, a resposta estruturada da E03 deve ser salva como JSON tecnico em `MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR`.
- Quando o pos-processamento conclui, a E03 deve salvar tambem um artefato Markdown (`.md`) legivel para humano em `MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR`.
- Quando metadados de aula forem enviados, os artefatos processados podem usar prefixo seguro com data/titulo/sessao, e o Markdown humano deve usar titulo legivel e bloco curto de metadados.
- A resposta de sucesso contem `artifact_locations`, indicando caminho relativo do artefato humano e do JSON tecnico sem expor path absoluto local.
- Quando o pos-processamento falha apos STT, o job deve permanecer em `queue/pending` e poder ser reprocessado sem novo upload.
- Quando `input_type=raw_text`, a E03 nao cria artefato de STT, pois o texto bruto foi fornecido pelo cliente.
- O modo usado nos testes automatizados deve manter STT e pos-processamento em contrato, seja com `MINDVOX_TRANSCRIPTION_MODE=contract` e `MINDVOX_POSTPROCESSING_MODE=auto`, seja com ambos explicitamente em `contract`.
- Em modo `contract`, a aplicacao nao deve iniciar `llama-server`.
- Em modo `local` com `MINDVOX_LOCAL_LLM_AUTOSTART=true`, a aplicacao deve iniciar `llama-server` ou falhar claramente quando faltar binario, modelo ou prontidao.
- Em desenvolvimento local, `MINDVOX_API_TOKEN` ausente ou vazio deve usar automaticamente o token didatico `dev-token`.
- A API rejeita requisicao sem token com `401 Unauthorized`.
- A API rejeita token invalido com `401 Unauthorized`.
- A API trata placeholder de `MINDVOX_API_TOKEN` como token ausente.
- A API rejeita header `Authorization` malformado com `401 Unauthorized`.
- A API trata `dev-token` como token ausente quando `MINDVOX_PUBLIC_DEPLOYMENT=true`.
- Em `MINDVOX_PUBLIC_DEPLOYMENT=true`, ausencia de `MINDVOX_API_TOKEN` nao deve criar token padrao.
- O perfil `contract` deve forcar STT/E03 em contrato e desligar autostart do Llama.
- O perfil `prod` deve ligar endurecimento publico, exigir host confiavel/token externo e desligar Llama local.
- O Swagger/OpenAPI deve mostrar `Active startup profile` no cabecalho da API, indicando `dev`, `contract` ou `prod`, a partir de `MINDVOX_RUNTIME_PROFILE` inferido ou definido pelo perfil de inicializacao.
- Em `MINDVOX_PUBLIC_DEPLOYMENT=true`, `POST /processed-transcriptions/v1.0.0` retorna `403 Forbidden` quando a aplicacao nao recebe scheme `https`.
- Em `MINDVOX_PUBLIC_DEPLOYMENT=true`, `POST /processed-transcriptions/v1.0.0` aceita requisicao que chega a aplicacao com scheme `https`.
- A API rejeita `input_type` ausente ou invalido com `422 Unprocessable Entity`.
- A API rejeita `input_type=raw_text` sem `raw_text` ou `raw_text_file` com `422 Unprocessable Entity`.
- A API rejeita `input_type=audio` sem `audio_file` com `422 Unprocessable Entity`.
- A API trata placeholder vazio de upload opcional como ausente.
- A API rejeita envio simultaneo de `audio_file` e `raw_text` ou `raw_text_file` com `422 Unprocessable Entity`.
- A API rejeita envio simultaneo de `raw_text` e `raw_text_file` com `422 Unprocessable Entity`.
- A API rejeita `raw_text_file` fora de `.txt` com `400 Bad Request`.
- A API rejeita `processing_profile` invalido com `422 Unprocessable Entity`.
- A API rejeita extensao de audio fora de `.wav` e `.m4a` com `400 Bad Request`.
- A API rejeita `content_type` de audio incompativel com `400 Bad Request`.
- A API rejeita metadados invalidos com `422 Unprocessable Entity`.
- A API rejeita `course`, `discipline` e `class_title` acima dos limites definidos com `422 Unprocessable Entity`.
- A API rejeita `raw_text` acima de `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS=150000` com `413 Payload Too Large`.
- A API rejeita upload de audio acima de `MINDVOX_MAX_UPLOAD_MB` com `413 Payload Too Large`.
- A leitura de upload de audio e incremental e interrompe antes de consumir o arquivo inteiro quando o limite e excedido.
- A API retorna `503 Service Unavailable` quando o motor de pos-processamento ou STT necessario estiver indisponivel.
- A API retorna `503 Service Unavailable` quando estiver em modo `provider` e `MINDVOX_LLM_API_KEY` estiver vazio ou contiver placeholder de exemplo, como `replace-with-provider-key`.
- A API rejeita endpoint local em modo `provider`, hostname provider que resolva para IP local/privado, hostname fora da allowlist quando configurada e endpoint publico em modo `local`, evitando envio acidental do bruto ao destino errado.
- Em modo publico, a aplicacao exige `MINDVOX_TRUSTED_HOSTS`, rejeita `MINDVOX_TRUSTED_HOSTS=*`, desabilita docs por padrao e rejeita Host header fora da lista.
- O cliente LLM envia `MINDVOX_LLM_MAX_OUTPUT_TOKENS` e limita o tamanho da resposta lida.
- O script interno de benchmark tambem limita o tamanho da resposta HTTP lida.
- O pipeline longo da E03 e opcional por configuracao: `MINDVOX_POSTPROCESSING_CHUNKING_MODE=off|tfidf`.
- Quando ativado, o pipeline longo preserva `raw_text` original, aplica pre-auditoria lexical em texto interno derivado, divide a entrada por TF-IDF, processa chunks separadamente, executa merge canonico e audita os campos semanticos finais.
- Suspeitas remanescentes da pre-auditoria nao devem ser promovidas para `didactic_text`, `themes`, `technical_terms` ou `technology_mentions`; no maximo aparecem em `processing_notes`.
- `MINDVOX_LLM_MAX_OUTPUT_TOKENS=0` e tratado como invalido e volta ao padrao seguro.
- Saida quase correta do LLM, com aliases previsiveis, cerca Markdown ou valores em portugues para confianca/categoria, e normalizada para o contrato E03 quando contem texto didatico principal.
- Saida invalida do LLM retorna erro controlado sem expor a resposta integral.
- Saida de LLM estruturalmente valida, mas semanticamente insuficiente para transcricao longa, aciona retry com instrucao mais rigorosa; se continuar insuficiente, retorna `502` estruturado com `error_code=postprocessing_quality_rejected` e salva a saida rejeitada em quarentena com `runtime_snapshot`.
- Jobs de audio com falhas repetidas respeitam `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS` e vao para `queue/failed/` quando o limite e atingido.
- A API retorna `504 Gateway Timeout` quando provider externo ou servidor local compativel com OpenAI nao responder dentro do timeout configurado.
- A API rejeita metodo HTTP incorreto para a rota com `405 Method Not Allowed`.
- A documentacao OpenAPI apresenta a rota, o formulario `multipart/form-data`, o esquema Bearer, as descricoes didaticas dos campos, as cinco entregas e as respostas `400`, `401`, `403`, `405`, `413`, `422`, `500`, `502`, `503` e `504`.
- A documentacao OpenAPI informa que, em modo `provider`, o conteudo bruto e enviado ao provider externo configurado.
- Respostas, erros e logs nao devem expor token, `.env`, paths locais, audio bruto, transcricao integral, prompt integral, provider sensivel ou resposta integral de provider.

## Matriz minima de testes

| Teste | Hipotese |
| --- | --- |
| `test_e03_test_plan_documents_required_contract` | Teste documental inicial: garante que README e Spec registram a matriz obrigatoria da E03 antes da implementacao |
| `test_post_processed_transcriptions_raw_text_contract_success` | Sucesso com `raw_text` em modo `contract` |
| `test_post_processed_transcriptions_raw_text_file_contract_success` | Sucesso com `raw_text_file` `.txt` em modo `contract` |
| `test_raw_text_file_input_type_alias_is_normalized_to_raw_text` | `input_type=raw_text_file` e normalizado para `raw_text` |
| `test_raw_text_file_ignores_legacy_swagger_string_placeholder` | Valor literal `string` vindo de cliente antigo/cacheado e tratado como ausente em campo opcional |
| `test_success_response_contains_five_deliveries_and_auxiliary_fields` | Schema de sucesso contem cinco entregas e campos auxiliares |
| `test_raw_text_source_has_no_transcription_object` | `source.transcription` e `null` quando a entrada e `raw_text` |
| `test_post_processed_transcriptions_audio_contract_success` | Sucesso com audio em modo `contract`, quando viavel |
| `test_audio_flow_saves_internal_raw_transcription_artifacts` | Audio processado pela E03 salva o bruto STT em `.json` e `.txt` |
| `test_audio_flow_completes_generated_transcription_queue_job` | Audio processado pela E03 cria job e conclui a fila quando o pos-processamento funciona |
| `test_processed_markdown_artifact_uses_class_metadata_title` | Markdown processado usa metadados no nome seguro do arquivo e no titulo humano |
| `test_artifact_stem_uses_safe_class_metadata_prefix` | Servico compartilhado cria nome de artefato com prefixo sanitizado e identificador opaco |
| `test_prepared_raw_text_file_name_fills_missing_metadata` | Nome preparado de `raw_text_file` preenche metadados ausentes para evitar nome generico |
| `test_prepared_raw_text_file_keeps_custom_session_metadata` | Nome preparado de `raw_text_file` nao bloqueia `session_label` explicito do usuario e registra diferenca em log saneado |
| `test_prepared_raw_text_file_keeps_custom_title_metadata` | Nome preparado de `raw_text_file` nao bloqueia `class_title` explicito do usuario |
| `test_submit_uses_metadata_json_as_form_source` | Cliente local de submit usa o `.metadata.json` como fonte unica dos campos E03 |
| `test_audio_flow_keeps_queue_job_pending_when_postprocessing_fails` | Falha do motor depois da STT deixa o job pendente para retry |
| `test_pending_generated_transcription_job_can_be_retried_without_reupload` | Job pendente e reprocessado sem reenviar audio |
| `test_contract_mode_does_not_invent_technology_mentions` | Modo `contract` nao inventa tecnologias ausentes do bruto |
| `test_missing_token_returns_401` | Ausencia de token retorna `401` |
| `test_invalid_token_returns_401` | Token invalido retorna `401` |
| `test_local_development_without_api_token_uses_dev_token` | Desenvolvimento local usa `dev-token` quando `MINDVOX_API_TOKEN` esta ausente ou vazio |
| `test_placeholder_api_token_configuration_returns_503` | Placeholder de `MINDVOX_API_TOKEN` e tratado como token ausente |
| `test_malformed_authorization_header_returns_401` | Header `Authorization` malformado retorna `401` |
| `test_dev_token_configuration_returns_503_in_public_deployment` | `dev-token` em deploy publico e tratado como token ausente |
| `test_public_deployment_without_api_token_has_no_default_token` | Deploy publico sem `MINDVOX_API_TOKEN` nao cria token padrao |
| `test_contract_profile_forces_contract_modes_and_disables_llama_autostart` | Perfil `contract` seleciona contrato e nao aciona Llama |
| `test_prod_profile_enables_public_hardening_without_dev_token_default` | Perfil `prod` aplica endurecimento publico e nao usa token didatico |
| `test_public_deployment_requires_https_for_processed_transcriptions` | HTTP sem scheme `https` recebido pela aplicacao retorna `403` em deploy publico |
| `test_public_deployment_accepts_https_for_processed_transcriptions` | Scheme `https` passa pela verificacao de transporte seguro em deploy publico |
| `test_missing_main_input_returns_422` | Entrada principal ausente retorna `422` |
| `test_invalid_input_type_returns_422` | `input_type` invalido retorna `422` |
| `test_audio_input_without_audio_file_returns_422` | `input_type=audio` sem arquivo retorna `422` |
| `test_audio_and_raw_text_conflict_returns_422` | `audio_file` e `raw_text` juntos retornam `422` |
| `test_raw_text_flow_ignores_empty_audio_file_placeholder` | Placeholder vazio de upload nao bloqueia fluxo valido por texto |
| `test_raw_text_and_raw_text_file_conflict_returns_422` | `raw_text` e `raw_text_file` juntos retornam `422` |
| `test_audio_and_raw_text_file_conflict_returns_422` | `audio_file` e `raw_text_file` juntos retornam `422` |
| `test_invalid_raw_text_file_extension_returns_400` | `raw_text_file` fora de `.txt` retorna `400` |
| `test_invalid_processing_profile_returns_422` | Perfil invalido retorna `422` |
| `test_invalid_audio_extension_returns_400` | Extensao de audio invalida retorna `400` |
| `test_incompatible_audio_content_type_returns_400` | Content type de audio incompativel retorna `400` |
| `test_invalid_metadata_returns_422` | Metadados invalidos retornam `422` |
| `test_oversized_optional_metadata_returns_422` | `course`, `discipline` e `class_title` acima dos limites retornam `422` |
| `test_raw_text_over_limit_returns_413` | `raw_text` acima de `150000` caracteres retorna `413` |
| `test_audio_over_upload_limit_returns_413` | Audio acima de `MINDVOX_MAX_UPLOAD_MB` retorna `413` |
| `test_limited_upload_reader_rejects_before_reading_full_oversized_upload` | Upload acima do limite e interrompido sem leitura integral previa |
| `test_unavailable_processing_engine_returns_503` | Motor indisponivel retorna `503` |
| `test_placeholder_provider_key_returns_503` | Chave vazia ou placeholder de provider retorna `503` |
| `test_empty_provider_key_returns_503` | Chave vazia de provider retorna `503` |
| `test_provider_mode_rejects_localhost_endpoint` | Modo `provider` rejeita endpoint local |
| `test_provider_mode_rejects_hostname_resolving_to_private_address` | Modo `provider` rejeita hostname que resolve para IP local/privado |
| `test_provider_mode_rejects_hostname_outside_allowed_list` | Modo `provider` rejeita host fora de `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` |
| `test_provider_mode_accepts_hostname_inside_allowed_list` | Modo `provider` aceita host previsto em `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` |
| `test_local_mode_rejects_public_endpoint` | Modo `local` rejeita endpoint publico |
| `test_local_unavailable_processing_engine_returns_503` | Modo `local` com motor indisponivel retorna `503` |
| `test_contract_mode_does_not_start_llama_server` | Modo `contract` nao aciona autostart do Llama |
| `test_local_autostart_disabled_does_not_start_llama_server` | Autostart desligado nao inicia `llama-server` |
| `test_existing_openai_compatible_server_is_reused` | Servidor local ja ativo e reaproveitado |
| `test_local_autostart_starts_llama_server_until_ready` | Autostart inicia `llama-server` e aguarda prontidao |
| `test_missing_llama_server_path_fails_with_clear_message` | Falta de binario gera erro claro |
| `test_missing_model_path_fails_with_clear_message` | Falta de modelo GGUF gera erro claro |
| `test_startup_timeout_terminates_started_process` | Timeout de startup encerra processo iniciado |
| `test_invalid_llm_output_returns_500` | Saida invalida do LLM retorna `500` controlado |
| `test_long_llm_output_with_insufficient_semantic_coverage_returns_502_with_rejected_artifact` | Saida longa insuficiente e rejeitada apos retry com `502` estruturado e artefato em quarentena |
| `test_long_llm_output_retry_can_recover_semantic_coverage` | Retry por cobertura semantica aceita resposta suficiente e registra nota de controle |
| `test_audio_flow_moves_quality_failure_to_failed_after_max_attempts` | Job de audio com falha de qualidade atinge o limite de tentativas, sai de `pending`, entra em `queue/failed/` e salva artefato rejeitado |
| `test_chunked_semantic_coverage_allows_compact_anchor_preserving_merge` | Validacao chunked aceita merge compacto quando ancoras e temas protegidos foram preservados |
| `test_chunked_semantic_coverage_records_missing_anchors_without_rejecting` | Validacao chunked registra ancoras ausentes em `semantic_anchor_audit`, sem derrubar a resposta inteira, e notas operacionais nao satisfazem cobertura |
| `test_semantic_anchors_do_not_treat_generic_positive_as_company` | Heuristica de ancoras nao trata uso generico de "positivo" como empresa Positivo |
| `test_semantic_anchors_detect_possibly_named_positivo_company` | Heuristica de ancoras continua detectando a empresa Positivo quando ha contexto nominal minimo |
| `test_semantic_anchors_do_not_treat_generic_score_as_viability_case` | Heuristica de ancoras nao trata qualquer "score" isolado como o case de score de viabilidade |
| `test_semantic_coverage_matches_microsservicos_accented_spelling` | Cobertura semantica reconhece grafia acentuada `microsserviços` para a ancora `microservicos` |
| `test_processing_engine_timeout_returns_504` | Timeout do motor retorna `504` |
| `test_get_processed_transcriptions_returns_405` | Metodo HTTP invalido retorna `405` |
| `test_public_deployment_requires_trusted_hosts` | Deploy publico exige `MINDVOX_TRUSTED_HOSTS` |
| `test_public_deployment_disables_docs_and_enforces_trusted_hosts` | Deploy publico desabilita docs por padrao e aplica Trusted Host |
| `test_public_deployment_rejects_wildcard_trusted_hosts` | Deploy publico rejeita `MINDVOX_TRUSTED_HOSTS=*` |
| `test_openapi_documents_e03_contract` | `/openapi.json` informa `Active startup profile` e reflete contrato aprovado |
| `test_response_and_errors_do_not_expose_sensitive_values` | Respostas e erros nao vazam dados sensiveis |
| `test_e03_logs_are_sanitized` | Logs nao registram bruto, prompt integral, resposta integral, token, chave ou path sensivel |
| `test_processed_transcription_auth_failure_logs_status_error_and_duration` | Logs de autenticacao registram status, codigo, fase e duracao sem credenciais |
| `test_controlled_validation_errors_are_logged_without_sensitive_values` | Erros controlados sao logados sem dados sensiveis |
| `test_processing_engine_redacts_sensitive_provider_name` | `processing_engine.name` redige provider com marcador sensivel |
| `test_llm_client_sends_max_tokens_and_limits_response_size` | Cliente LLM envia limite de tokens e limita leitura |
| `test_llm_prompt_uses_e03_manual_without_concise_instruction` | Prompt LLM usa o manual operacional da E03, exige preservacao semantica e nao reintroduz instrucao de concisao/resumo |
| `test_llm_client_disables_thinking_for_local_llama_server` | Cliente LLM desliga thinking ao usar `llama-server` local |
| `test_llm_client_does_not_send_local_template_kwargs_to_provider` | Cliente LLM nao envia parametro local para provider externo |
| `test_llm_client_rejects_excessive_response_body` | Cliente LLM rejeita resposta excessiva |
| `test_benchmark_script_rejects_excessive_response_body` | Benchmark interno rejeita resposta HTTP excessiva |
| `test_zero_llm_max_output_tokens_falls_back_to_default` | Valor zero para limite de saida LLM volta ao padrao |
| `test_zero_llama_server_parallel_falls_back_to_default` | Valor zero para slots do `llama-server` volta ao padrao seguro `1` |
| `test_pre_audit_replaces_known_suspects_and_tracks_unresolved_terms` | Pre-auditoria normaliza formas canonicas conhecidas e preserva suspeitas remanescentes |
| `test_chunk_text_tfidf_creates_ordered_chunks` | Chunking TF-IDF cria chunks ordenados em memoria |
| `test_merge_filters_unresolved_terms_from_structured_deliveries` | Merge/auditoria final remove suspeitas remanescentes dos campos estruturados |
| `test_process_transcription_uses_chunk_pipeline_without_changing_public_raw_text` | E03 usa pipeline longo em modo `contract` sem alterar `raw_text` publico |

## Como executar somente os testes da E03

```bash
uv run python -m unittest discover -s tests/e03_processed_transcriptions -v
```

## Como executar todos os testes

```bash
uv run python -m unittest discover -s tests -v
```

## Perfis locais de inicializacao

Dentro da pasta `src`, os perfis operacionais curtos sao:

```bash
fastapi dev
fastapi dev contract
fastapi run prod
```

No perfil local padrao, o Swagger ainda deve receber `dev-token` em `Authorize`.
Esse perfil ativa o pipeline longo da E03 por padrao para transcricoes longas.
No perfil `contract`, STT e pos-processamento ficam em contrato e o Llama nao sobe.
No perfil `prod`, `dev-token` e bloqueado e o app exige configuracao segura externa.

Para preparar uma transcricao copiada do Vault para upload em `raw_text_file`:

```bash
uv run python scripts/prepare_e03_raw_text_from_vault.py --section 3
```

O `.txt` gerado fica em `inputs/e03_raw_texts/`. O script tambem grava um
`.metadata.json` ao lado, com os campos do formulario E03 inferidos do
frontmatter da inbox.

Para o modo aprendiz/desenvolvedor local, preencher visualmente a tela do Swagger
sem clicar em `Execute`:

```bash
cd /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox && uv run python /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/scripts/fill_e03_swagger_from_vault.py --section 3
```

Para copiar os campos preparados para conferencia/colagem no Swagger ja aberto:

```bash
cd /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox && uv run python /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/scripts/prepare_e03_raw_text_from_vault.py --section 3 --copy-swagger-fields
```

Para submeter sem copiar manualmente os metadados no Swagger:

```bash
cd /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox && uv run python /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/scripts/submit_e03_raw_text.py /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/inputs/e03_raw_texts/2026-05-09-api-rogerio-aula-1-sessao-4.metadata.json
```

Ou em uma unica etapa:

```bash
uv run python scripts/prepare_e03_raw_text_from_vault.py --section 4 --submit
```

## Observacao sobre o motor de LLM

Estes testes automatizados nao substituem a prova humana de qualidade semantica do modelo local ou de provider externo. Eles validam a borda HTTP, o schema, os erros, a documentacao, as regras de seguranca e um freio estrutural minimo contra resumo excessivo em transcricoes longas.

Em modo `provider`, o conteudo de `raw_text` ou a transcricao gerada a partir de audio e enviado ao provider externo configurado. Use modo `local` quando o conteudo nao puder sair da maquina.

Enquanto o endpoint ainda nao estiver implementado, esta pasta deve conter pelo menos o teste documental do plano de testes. Ele nao substitui os testes executaveis do endpoint; apenas impede que a matriz obrigatoria da E03 fique sem verificacao automatizada.

O teste funcional real da E03 deve ser executado por humano antes do commit de fechamento, usando entrada representativa e registrando modo (`local` ou `provider`), modelo/provider, status HTTP, tempo aproximado e avaliacao humana da coerencia das cinco entregas.

## Relacao com a Spec

Estes testes verificam a parte executavel da Spec:

```text
docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md
```

Eles nao substituem a Spec. A Spec define o contrato; estes testes confirmam que o codigo continua obedecendo a esse contrato.
