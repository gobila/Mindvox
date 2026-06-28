# Plano P02: Implementacao do Endpoint E02 Transcriptions

## 1. Identificacao

- `ID`: `P02`
- `Tipo`: `Plano de Implementacao`
- `Status`: `aberto`
- `Spec alvo`: `E02_ENDPOINT_TRANSCRIPTIONS.md`
- `Endpoint alvo`: `POST /transcriptions/v1.0.0`
- `Data`: `2026-06-08`

---

## 2. Objetivo

Implementar o endpoint de transcricao de audio do Mindvox:

```text
POST /transcriptions/v1.0.0
```

O endpoint deve receber um arquivo de audio ja gravado, autenticar a requisicao, validar arquivo e metadados, encaminhar o audio para uma camada de servico de transcricao e devolver uma resposta estruturada.

Este endpoint inaugura o primeiro servico de negocio do Mindvox. Diferente de `GET /health`, que apenas verifica se a API esta viva, a E02 executa uma funcao essencial do produto: transformar fala gravada em texto.

---

## 3. Observacao de Governanca

Este plano deve ser usado para auditar e alinhar a implementacao da E02 antes do commit de fechamento.

Regra de conferencia:

- se a implementacao atual cumprir este plano e a Spec E02, marcar as tarefas correspondentes como concluidas;
- se faltar algo previsto aqui, implementar antes do commit;
- se houver excesso fora do escopo, remover ou justificar;
- se o plano estiver incompleto em relacao a Spec E02, emendar este plano antes de fechar;
- se a implementacao divergir corretamente da previsao, registrar a justificativa no plano, nas tarefas ou na Spec.

---

## 4. Estado Atual Esperado Antes da E02

Arquivos relevantes ja existentes apos a E01:

- `src/main.py`
- `src/routers/health.py`
- `tests/e01_health/test_health.py`
- `tests/e01_health/README.md`
- `docs/sdd/specs/E02_ENDPOINT_TRANSCRIPTIONS.md`

Situacao esperada:

- a API ja deve possuir `GET /health` funcionando;
- a suite de testes da E01 deve passar;
- a Spec E02 deve estar fechada;
- rascunhos de transcricao nao aprovados nao devem ser registrados no app;
- nenhum token real deve estar versionado;
- `.env` deve continuar fora do Git.

---

## 5. Decisoes de Implementacao

Implementacao proposta:

- criar um router especifico para transcricoes;
- registrar esse router em `src/main.py`;
- exigir autenticacao por `Authorization: Bearer <token>`;
- ler o token de configuracao externa por `MINDVOX_API_TOKEN`;
- usar `dev-token` automaticamente em desenvolvimento local quando `MINDVOX_API_TOKEN` estiver ausente ou vazio;
- tratar placeholder de exemplo em `MINDVOX_API_TOKEN` como token ausente;
- tratar `dev-token` como token ausente quando `MINDVOX_PUBLIC_DEPLOYMENT=true`;
- exibir `Active startup profile` no Swagger/OpenAPI global, indicando `dev`, `contract` ou `prod`;
- rejeitar `MINDVOX_TRUSTED_HOSTS=*` quando `MINDVOX_PUBLIC_DEPLOYMENT=true`;
- exigir transporte seguro para `POST /transcriptions/v1.0.0` em deploy publico, aceitando apenas requisicao que chegue a aplicacao com scheme `https`;
- se TLS terminar em proxy, o proxy e o servidor ASGI devem ser configurados de modo confiavel para repassar o scheme `https`; a aplicacao nao deve confiar em header `X-Forwarded-Proto` enviado livremente pelo cliente;
- ler o limite de upload por `MINDVOX_MAX_UPLOAD_MB`;
- usar como backend STT preferencial em macOS Apple Silicon `mlx-whisper + mlx-community/whisper-large-v3-turbo-fp16`, conforme [Spec E02, secao 8, Motor STT](../specs/E02_ENDPOINT_TRANSCRIPTIONS.md#8-motor-stt);
- selecionar backend STT por `MINDVOX_TRANSCRIPTION_BACKEND=auto|mlx-whisper|openai-whisper`;
- em `auto`, usar `mlx-whisper` em macOS Apple Silicon e `openai-whisper` como backend local cross-platform em Windows/Linux;
- tratar `openai-whisper` como STT local via PyTorch, nao como provider remoto e nao como chamada a API da OpenAI;
- documentar FFmpeg como dependencia de sistema para ambientes que usam `openai-whisper`;
- admitir `mlx-whisper + whisper-small` apenas como fallback de desenvolvimento ou smoke test, sem apresenta-lo como motor final de qualidade;
- aceitar arquivos `.wav` e `.m4a`;
- validar nome de arquivo nao vazio, extensao, `content_type`, tamanho e assinatura minima do container de audio;
- validar metadados opcionais, especialmente `class_date`, `session_label`, `language` e tamanho de `course`, `discipline` e `class_title`;
- criar schemas Pydantic para a resposta de sucesso;
- separar a chamada ao motor de transcricao em uma camada de servico;
- manter o router desacoplado do motor concreto de STT;
- prever modo de contrato para testes automatizados e demonstracao controlada;
- nao apresentar modo de contrato como transcricao real;
- retornar erro controlado quando o motor real de STT estiver indisponivel;
- registrar logs operacionais sem audio bruto, transcricao integral, token, `.env` ou paths sensiveis.

### 5.1 Clausula de Preservacao do Motor STT

A escolha do motor STT primario da E02 nao deve ser alterada por conveniencia local, cache disponivel, funcionamento atual do N02 do Atrium ou facilidade momentanea de instalacao.

A escolha vigente e:

```text
mlx-whisper + mlx-community/whisper-large-v3-turbo-fp16
```

Esta escolha vem da [Spec E02, secao 8, Motor STT](../specs/E02_ENDPOINT_TRANSCRIPTIONS.md#8-motor-stt), que registra expressamente que:

- o Mindvox precisa de transcricao batch confiavel de arquivos ja gravados;
- o hardware de referencia suporta o modelo;
- `mlx-whisper` e coerente com a referencia tecnica do N02 do Atrium para STT local;
- `whisper-large-v3-turbo-fp16` favorece qualidade e desempenho em Apple Silicon;
- o fallback `mlx-whisper + whisper-small` pode validar instalacao, contrato ou testes rapidos, mas nao deve ser apresentado como motor final de qualidade da E02.

Essa decisao tambem preserva o objetivo real do Mindvox descrito no [Contrato de Mentoria, secao 2](../../mindvox_mentoring_agreement.md#2-objetivo-real-do-mindvox): transformar aulas longas em memoria consultavel a partir de transcricoes confiaveis. Como a E03 devera processar texto transcrito, conforme o [relatorio orientador da E03](../reports/RELATORIO_DIRETRIZES_E03_SERVICO_IA_LLM.md#6-diretriz-recomendada-para-a-e03), a qualidade da STT da E02 e insumo estrutural para a qualidade do processamento posterior.

Consequencia obrigatoria:

- aproveitar codigo, cache, padroes ou experiencia do N02 e permitido quando nao contrariar a E02;
- substituir `mlx-community/whisper-large-v3-turbo-fp16` por `mlx-community/whisper-large-v3-turbo`, `whisper-small` ou qualquer outro modelo exige emenda explicita da Spec E02 antes da alteracao no codigo, plano ou tarefas;
- a disponibilidade local de um modelo no N02 do Atrium nao autoriza, por si so, alterar o motor final de qualidade do Mindvox.

Detalhe tecnico de implementacao permitido:

- se o repositorio Hugging Face do modelo final entregar pesos como `model.safetensors`, a camada de servico pode preparar um layout local compativel com `mlx-whisper`, expondo esse mesmo arquivo como `weights.safetensors`;
- essa adaptacao nao altera o modelo escolhido, nao troca o motor final de qualidade e nao autoriza fallback para modelo diferente;
- se o contrato HTTP receber idioma regional como `pt-BR`, a camada de servico pode enviar ao backend Whisper selecionado a forma base esperada, como `pt`, preservando `pt-BR` na resposta publica do Mindvox.

Emenda de portabilidade em `2026-06-25`:

- a preservacao do motor final de qualidade continua valendo para o backend MLX em macOS Apple Silicon;
- a portabilidade multiplataforma nao substitui a prova real historica com `mlx-whisper`;
- `MINDVOX_TRANSCRIPTION_FALLBACK_MODEL=turbo` define o modelo inicial do backend `openai-whisper`;
- FFmpeg deve estar disponivel no `PATH` quando o backend real depender de `openai-whisper`;
- o contrato HTTP e a composicao com a E03 permanecem inalterados.

---

## 6. Arquivos Planejados

Arquivos de codigo:

- `src/main.py`
- `src/settings.py`
- `src/routers/transcriptions.py`
- `src/schemas/__init__.py`
- `src/schemas/transcriptions.py`
- `src/services/__init__.py`
- `src/services/transcription_service.py`

Arquivos de teste:

- `tests/e02_transcriptions/__init__.py`
- `tests/e02_transcriptions/README.md`
- `tests/e02_transcriptions/test_transcriptions.py`

Arquivos de documentacao e configuracao:

- `.env.example`
- `.gitignore`
- `README.md`
- `docs/sdd/specs/E02_ENDPOINT_TRANSCRIPTIONS.md`

Regra:

- qualquer arquivo adicional deve ser justificado antes do commit;
- arquivos gerados, caches, `.env`, audio real e tokens reais nao devem entrar no Git.

---

## 7. Configuracao Planejada

Variaveis esperadas:

| Variavel | Finalidade | Regra |
| --- | --- | --- |
| `MINDVOX_API_TOKEN` | Token local do MVP para autenticar o endpoint | Ausente ou vazio usa `dev-token` em desenvolvimento local; em producao publica exige token forte externo |
| `MINDVOX_MAX_UPLOAD_MB` | Limite maximo de upload em MB | Deve ter padrao seguro para desenvolvimento local, inicialmente `500` |
| `MINDVOX_TRANSCRIPTION_MODE` | Define modo real ou modo de contrato | `contract` somente para testes automatizados e demonstracao controlada |
| `MINDVOX_TRANSCRIPTION_BACKEND` | Define backend STT real | `auto` escolhe MLX em macOS Apple Silicon e OpenAI Whisper local em Windows/Linux |
| `MINDVOX_TRANSCRIPTION_MODEL` | Define o modelo usado pelo backend MLX | Padrao esperado: `mlx-community/whisper-large-v3-turbo-fp16`, conforme [Spec E02 §8](../specs/E02_ENDPOINT_TRANSCRIPTIONS.md#8-motor-stt) |
| `MINDVOX_TRANSCRIPTION_FALLBACK_MODEL` | Define modelo local cross-platform | Padrao inicial: `turbo` para `openai-whisper` |
| `MINDVOX_TRANSCRIPTION_OUTPUT_DIR` | Pasta local do JSON tecnico da transcricao bruta | Padrao `outputs/transcriptions`; path relativo deve ser resolvido a partir da raiz do projeto |
| `MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR` | Pasta local do TXT humano da transcricao bruta | Padrao `outputs/human/transcriptions`; propria do modo `dev`/instalacao local |

Regras:

- valores reais de token devem ficar fora do codigo e fora do Git;
- `.env.example` deve documentar nomes e exemplos ficticios;
- `.env` real deve permanecer ignorado;
- mensagens de erro e logs nao devem revelar valores dessas variaveis.

---

## 8. Contrato HTTP Planejado

Metodo:

```text
POST
```

Rota:

```text
/transcriptions/v1.0.0
```

Interpretacao:

- `transcriptions` indica o recurso produzido pela operacao;
- `v1.0.0` segue o padrao ja usado na E01 para indicar a primeira versao estavel do contrato.

Entrada:

```text
multipart/form-data
```

Campos:

- `audio_file`: obrigatorio;
- `course`: opcional;
- `discipline`: opcional;
- `class_date`: opcional, formato `YYYY-MM-DD`;
- `class_title`: opcional;
- `session_label`: opcional;

Limites de metadados textuais:

- `course`: ate `160` caracteres;
- `discipline`: ate `120` caracteres;
- `class_title`: ate `200` caracteres.
- `language`: opcional, padrao `pt-BR`.

Cada campo do formulario deve ser declarado com descricao didatica propria em `File(description=...)` ou `Form(description=...)`. Essas descricoes devem aparecer no Swagger/OpenAPI em ingles e incluir exemplo curto, para que o usuario consiga compreender o que preencher sem depender de explicacao externa.

Header obrigatorio:

```text
Authorization: Bearer <token>
```

Regras de autenticacao:

- requisicao sem header `Authorization` deve retornar `401 Unauthorized`;
- requisicao com token invalido deve retornar `401 Unauthorized`;
- requisicao com formato incorreto, diferente de `Bearer <token>`, deve retornar `401 Unauthorized`;
- mensagens de erro de autenticacao nao devem revelar token recebido, token esperado ou detalhes internos da configuracao.

---

## 9. Resposta Planejada

Resposta de sucesso:

```text
200 OK
```

Campos obrigatorios na resposta:

- `transcription_id`;
- `text`;
- `language`;
- `duration_seconds`;
- `segments`;
- `metadata`;
- `engine`.

Regras:

- `segments` deve existir sempre, mesmo quando vazio;
- `speaker_label` pode permanecer `null` no MVP;
- `engine` nao deve revelar paths locais, tokens, `.env` ou dados sensiveis;
- `transcription_id` deve ser opaco para o cliente e usar o prefixo controlado `tr_`, sem incorporar nome de arquivo, token, path local ou dado pessoal.

Detalhamento de `engine`:

- `engine.name`: nome controlado do motor usado, como `mlx-whisper`, `openai-whisper` ou marcador explicito de modo de contrato;
- `engine.model`: modelo configurado para a transcricao, sem path local ou detalhe sensivel;
- `engine.version`: versao conhecida da biblioteca/modelo quando disponivel; quando indisponivel, usar valor controlado como `unknown`.

---

## 10. Erros Planejados

Erros que devem ser tratados:

| Situacao | Status esperado |
| --- | --- |
| Arquivo ausente | `422 Unprocessable Entity` |
| Nome de arquivo vazio | `422 Unprocessable Entity` |
| Tipo de arquivo invalido | `400 Bad Request` |
| Audio com extensao aceita mas conteudo invalido | `422 Unprocessable Entity` |
| Arquivo maior que o limite configurado | `413 Payload Too Large` |
| Metadados invalidos em `class_date`, `session_label`, `language`, `course`, `discipline` ou `class_title` | `422 Unprocessable Entity` |
| Token ausente | `401 Unauthorized` |
| Token invalido | `401 Unauthorized` |
| Header `Authorization` em formato incorreto | `401 Unauthorized` |
| Transporte inseguro em deploy publico | `403 Forbidden` |
| Motor de transcricao indisponivel | `503 Service Unavailable` |
| Metodo HTTP errado | `405 Method Not Allowed` |
| Erro interno inesperado | `500 Internal Server Error` |

Erros internos inesperados nao devem expor stack trace, paths locais, token, bytes do audio ou configuracoes internas.

---

## 10.1 Logs Planejados

Logs devem registrar apenas dados operacionais necessarios.

Eventos permitidos:

- inicio da requisicao;
- tamanho do arquivo;
- `content_type`;
- resultado da autenticacao, sem registrar token;
- duracao do processamento, quando disponivel;
- sucesso ou falha;
- codigo de erro controlado.

Dados proibidos:

- audio bruto;
- transcricao integral;
- header `Authorization`;
- chaves, tokens ou valores de `.env`;
- paths locais sensiveis;
- dados pessoais desnecessarios.

Decisao de persistencia:

- persistencia propria de logs fica adiada no MVP;
- o plano exige logger operacional proprio apenas para eventos controlados da E02;
- logs persistentes, agregacao, auditoria externa e observabilidade cloud devem ser tratados em Spec futura, se necessarios.

Decisao de artefatos locais:

- cada transcricao bruta produzida pelo STT deve gerar automaticamente `[metadados-seguros_]<transcription_id>.json` e `[metadados-seguros_]<transcription_id>.txt`;
- por padrao o JSON tecnico fica em `outputs/transcriptions/` e o TXT humano fica em `outputs/human/transcriptions/`, ambos ignorados pelo Git;
- o TXT humano deve ser paragrafado quando houver segmentos do STT, preservando apenas o texto bruto audivel e mantendo timestamps no JSON tecnico;
- a escrita deve terminar com `transcription_id` opaco e pode usar prefixo humano sanitizado derivado de `class_date`, `class_title`, `session_label` ou metadado equivalente, para facilitar localizacao local da aula;
- a escrita nao deve usar nome original de arquivo, token, path local, dado pessoal sensivel ou metadado nao sanitizado;
- o TXT humano deve conter somente o texto bruto transcrito, sem cabecalho artificial;
- a API nao deve retornar path absoluto local.

Verificacao obrigatoria:

- testes automatizados ou revisao documentada devem confirmar que logs da E02 nao registram audio bruto, transcricao integral, `Authorization`, tokens, `.env`, paths sensiveis ou dados pessoais desnecessarios.

---

## 10.2 Documentacao FastAPI Planejada

A documentacao automatica deve permitir conferir:

- `summary` definido como `Transcribe audio file`;
- `description` definida como `Receives a recorded audio file and returns a text transcription with optional class metadata.`;
- rota `POST /transcriptions/v1.0.0`;
- entrada `multipart/form-data`;
- campo obrigatorio `audio_file`;
- metadados opcionais do formulario;
- descricoes didaticas com exemplos curtos para `audio_file`, `course`, `discipline`, `class_date`, `class_title`, `session_label` e `language`;
- formatos aceitos `.wav` e `.m4a`;
- esquema de autenticacao por Bearer token;
- resposta de sucesso;
- respostas principais de erro: `400`, `401`, `413`, `422`, `500` e `503`;
- indicacao de que o audio deve ser arquivo ja gravado;
- indicacao de que streaming, TTS e speech-to-speech estao fora deste endpoint.

---

## 11. Passos de Implementacao

1. Criar mecanismo de configuracao externa.
2. Definir variaveis esperadas em `.env.example`.
3. Ajustar `.gitignore` para permitir `.env.example` e manter `.env` ignorado.
4. Criar schemas Pydantic da resposta de transcricao.
5. Criar camada de servico de transcricao.
6. Criar modo de contrato para testes e demonstracao controlada.
7. Criar modo real substituivel para execucao com backend STT configuravel, preservando `mlx-whisper + mlx-community/whisper-large-v3-turbo-fp16` como backend preferencial em macOS Apple Silicon.
8. Criar router `POST /transcriptions/v1.0.0`.
9. Implementar autenticacao por Bearer token.
10. Implementar rejeicao de token ausente, token invalido e header `Authorization` em formato incorreto.
10.1. Implementar bloqueio de `dev-token` em `MINDVOX_PUBLIC_DEPLOYMENT=true`.
10.2. Implementar rejeicao de wildcard em `MINDVOX_TRUSTED_HOSTS` quando `MINDVOX_PUBLIC_DEPLOYMENT=true`.
10.3. Implementar exigencia de transporte seguro para E02 em deploy publico, retornando `403 Forbidden` quando a aplicacao nao receber scheme `https`.
11. Implementar validacoes de arquivo, incluindo nome nao vazio, extensao, `content_type`, tamanho e assinatura minima de container.
12. Implementar validacoes de metadados.
13. Implementar tratamento de erros controlados, incluindo `500 Internal Server Error` sem vazamento sensivel.
14. Registrar logs operacionais sem dados sensiveis.
15. Decidir explicitamente persistencia de logs ou adiamento.
16. Registrar router em `src/main.py`.
17. Criar pasta propria de testes `tests/e02_transcriptions/`.
18. Criar README da pasta de testes.
19. Criar teste de sucesso cobrindo schema, `transcription_id` com prefixo `tr_`, `language` padrao `pt-BR` quando ausente e `engine.version` conhecido ou `unknown`.
20. Criar testes de autenticacao, incluindo token ausente, token invalido e header malformado.
21. Criar testes de validacao de arquivo, incluindo nome de arquivo vazio com `422 Unprocessable Entity`.
22. Criar testes de validacao de metadados, cobrindo `class_date`, `session_label`, `language`, `course`, `discipline` e `class_title` invalidos com `422 Unprocessable Entity`.
23. Criar teste de falha do motor de transcricao retornando `503 Service Unavailable`.
24. Criar teste de metodo invalido.
25. Criar teste de OpenAPI, cobrindo rota, formulario, autenticacao, resposta de sucesso, erros `400`, `401`, `403`, `413`, `422`, `500` e `503`, audio gravado e exclusao de streaming, TTS e speech-to-speech.
26. Criar teste de nao vazamento sensivel em resposta e mensagens de erro.
27. Criar teste automatizado ou revisao documentada de nao vazamento sensivel em logs.
28. Rodar verificacao de sintaxe.
29. Rodar testes da E02.
30. Rodar suite geral.
31. Atualizar a checklist aplicavel da Spec E02.
32. Atualizar material didatico externo ao repo, quando aplicavel.
33. Revisar `git status`.
34. Revisar `git diff`.
35. Confirmar que os arquivos alterados pertencem ao escopo da E02 ou estao justificados.
36. Confirmar que nenhum segredo, token real, `.env`, path sensivel ou dado privado aparece no diff.
37. Confirmar que nenhum cache, `__pycache__`, temporario ou artefato gerado indevido aparece no diff.
38. Confirmar que o README da pasta de testes esta atualizado.
39. Confirmar que a mensagem de commit identifica a E02.
40. Preparar commit de fechamento.
41. Realizar o commit de fechamento antes de iniciar a E03.

---

## 12. Verificacoes

Verificacao de sintaxe:

```bash
uv run python -m py_compile src/main.py src/settings.py src/routers/health.py src/routers/transcriptions.py src/schemas/transcriptions.py src/services/transcription_service.py tests/e01_health/test_health.py tests/e02_transcriptions/test_transcriptions.py
```

Testes automatizados da E02:

```bash
uv run python -m unittest discover -s tests/e02_transcriptions -v
```

Testes automatizados gerais:

```bash
uv run python -m unittest discover -s tests -v
```

Servidor local em modo de contrato:

```bash
uv run fastapi dev src/contract
```

Documentacao:

```text
http://127.0.0.1:8000/docs
```

---

## 13. Demonstracao Manual Prevista

Chamada valida em modo de contrato:

```bash
curl -X POST "http://127.0.0.1:8000/transcriptions/v1.0.0" \
  -H "Authorization: Bearer dev-token" \
  -F "audio_file=@/caminho/para/audio.wav;type=audio/wav" \
  -F "discipline=API" \
  -F "session_label=s1" \
  -F "language=pt-BR"
```

Resultado esperado:

```text
200 OK
```

Chamada sem token:

```bash
curl -X POST "http://127.0.0.1:8000/transcriptions/v1.0.0" \
  -F "audio_file=@/caminho/para/audio.wav;type=audio/wav"
```

Resultado esperado:

```text
401 Unauthorized
```

---

## 14. Fora do Escopo Deste Plano

Este plano nao implementa:

- captura de audio ao vivo;
- streaming;
- TTS;
- speech-to-speech;
- diarizacao final;
- identificacao robusta de falantes;
- correcao contextual por LLM;
- analise afetiva da voz;
- processamento semantico da transcricao;
- persistencia definitiva em banco ou memoria;
- busca semantica;
- busca relacional;
- interface grafica;
- upload indireto para storage;
- fila assincrona;
- estrategia final de deploy em cloud.

---

## 15. Riscos e Cuidados

Riscos principais:

- confundir modo de contrato com transcricao real;
- vazar audio, transcricao, token ou paths locais em logs ou respostas;
- aceitar arquivo apenas pela extensao sem validacao minima de conteudo;
- misturar logica de STT diretamente no router;
- implementar escopo futuro dentro da E02;
- deixar `.env.example` ignorado pelo Git;
- commitar `.env`, caches ou arquivos temporarios.

Cuidados obrigatorios:

- manter audio e transcricao como dados sensiveis;
- usar exemplos ficticios;
- manter token fora do codigo-fonte;
- manter o motor real substituivel;
- garantir testes perenes antes de iniciar a E03.

---

## 16. Criterios de Pronto

Este plano podera ser fechado quando:

- o endpoint `POST /transcriptions/v1.0.0` existir;
- o endpoint exigir Bearer token;
- o endpoint rejeitar token ausente, token invalido e header `Authorization` em formato incorreto;
- o endpoint usar `dev-token` quando `MINDVOX_API_TOKEN` estiver ausente ou vazio em desenvolvimento local;
- o endpoint retornar `503 Service Unavailable` quando `MINDVOX_API_TOKEN` estiver com placeholder de exemplo;
- o endpoint aceitar arquivo valido em modo de contrato;
- o endpoint rejeitar arquivo ausente;
- o endpoint rejeitar arquivo sem nome;
- o endpoint rejeitar tipo invalido;
- o endpoint rejeitar audio corrompido;
- o endpoint rejeitar arquivo acima do limite;
- o endpoint rejeitar metadados invalidos de `class_date`, `session_label`, `language`, `course`, `discipline` e `class_title`;
- o endpoint retornar `503 Service Unavailable` quando o motor de transcricao estiver indisponivel;
- o endpoint tratar erro interno inesperado como `500`, sem vazamento sensivel;
- o endpoint retornar resposta estruturada conforme a Spec E02;
- o `transcription_id` retornar identificador opaco com prefixo `tr_`, sem dado sensivel embutido;
- os artefatos locais usarem prefixo humano sanitizado quando houver metadados de aula e manterem o `transcription_id` opaco como sufixo obrigatorio;
- o `language` retornar `pt-BR` como padrao quando o formulario nao informar idioma;
- o `engine.version` retornar versao conhecida ou valor controlado como `unknown`, sem expor path local;
- `dev-token` ser recusado em deploy publico;
- `MINDVOX_TRUSTED_HOSTS=*` ser recusado em deploy publico;
- `POST /transcriptions/v1.0.0` exigir transporte seguro em deploy publico, retornando `403` quando a aplicacao nao receber scheme `https`;
- o OpenAPI documentar rota, formulario, arquivo obrigatorio, metadados opcionais, descricoes didaticas dos campos com exemplos curtos, formatos aceitos, Bearer token, resposta de sucesso, erros `400`, `401`, `403`, `413`, `422`, `500` e `503`, audio gravado e exclusao de streaming, TTS e speech-to-speech;
- o plano de logs estiver cumprido ou justificado;
- logs tiverem sido verificados contra vazamento de audio bruto, transcricao integral, `Authorization`, token, `.env`, path sensivel e dados pessoais desnecessarios;
- houver testes automatizados da E02;
- houver README na pasta de testes da E02;
- a suite da E02 passar;
- a suite geral passar;
- a prova real humana do endpoint `POST /transcriptions/v1.0.0` em modo `real` passar e ficar registrada;
- a checklist da Spec E02 estiver coerente;
- o material didatico externo ao repo estiver atualizado, quando aplicavel;
- `git status` e `git diff` tiverem sido revisados;
- os arquivos alterados pertencerem ao escopo da E02 ou estiverem justificados;
- nenhum segredo, token real, `.env`, path sensivel, cache, `__pycache__`, temporario ou artefato gerado indevido aparecer no diff;
- o README da pasta de testes estiver atualizado;
- a mensagem de commit identificar a E02;
- o commit de fechamento tiver sido realizado antes de iniciar a E03;
- Adalberto conseguir explicar finalidade, entrada, autenticacao, validacao, processamento, resposta, erros, logs, testes e limites da E02.

---

## 17. Registro de Fechamento

Status atual: `pronto-para-commit-manual`.

Este plano devera ser fechado apenas apos conferencia contra:

- Spec E02;
- tarefas T02;
- implementacao real;
- testes automatizados;
- checklist aplicavel da E02;
- auditoria final antes do commit.

Atualizacao em `2026-06-09`:

- incluida exigencia de descricoes didaticas em ingles, com exemplos curtos, para cada campo do formulario no Swagger/OpenAPI;
- a exigencia responde ao criterio didatico de que a propria documentacao interativa da API deve orientar o usuario sobre o que preencher;
- o teste de OpenAPI deve validar essas descricoes para evitar regressao futura.

Atualizacao de prova real humana em `2026-06-09`:

- `POST /transcriptions/v1.0.0` foi executado manualmente em modo `real`;
- retorno HTTP observado: `200 OK`;
- `transcription_id`: `tr_20260609T154710Z_35969e23`;
- audio real de aula com `duration_seconds` igual a `3093.6`;
- texto bruto retornado nao vazio, extenso e coerente com o audio;
- resposta retornou `2067` segmentos temporais;
- `engine.name`: `mlx-whisper`;
- `engine.model`: `mlx-community/whisper-large-v3-turbo-fp16`;
- prova real humana da E02 aprovada para fechamento funcional;
- commit de fechamento ainda deve ser realizado manualmente antes de iniciar a E03.
