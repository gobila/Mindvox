# Tarefas T02: Implementacao do Endpoint E02 Transcriptions

## 1. Identificacao

- `ID`: `T02`
- `Tipo`: `Tarefas de Implementacao`
- `Status`: `emenda-multiplataforma-pronta-para-auditoria`
- `Spec alvo`: `E02_ENDPOINT_TRANSCRIPTIONS.md`
- `Plano alvo`: `P02_IMPLEMENTACAO_E02_TRANSCRIPTIONS.md`
- `Endpoint alvo`: `POST /transcriptions/v1.0.0`
- `Data`: `2026-06-08`
- `Emenda`: `2026-06-25`, portabilidade STT por backend local cross-platform

---

## 2. Objetivo

Executar a implementacao do endpoint E02 Transcriptions conforme a Spec E02 fechada e o Plano P02 aberto para auditoria.

O endpoint deve receber audio ja gravado, autenticar a requisicao, validar arquivo e metadados, encaminhar o audio para camada de servico de transcricao e devolver resposta estruturada sem vazar dados sensiveis.

---

## 3. Regra de Execucao

Estas tarefas devem ser usadas como lista de conferencia antes do commit de fechamento da E02.

Interpretacao:

- enquanto a auditoria final nao for feita, as tarefas permanecem `pendente`;
- apos comparar Spec, Plano, tarefas, implementacao e testes, cada item pode ser marcado como `concluida`, `ajustar` ou `N/A`;
- divergencias justificadas devem ser registradas nesta nota, no plano ou na Spec antes do commit;
- nenhuma tarefa da E03 deve iniciar antes do fechamento da E02;
- a E02 nao pode ser fechada somente com testes automatizados em modo `contract`;
- a E02 so pode ser fechada depois de prova real humana, com audio real, demonstrando que o endpoint faz corretamente aquilo que seu contrato declara.

### 3.1 Regra de Prova Real Para Specs Tipo E

Toda Spec tipo `E` do Mindvox deve exigir prova real humana antes de ser considerada fechada.

Para fins desta T02, `prova real humana` significa:

- execucao manual do endpoint por uma pessoa;
- uso de entrada real ou representativa do dominio do endpoint;
- verificacao de que a resposta corresponde ao comportamento prometido no contrato;
- verificacao de erros relevantes quando aplicavel;
- registro do resultado no documento de tarefas, plano, Spec ou relatorio aplicavel.

Consequencia obrigatoria:

- enquanto um endpoint nao provar na vida real que faz sem erros aquilo que seu contrato diz que faz, ele nao esta concluido;
- enquanto o endpoint nao estiver concluido, nao pode haver mudanca de desenvolvimento para outro endpoint;
- Specs tipo `E` futuras devem incluir um item explicito de prova real humana no checklist aplicavel do endpoint;
- testes automatizados continuam obrigatorios, mas nao substituem a prova real humana quando o endpoint envolver IA, motor externo, modelo local, provider, persistencia, busca ou qualquer efeito funcional que precise ser demonstrado fora do modo de contrato.

---

## 4. Tarefas

| ID | Status | Tarefa | Criterio de conclusao |
| --- | --- | --- | --- |
| T02.01 | concluida | Criar mecanismo de configuracao externa | Configuracoes da E02 ficam concentradas em modulo proprio ou mecanismo equivalente |
| T02.02 | concluida | Definir `MINDVOX_API_TOKEN` | Token do MVP e lido de configuracao externa e nao fica no codigo |
| T02.02.1 | concluida | Tratar placeholder de `MINDVOX_API_TOKEN` como ausente | `replace-with-local-token` ou `<set-real-token-only-in-local-env>` nao autentica a E02 e gera erro controlado |
| T02.02.2 | concluida | Usar token local automatico | Em desenvolvimento local, `MINDVOX_API_TOKEN` ausente ou vazio usa `dev-token` |
| T02.03 | concluida | Definir `MINDVOX_MAX_UPLOAD_MB` | Limite de upload e configuravel, com padrao inicial coerente com `500 MB` |
| T02.04 | concluida | Definir `MINDVOX_TRANSCRIPTION_MODE` | Modo de contrato existe apenas para testes automatizados e demonstracao controlada |
| T02.05 | concluida | Definir `MINDVOX_TRANSCRIPTION_MODEL` | Modelo padrao previsto e `mlx-community/whisper-large-v3-turbo-fp16`, conforme [Spec E02 §8](../specs/E02_ENDPOINT_TRANSCRIPTIONS.md#8-motor-stt) e [Plano P02 §5.1](../plans/P02_IMPLEMENTACAO_E02_TRANSCRIPTIONS.md#51-clausula-de-preservacao-do-motor-stt) |
| T02.06 | concluida | Criar `.env.example` | Arquivo documenta variaveis com valores ficticios, sem segredo real |
| T02.07 | concluida | Ajustar `.gitignore` para `.env.example` | `.env` continua ignorado e `.env.example` pode ser versionado |
| T02.08 | concluida | Criar schemas Pydantic da resposta | Resposta possui `transcription_id`, `text`, `language`, `duration_seconds`, `segments`, `metadata` e `engine` |
| T02.09 | concluida | Detalhar `segments` | `segments` existe sempre como lista; `speaker_label` pode ser `null` |
| T02.10 | concluida | Detalhar `engine` | `engine.name`, `engine.model` e `engine.version` nao expõem paths, tokens ou detalhes sensiveis; `engine.version` usa versao conhecida ou `unknown` |
| T02.11 | concluida | Criar camada de servico de transcricao | Router nao contem toda a logica de STT |
| T02.12 | concluida | Prever motor STT primario | Motor real previsto e `mlx-whisper + mlx-community/whisper-large-v3-turbo-fp16`; a escolha privilegia qualidade de STT para aulas longas e processamento posterior, conforme [Spec E02 §8](../specs/E02_ENDPOINT_TRANSCRIPTIONS.md#8-motor-stt) |
| T02.13 | concluida | Prever fallback de desenvolvimento | `mlx-whisper + whisper-small` e tratado apenas como fallback/smoke test; nao pode ser apresentado como motor final de qualidade da E02, conforme [Spec E02 §8](../specs/E02_ENDPOINT_TRANSCRIPTIONS.md#8-motor-stt) |
| T02.13.1 | concluida | Preservar decisao do motor final de qualidade da E02 | Nao substituir `mlx-community/whisper-large-v3-turbo-fp16` por modelo disponivel no N02 do Atrium, cache local ou fallback sem emenda previa da Spec E02, conforme [Plano P02 §5.1](../plans/P02_IMPLEMENTACAO_E02_TRANSCRIPTIONS.md#51-clausula-de-preservacao-do-motor-stt) |
| T02.13.2 | concluida | Adaptar layout local do modelo `-fp16` para `mlx-whisper` | Quando o modelo final entregar `model.safetensors`, a camada de servico prepara layout compativel expondo o mesmo arquivo como `weights.safetensors`, sem trocar o modelo definido pela E02 |
| T02.13.3 | concluida | Adaptar idioma regional para o motor real | `pt-BR` permanece no contrato publico da API, mas a camada de servico envia `pt` ao `mlx-whisper`, que espera idioma base |
| T02.13.4 | concluida | Adicionar selecao explicita de backend STT | `MINDVOX_TRANSCRIPTION_BACKEND=auto|mlx-whisper|openai-whisper` define o backend real sem alterar o contrato HTTP da E02 |
| T02.13.5 | concluida | Manter `mlx-whisper` como backend preferencial em macOS Apple Silicon | Em `auto`, macOS Apple Silicon continua usando `mlx-whisper` com `MINDVOX_TRANSCRIPTION_MODEL` |
| T02.13.6 | concluida | Adicionar backend local cross-platform | Em `auto`, Windows/Linux usam `openai-whisper` com `MINDVOX_TRANSCRIPTION_FALLBACK_MODEL`; esse backend roda localmente por PyTorch e nao chama API remota da OpenAI |
| T02.13.7 | concluida | Separar STT local de provider LLM da E03 | Documentacao deixa claro que `MINDVOX_POSTPROCESSING_MODE=provider` pertence ao pos-processamento textual por LLM OpenAI-compatible, nao a transcricao de audio |
| T02.13.8 | concluida | Documentar dependencia de sistema para STT cross-platform | FFmpeg deve estar disponivel no `PATH` quando o backend real usar `openai-whisper` |
| T02.14 | concluida | Criar modo de contrato | Modo de contrato e explicitamente identificado e nao e apresentado como transcricao real |
| T02.15 | concluida | Criar router de transcricoes | Router especifico declara `POST /transcriptions/v1.0.0` |
| T02.16 | concluida | Registrar router no app | `src/main.py` inclui o router da E02 |
| T02.17 | concluida | Implementar autenticacao Bearer | Endpoint exige `Authorization: Bearer <token>` |
| T02.18 | concluida | Rejeitar token ausente | Requisicao sem `Authorization` retorna `401 Unauthorized` |
| T02.19 | concluida | Rejeitar token invalido | Requisicao com token incorreto retorna `401 Unauthorized` |
| T02.20 | concluida | Rejeitar header malformado | Header diferente de `Bearer <token>` retorna `401 Unauthorized` |
| T02.20.1 | concluida | Rejeitar `dev-token` em deploy publico | Quando `MINDVOX_PUBLIC_DEPLOYMENT=true`, token didatico e tratado como ausente e nao autentica E02 |
| T02.20.2 | concluida | Exigir transporte seguro em deploy publico | `POST /transcriptions/v1.0.0` retorna `403 Forbidden` se a aplicacao nao receber scheme `https` em modo publico |
| T02.20.3 | concluida | Rejeitar wildcard de trusted hosts em deploy publico | `MINDVOX_TRUSTED_HOSTS=*` impede inicializacao quando `MINDVOX_PUBLIC_DEPLOYMENT=true` |
| T02.20.4 | concluida | Exibir perfil ativo no Swagger global | `Active startup profile` informa `dev`, `contract` ou `prod` na documentacao OpenAPI |
| T02.21 | concluida | Validar presenca de `audio_file` | Requisicao sem arquivo retorna `422 Unprocessable Entity` |
| T02.22 | concluida | Validar nome de arquivo nao vazio | Arquivo sem nome retorna `422 Unprocessable Entity` |
| T02.23 | concluida | Validar extensoes aceitas | Apenas `.wav` e `.m4a` sao aceitas no MVP |
| T02.24 | concluida | Validar `content_type` | `content_type` deve ser compativel com audio aceito |
| T02.25 | concluida | Validar tamanho do arquivo | Arquivo acima de `MINDVOX_MAX_UPLOAD_MB` retorna `413 Payload Too Large` |
| T02.26 | concluida | Validar conteudo minimo do audio | Arquivo com extensao aceita mas conteudo invalido retorna `422 Unprocessable Entity` |
| T02.27 | concluida | Validar `class_date` | Valor invalido retorna `422 Unprocessable Entity`; valor informado deve seguir `YYYY-MM-DD` |
| T02.28 | concluida | Validar `session_label` | Valor invalido retorna `422 Unprocessable Entity`; valor informado deve ser simples, explicavel e curto |
| T02.28.1 | concluida | Limitar metadados opcionais textuais | `course` ate `160`, `discipline` ate `120` e `class_title` ate `200` caracteres; excesso retorna `422` |
| T02.29 | concluida | Validar `language` e aplicar padrao | Valor ausente assume `pt-BR`; valor invalido retorna `422 Unprocessable Entity`; valor informado deve usar formato simples, como `pt-BR` |
| T02.30 | concluida | Gerar `transcription_id` opaco | Identificador usa prefixo `tr_` e nao incorpora nome de arquivo, token, path local ou dado pessoal |
| T02.31 | concluida | Tratar falha do motor | Motor indisponivel retorna `503 Service Unavailable` |
| T02.32 | concluida | Tratar erro interno inesperado | Erro inesperado retorna `500 Internal Server Error` sem vazamento sensivel |
| T02.33 | concluida | Registrar logs operacionais permitidos | Logs registram apenas eventos operacionais como inicio, tamanho, content type, duracao, sucesso/falha e codigo controlado |
| T02.34 | concluida | Proibir vazamento em logs | Logs nao registram audio bruto, transcricao integral, `Authorization`, tokens, `.env`, paths sensiveis ou dados pessoais desnecessarios |
| T02.35 | concluida | Decidir persistencia de logs | Persistencia propria e implementada ou explicitamente adiada |
| T02.36 | concluida | Verificar logs contra vazamento sensivel | Teste automatizado ou revisao documentada confirma ausencia de audio bruto, transcricao integral, token, `.env`, path sensivel e dados pessoais desnecessarios nos logs |
| T02.36.1 | concluida | Persistir artefatos locais da transcricao bruta | Cada sucesso do STT salva JSON tecnico em `outputs/transcriptions/` e TXT humano em `outputs/human/transcriptions/` |
| T02.36.2 | concluida | Testar persistencia local da transcricao bruta | `test_post_transcriptions_saves_raw_transcription_artifacts` confirma JSON tecnico, TXT humano e `artifact_locations` sem path absoluto local |
| T02.36.3 | concluida | Nomear artefatos com metadados seguros | Arquivos locais podem usar prefixo sanitizado de data/titulo/sessao e sempre terminam com `transcription_id` opaco |
| T02.36.4 | concluida | Preservar TXT bruto auditavel | TXT humano da E02 contem somente a transcricao bruta, sem cabecalho artificial |
| T02.36.5 | concluida | Paragrafar TXT humano da transcricao | Quando o STT fornece segmentos, o TXT humano e quebrado em paragrafos legiveis sem inserir timestamps; timestamps ficam no JSON tecnico |
| T02.37 | concluida | Configurar documentacao FastAPI | OpenAPI exibe summary, description, formulario, formatos aceitos, Bearer token, sucesso, erros `400`, `401`, `403`, `413`, `422`, `500` e `503`, audio gravado e exclusao de streaming, TTS e speech-to-speech |
| T02.37.1 | concluida | Documentar didaticamente cada campo do formulario | `File(description=...)` e `Form(description=...)` explicam em ingles, com exemplo curto, `audio_file`, `course`, `discipline`, `class_date`, `class_title`, `session_label` e `language`, para orientar usuarios diretamente no Swagger/OpenAPI |
| T02.38 | concluida | Criar pasta de testes da E02 | `tests/e02_transcriptions/` existe |
| T02.39 | concluida | Criar README da pasta de testes | README explica hipoteses verificadas e comandos de execucao |
| T02.40 | concluida | Criar teste de sucesso | Envio valido em modo de contrato retorna `200 OK`, schema esperado, `transcription_id` com prefixo `tr_`, `language` padrao `pt-BR` quando ausente e `engine.version` conhecido ou `unknown` |
| T02.41 | concluida | Criar testes de autenticacao | Cobrir token ausente, token invalido e header malformado |
| T02.42 | concluida | Criar testes de arquivo invalido | Cobrir arquivo ausente `422`, nome de arquivo vazio `422`, tipo invalido `400`, conteudo corrompido `422` e arquivo grande demais `413` |
| T02.43 | concluida | Criar testes de metadados invalidos | Cobrir `class_date`, `session_label`, `language`, `course`, `discipline` e `class_title` invalidos retornando `422 Unprocessable Entity` |
| T02.43.1 | concluida | Criar teste de placeholder de token do app | `test_post_transcriptions_rejects_placeholder_api_token_configuration` passa |
| T02.43.2 | concluida | Criar teste de `dev-token` em deploy publico | `test_post_transcriptions_rejects_dev_token_in_public_deployment` passa |
| T02.43.3 | concluida | Criar testes de transporte seguro em deploy publico | `test_post_transcriptions_requires_https_in_public_deployment` e `test_post_transcriptions_accepts_https_in_public_deployment` passam |
| T02.43.4 | concluida | Criar teste de wildcard em trusted hosts | `test_public_deployment_rejects_wildcard_trusted_hosts` passa |
| T02.44 | concluida | Criar teste de falha do motor | Indisponibilidade do motor retorna `503 Service Unavailable` |
| T02.45 | concluida | Criar teste de metodo invalido | Metodo nao permitido na rota retorna `405 Method Not Allowed` |
| T02.46 | concluida | Criar teste de OpenAPI | `/openapi.json` reflete rota, formulario, descricoes didaticas dos campos com exemplos curtos, seguranca, sucesso, erros `400`, `401`, `403`, `413`, `422`, `500` e `503`, audio gravado e exclusao de streaming, TTS e speech-to-speech |
| T02.47 | concluida | Criar teste de nao vazamento sensivel em resposta | Resposta e erros nao expõem token, `.env`, paths ou dados privados |
| T02.48 | concluida | Criar teste ou revisao de nao vazamento sensivel em logs | Logs da E02 nao expõem token, `.env`, paths, audio bruto, transcricao integral ou dados pessoais desnecessarios |
| T02.49 | concluida | Rodar verificacao de sintaxe | `py_compile` passa para arquivos da E02 e testes relacionados |
| T02.50 | concluida | Rodar testes da E02 | `uv run python -m unittest discover -s tests/e02_transcriptions -v` passa |
| T02.51 | concluida | Rodar suite geral | `uv run python -m unittest discover -s tests -v` passa |
| T02.52 | concluida | Atualizar checklist aplicavel da Spec E02 | Checklist reflete implementacao, testes, OpenAPI, logs e pre-commit |
| T02.53 | concluida | Atualizar material didatico externo ao repo | Checklist didatico da E02 no vault e atualizado, quando aplicavel |
| T02.54 | concluida | Revisar `git status` | Apenas arquivos da E02 ou justificaveis aparecem |
| T02.55 | concluida | Revisar `git diff` | Diff e coerente com Spec, Plano e tarefas |
| T02.56 | concluida | Verificar ausencia de segredos e artefatos indevidos | Diff nao contem token real, `.env`, path sensivel, cache, `__pycache__`, temporario ou artefato gerado indevido |
| T02.57 | concluida | Definir mensagem de commit | Mensagem identifica a E02 concluida |
| T02.58 | concluida | Realizar prova real humana do endpoint | Humano executou `POST /transcriptions/v1.0.0` em modo real, com audio real, e confirmou `200 OK`, texto nao vazio, texto coerente com o audio, `engine.name` igual a `mlx-whisper` e ausencia de vazamento sensivel |
| T02.59 | concluida | Registrar resultado da prova real humana | Resultado da prova real registrado na E02, T02 e plano antes do commit |
| T02.60 | concluida | Atualizar checklist aplicavel da E02 com a prova real | Checklist da E02 deixa claro que a prova real humana e criterio de fechamento de endpoint tipo `E` |
| T02.61 | concluida | Realizar commit de fechamento | Commit principal da E02 realizado apos a prova real humana, seu registro documental e antes do prosseguimento efetivo para a E03 |

---

## 5. Comandos de Verificacao

Verificacao de sintaxe:

```bash
uv run python -m py_compile src/main.py src/settings.py src/routers/health.py src/routers/endpoint_security.py src/routers/transcriptions.py src/schemas/transcriptions.py src/services/transcription_service.py tests/e01_health/test_health.py tests/e02_transcriptions/test_transcriptions.py
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

Prova real humana obrigatoria antes do fechamento:

```bash
uv sync --extra stt
uv sync --extra stt-mlx
uv sync --extra stt-cross-platform
uv run python -c "import mlx_whisper; print('mlx_whisper ok')"
uv run python -c "import whisper; print('openai_whisper ok')"
uv run fastapi dev src/main.py
curl -X POST "http://127.0.0.1:8000/transcriptions/v1.0.0" \
  -H "Authorization: Bearer dev-token" \
  -F "audio_file=@/caminho/para/audio-real.wav;type=audio/wav" \
  -F "discipline=API" \
  -F "session_label=teste-real-e02" \
  -F "language=pt-BR"
```

Criterio minimo da prova real humana:

- retorno `200 OK`;
- campo `text` presente e nao vazio;
- texto reconhecivel em relacao ao audio real enviado;
- `engine.name` igual a `mlx-whisper` em macOS Apple Silicon ou `openai-whisper` em backend cross-platform;
- resposta sem token, path local, `.env` ou dado sensivel indevido;
- logs sem audio bruto, transcricao integral, token, `.env` ou path local sensivel.

---

## 6. Fora do Escopo

Estas tarefas nao implementam:

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

## 7. Criterio de Encerramento

Estas tarefas poderao ser encerradas quando:

- todas as tarefas aplicaveis estiverem marcadas como `concluida`;
- itens nao aplicaveis estiverem marcados como `N/A`, com justificativa;
- divergencias estiverem justificadas no documento correto;
- os testes da E02 passarem;
- a suite geral passar;
- a persistencia local usar nomes humanos seguros quando houver metadados, sem perder o `transcription_id` opaco e sem poluir o TXT bruto;
- os testes ou revisoes de metadados, OpenAPI e logs sem vazamento estiverem cobertos;
- os testes de hardening publico compartilhado passarem, incluindo bloqueio de `dev-token`, exigencia de transporte seguro em deploy publico e rejeicao de `MINDVOX_TRUSTED_HOSTS=*`;
- a prova real humana do endpoint tiver sido executada com sucesso;
- o resultado da prova real humana estiver registrado;
- a checklist da Spec E02 estiver coerente;
- a checklist da Spec E02 contiver item explicito de prova real humana para fechamento de endpoint tipo `E`;
- a auditoria final de Git estiver limpa;
- o commit de fechamento da E02 tiver sido realizado por Adalberto.

---

## 8. Registro de Fechamento

Status historico da E02 fechada em `2026-06-08`: `pronta-para-commit-manual`.

Status atual da emenda multiplataforma em `2026-06-25`: `pronta-para-auditoria`.

Auditoria final realizada em `2026-06-08`:

- `py_compile` passou para os arquivos da E01, E02 e testes relacionados;
- suite E02 passou com `23` testes;
- suite geral passou com `28` testes;
- `git status` foi revisado;
- `git diff` tracked foi revisado;
- `.env` local permanece ignorado;
- `.env.example` esta liberado para versionamento;
- nao ha `__pycache__`, `.pyc`, `.DS_Store` ou cache indevido fora da `.venv`;
- a varredura do diff nao encontrou path local sensivel ou padrao de segredo em linhas adicionadas;

Emenda de portabilidade STT registrada em `2026-06-25`:

- a E02 passou a aceitar `MINDVOX_TRANSCRIPTION_BACKEND=auto|mlx-whisper|openai-whisper`;
- `auto` preserva `mlx-whisper` em macOS Apple Silicon;
- `auto` usa `openai-whisper` em Windows/Linux;
- `openai-whisper` foi registrado como backend local cross-platform baseado em PyTorch, nao como provider remoto ou API OpenAI;
- `MINDVOX_TRANSCRIPTION_FALLBACK_MODEL` documenta o modelo do backend cross-platform, com padrao `turbo`;
- FFmpeg foi registrado como dependencia de sistema para ambientes que usam `openai-whisper`;
- a fronteira com a E03 foi reforcada: `provider` em E03 continua significando LLM externo para pos-processamento textual, nao STT remoto;
- a prova real historica com `mlx-whisper` permanece valida para a E02 original, mas a emenda cross-platform ainda deve ser auditada antes de eventual commit de fechamento.
- existe um path local antigo em `docs/mindvox_mentoring_agreement.md`, mas ele e preexistente e nao aparece em linhas adicionadas; a alteracao atual nesse arquivo limita-se a atualizar a rota antiga da E02 para `POST /transcriptions/v1.0.0`.

Pendencias restantes apos prova real humana de `2026-06-09`:

- `T02.61`: commit manual de fechamento por Adalberto.

Observacao normativa:

- a auditoria de `2026-06-08` validou o contrato automatizado da E02 em modo `contract`;
- a emenda posterior da E02, de `2026-06-09`, acrescentou uma exigencia bloqueante: teste manual real com `mlx-whisper` antes do commit;
- portanto, a E02 nao estava pronta para commit enquanto a prova real humana nao fosse executada, aprovada e registrada;
- a mesma regra deve ser aplicada a toda Spec tipo `E`: endpoint sem prova real humana nao esta concluido e nao libera mudanca de desenvolvimento para o endpoint seguinte.

Atualizacao tecnica em `2026-06-09`:

- extra `stt` instalado no ambiente isolado do Mindvox por `uv sync --extra stt`;
- `mlx-whisper` importavel no `.venv` do Mindvox;
- modelo `mlx-community/whisper-large-v3-turbo-fp16` baixado e mantido como motor final de qualidade da E02;
- camada de servico adaptada para preparar o layout `model.safetensors` como `weights.safetensors` quando necessario;
- camada de servico adaptada para enviar `pt` ao motor real quando o contrato receber `pt-BR`, preservando `pt-BR` na resposta publica;
- testes da E02 passaram com `25` testes;
- suite geral passou com `30` testes;
- smoke test tecnico real via API retornou `200 OK`, texto nao vazio, segmentos temporais, `language` igual a `pt-BR`, `engine.name` igual a `mlx-whisper` e `engine.model` igual a `mlx-community/whisper-large-v3-turbo-fp16`;
- este smoke test tecnico usou audio pequeno existente no N02 e nao substitui a prova real humana exigida por `T02.58`.

Atualizacao documental e OpenAPI em `2026-06-09`:

- incluida a tarefa `T02.37.1` para descricoes didaticas com exemplos curtos de cada campo do formulario;
- `src/routers/transcriptions.py` deve expor descricoes em ingles via `File(description=...)` e `Form(description=...)`;
- o teste de OpenAPI deve validar essas descricoes e exemplos para impedir regressao futura;
- esta atualizacao documental foi registrada antes do fechamento e nao altera o escopo funcional da E02.

Prova real humana executada em `2026-06-09`:

- endpoint: `POST /transcriptions/v1.0.0`;
- modo: `MINDVOX_TRANSCRIPTION_MODE=real`;
- token de desenvolvimento usado no servidor e no Swagger: `dev-token`;
- audio real de aula: `duration_seconds` retornou `3093.6`, aproximadamente `51min34s`;
- retorno HTTP observado no log: `200 OK`;
- `transcription_id`: `tr_20260609T154710Z_35969e23`;
- `language`: `pt-BR`;
- `text`: nao vazio, extenso e coerente com aula sobre APIs, API First, REST, SOAP/XML, JSON, GraphQL, gRPC, automacao, seguranca e dependencias externas;
- volume retornado: cerca de `42.998` caracteres e `7.747` palavras no campo `text`;
- `segments`: `2067` segmentos temporais;
- `engine.name`: `mlx-whisper`;
- `engine.model`: `mlx-community/whisper-large-v3-turbo-fp16`;
- `engine.version`: `unknown`;
- metadados retornados: `course`, `discipline`, `class_date`, `class_title` e `session_label`;
- resultado qualitativo: transcricao bruta real aprovada para uso como insumo da E03, com erros normais de STT em termos tecnicos e sem diarizacao final;
- observacao de produto: a transcricao bruta e adequada para prova do que foi ouvido e para processamento posterior; limpeza, normalizacao tecnica e organizacao de alto nivel pertencem ao endpoint futuro de pos-processamento;
- resposta analisada nao expos token, `.env`, path local sensivel, cache local ou audio bruto.

Atualizacao de hardening publico em `2026-06-10`:

- E02 passou a recusar `dev-token` quando `MINDVOX_PUBLIC_DEPLOYMENT=true`;
- E02 passou a retornar `403 Forbidden` quando `POST /transcriptions/v1.0.0` for chamado em deploy publico sem que a aplicacao receba scheme `https`;
- a aplicacao passou a recusar `MINDVOX_TRUSTED_HOSTS=*` quando `MINDVOX_PUBLIC_DEPLOYMENT=true`;
- OpenAPI e testes da E02 foram atualizados para documentar e validar o status `403`;
- a mudanca nao altera a prova real humana de STT ja executada, mas endurece o comportamento do endpoint em instalacao publica.

Mensagem de commit sugerida:

```text
feat(e02): implement real transcription endpoint
```
