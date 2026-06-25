# Mindvox

Mindvox tem como objetivo final transformar aulas gravadas ou transcritas em
memoria consultavel para estudo: o sistema deve receber conteudo de aula,
transcrever quando necessario, organizar o material, preservar rastreabilidade e
permitir consulta posterior por tema, disciplina, aula, sessao ou busca
semantica.

A versao atual entrega a base API First desse fluxo. Ela ja recebe audio ou
transcricao bruta, executa transcricao real quando configurada, processa o texto
da aula com um motor textual local ou externo e salva artefatos tecnicos e
humanos para estudo, auditoria e evolucao futura da memoria.

## Estado Atual

Ja estao implementados:

- `GET /health`
- `POST /transcriptions/v1.0.0`
- `POST /processed-transcriptions/v1.0.0`
- perfis de inicializacao `dev`, `prod` e `contract`
- autenticacao Bearer nos endpoints de negocio
- documentacao automatica FastAPI nos modos locais
- modo real de STT com `mlx-whisper` em macOS Apple Silicon e
  `openai-whisper` em Windows/Linux
- modo real de E03 com servidor local OpenAI-compatible ou provider externo
- modo mockado de contrato para testes sem STT e sem LLM reais
- fila local de retry da E03 quando a entrada for audio
- salvamento de artefatos locais em JSON, TXT e Markdown
- testes automatizados para E01, E02, E03 e perfis de startup

Ainda pertencem a etapas futuras:

- memoria semantica persistente consultavel por API
- busca relacional por curso, disciplina, aula, sessao, data ou tema
- interface grafica propria
- TTS, resposta falada em streaming ou speech-to-speech
- captura de audio ao vivo dentro da API
- gestao multiusuario de tokens, permissoes e auditoria por usuario

## Fluxo Do Projeto

O fluxo conceitual e:

```text
arquivo de audio ou transcricao bruta
  -> envio para a API
  -> transcricao, quando a entrada for audio
  -> processamento didatico da transcricao
  -> artefatos locais tecnicos e humanos
  -> memoria e buscas em etapas futuras
```

A captura do audio nao faz parte da API. O Mindvox comeca a operar a partir de
um arquivo de audio ja existente ou de uma transcricao bruta ja disponivel.

## Endpoints

### `GET /health`

Verifica se a API esta rodando.

Nao exige token.

```bash
curl http://127.0.0.1:8000/health
```

### `POST /transcriptions/v1.0.0`

Recebe um arquivo de audio e devolve uma transcricao estruturada.

Modos principais:

- `real`: usa o backend configurado em `MINDVOX_TRANSCRIPTION_BACKEND`
- `contract`: devolve resposta controlada para testar o contrato HTTP sem STT
  real

O backend real padrao da E02 e:

```text
MINDVOX_TRANSCRIPTION_BACKEND=auto
```

Com `auto`, a selecao e:

- macOS Apple Silicon: `mlx-whisper` com
  `mlx-community/whisper-large-v3-turbo-fp16`
- Windows ou Linux: `openai-whisper` com `turbo`

`openai-whisper` e biblioteca Python local baseada em PyTorch. Ela nao chama a
API da OpenAI e nao depende do modo `provider` da E03. O modo `provider`
continua sendo apenas para pos-processamento textual por LLM OpenAI-compatible,
como Groq.

### `POST /processed-transcriptions/v1.0.0`

Recebe audio ou transcricao bruta e devolve material processado para estudo.

Campos centrais da resposta:

- `raw_text`: texto bruto preservado para auditoria
- `didactic_text`: texto didatico, sequencial e organizado
- `themes`: mapa de temas da aula
- `technical_terms`: termos tecnicos normalizados
- `technology_mentions`: tecnologias, ferramentas, bibliotecas, APIs e
  providers citados
- `processing_notes`: observacoes, incertezas ou cuidados do processamento

Modos principais:

- `local`: usa um servidor local OpenAI-compatible, como `llama-server`
- `provider`: usa um provider externo compativel com o padrao OpenAI
- `contract`: valida o contrato HTTP sem LLM real
- `auto`: segue o modo da E02; `contract` leva a E03 para `contract`, e `real`
  leva a E03 para `local`

Quando a entrada da E03 e audio, o Mindvox primeiro gera a transcricao bruta e
depois coloca o item em uma fila local antes do processamento textual. Se o LLM
falhar temporariamente, a fila pode tentar novamente.

### Busca Semantica E Relacional

A busca semantica e a busca relacional fazem parte do objetivo final do Mindvox,
mas ainda nao estao implementadas como endpoints publicos nesta versao.

## Como Executar

Entre na pasta do projeto:

```bash
cd /caminho/para/Mindvox
```

Instale as dependencias principais:

```bash
uv sync
```

Para usar transcricao real, instale tambem o extra de STT:

```bash
uv sync --extra stt
```

O extra `stt` escolhe as dependencias por plataforma: `mlx-whisper` em macOS
Apple Silicon e `openai-whisper` em Windows/Linux. Para forcar uma familia
especifica:

```bash
uv sync --extra stt-mlx
uv sync --extra stt-cross-platform
```

Opcionalmente, crie um `.env` local a partir do exemplo:

```bash
cp .env.example .env
```

O arquivo `.env` nunca deve ser enviado ao Git.

## Modo Dev

Use o modo `dev` para desenvolvimento local, demonstracao com Swagger e testes
manuais.

Comando:

```bash
uv run fastapi dev src/main.py
```

Depois acesse:

```text
http://127.0.0.1:8000/docs
```

No Swagger, clique em `Authorize` e informe:

```text
dev-token
```

Esse token didatico e aceito apenas quando `MINDVOX_PUBLIC_DEPLOYMENT=false` e
nenhum token privado foi definido. Em ambiente exposto, use token forte em
`MINDVOX_API_TOKEN`.

### Dev Com Modelo Local Interno

Esse modo processa a E03 usando um servidor local OpenAI-compatible, como
`llama-server`. E o modo adequado quando o conteudo da aula nao deve sair da
maquina.

Configuracao tipica no `.env`:

```env
MINDVOX_PUBLIC_DEPLOYMENT=false
MINDVOX_ENABLE_DOCS=true
MINDVOX_TRANSCRIPTION_MODE=real
MINDVOX_POSTPROCESSING_MODE=local
MINDVOX_LLM_PROVIDER=local
MINDVOX_LLM_BASE_URL=http://127.0.0.1:8080/v1
MINDVOX_LLM_MODEL=qwen35a3b-q8
MINDVOX_LLM_API_KEY=
MINDVOX_LOCAL_LLM_AUTOSTART=true
MINDVOX_LLAMA_SERVER_PATH=
MINDVOX_LOCAL_LLM_MODEL_PATH=
MINDVOX_LLAMA_SERVER_CTX_SIZE=65536
MINDVOX_LLAMA_SERVER_GPU_LAYERS=99
MINDVOX_LLAMA_SERVER_PARALLEL=1
MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS=240
```

Com `MINDVOX_LOCAL_LLM_AUTOSTART=true`, o Mindvox tenta localizar e iniciar o
`llama-server` automaticamente quando a E03 precisar do motor local. Se o binario
ou o modelo nao forem encontrados, a falha aparece de forma explicita no
terminal.

### Dev Com Groq

Esse modo usa a E03 com API externa compativel com OpenAI. E util para
demonstracao quando o modelo local for pesado demais ou quando se quiser
comparar resultado com provider externo.

Configuracao tipica no `.env`:

```env
MINDVOX_PUBLIC_DEPLOYMENT=false
MINDVOX_ENABLE_DOCS=true
MINDVOX_TRANSCRIPTION_MODE=real
MINDVOX_POSTPROCESSING_MODE=provider
MINDVOX_LLM_PROVIDER=groq
MINDVOX_LLM_BASE_URL=https://api.groq.com/openai/v1
MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS=api.groq.com
MINDVOX_LLM_MODEL=llama-3.3-70b-versatile
MINDVOX_LLM_API_KEY=<sua-chave-groq-no-env-local>
MINDVOX_LLM_MAX_OUTPUT_TOKENS=20000
MINDVOX_LLM_TIMEOUT_SECONDS=1200
MINDVOX_LOCAL_LLM_AUTOSTART=false
```

Para testar um modelo menor e mais rapido, troque apenas
`MINDVOX_LLM_MODEL`, por exemplo para um modelo instantaneo disponivel na sua
conta Groq. O restante do modo continua igual.

Comando:

```bash
uv run fastapi dev src/main.py
```

No modo `provider`, o texto bruto da aula e enviado ao provider externo. Use
essa opcao somente quando isso for aceitavel para o conteudo processado.

### Dev Com Outro Provider OpenAI-Compatible

O Mindvox nao depende de Groq especificamente. Qualquer provider que exponha API
compativel com OpenAI pode ser usado, desde que a URL, o modelo, a chave e a
allowlist de host sejam configurados.

Exemplo:

```env
MINDVOX_POSTPROCESSING_MODE=provider
MINDVOX_LLM_PROVIDER=meu-provider
MINDVOX_LLM_BASE_URL=https://api.exemplo.com/openai/v1
MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS=api.exemplo.com
MINDVOX_LLM_MODEL=nome-do-modelo
MINDVOX_LLM_API_KEY=<chave-real-no-env-local>
MINDVOX_LOCAL_LLM_AUTOSTART=false
```

## Modo Prod

Use o modo `prod` para simular ou executar uma instalacao publica endurecida.
Nesse modo, o Mindvox bloqueia `dev-token`, desabilita docs por padrao, exige
hosts confiaveis e nao inicia Llama local automaticamente.

Gere um token forte fora do codigo:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Configure o ambiente seguro da instalacao:

```env
MINDVOX_PUBLIC_DEPLOYMENT=true
MINDVOX_ENABLE_DOCS=false
MINDVOX_TRUSTED_HOSTS=api.seu-dominio.example
MINDVOX_API_TOKEN=<token-forte-gerado-por-voce>
MINDVOX_POSTPROCESSING_MODE=provider
MINDVOX_LLM_PROVIDER=groq
MINDVOX_LLM_BASE_URL=https://api.groq.com/openai/v1
MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS=api.groq.com
MINDVOX_LLM_MODEL=llama-3.3-70b-versatile
MINDVOX_LLM_API_KEY=<chave-real-do-provider>
MINDVOX_LOCAL_LLM_AUTOSTART=false
```

Suba a API:

```bash
uv run fastapi run src/prod --host 0.0.0.0 --port 8000
```

Como acessar:

- use um cliente HTTP, sistema externo ou interface propria
- envie `Authorization: Bearer <token-forte-gerado-por-voce>`
- use HTTPS para os endpoints protegidos em exposicao publica
- deixe `/docs`, `/redoc` e `/openapi.json` desabilitados ou protegidos por uma
  camada externa

Exemplo de chamada ao health:

```bash
curl https://api.seu-dominio.example/health
```

Exemplo de cabecalho para endpoints protegidos:

```bash
curl \
  -H "Authorization: Bearer <token-forte-gerado-por-voce>" \
  https://api.seu-dominio.example/health
```

O endpoint `/health` nao exige token, mas o exemplo mostra o formato do cabecalho
que deve ser usado nos endpoints de negocio.

## Modo Teste Mockado

Use o modo `contract` quando quiser testar o contrato HTTP sem depender de
backend real de STT, `llama-server`, modelo local pesado ou provider externo.

Comando:

```bash
uv run fastapi dev src/contract
```

Depois acesse:

```text
http://127.0.0.1:8000/docs
```

No Swagger, use o token:

```text
dev-token
```

Nesse modo:

- `MINDVOX_RUNTIME_PROFILE=contract`
- `MINDVOX_TRANSCRIPTION_MODE=contract`
- `MINDVOX_POSTPROCESSING_MODE=auto`, resolvido como `contract`
- `MINDVOX_LOCAL_LLM_AUTOSTART=false`
- E02 e E03 retornam respostas controladas para teste do contrato

Se o terminal estiver dentro da pasta `src`, o comando equivalente e:

```bash
fastapi dev contract
```

## Artefatos Locais

As pastas de saida ficam fora do Git porque podem conter aulas reais e dados
sensiveis.

Transcricoes da E02:

```text
outputs/transcriptions/[class-date-title-session_]<transcription_id>.json
outputs/human/transcriptions/[class-date-title-session_]<transcription_id>.txt
```

Saidas processadas da E03:

```text
outputs/processed_transcriptions/[class-date-title-session_]<processed_transcription_id>.json
outputs/human/processed_transcriptions/[class-date-title-session_]<processed_transcription_id>.md
outputs/study_packages/
```

Saidas rejeitadas pela auditoria da E03:

```text
outputs/processed_transcriptions/rejected/
outputs/human/processed_transcriptions/rejected/
```

Fila local da E03 quando a entrada for audio:

```text
outputs/processed_transcriptions/queue/pending/
outputs/processed_transcriptions/queue/completed/
outputs/processed_transcriptions/queue/failed/
```

## Scripts Auxiliares Para Vault Local

O contrato publico continua sendo a API. Os scripts abaixo apenas ajudam o uso
local com transcricoes ja existentes no vault de estudo.

Preparar um `.txt` para anexar no Swagger da E03:

```bash
uv run python scripts/prepare_e03_raw_text_from_vault.py --section 3
```

Preparar e copiar campos para preenchimento manual:

```bash
uv run python scripts/prepare_e03_raw_text_from_vault.py --section 3 --copy-swagger-fields
```

Abrir o Swagger, preencher a tela e parar antes de executar:

```bash
uv run python scripts/fill_e03_swagger_from_vault.py --section 3
```

Submeter diretamente um `.metadata.json` ja preparado:

```bash
uv run python scripts/submit_e03_raw_text.py inputs/e03_raw_texts/arquivo.metadata.json
```

Preparar e submeter em um unico comando:

```bash
uv run python scripts/prepare_e03_raw_text_from_vault.py --section 4 --submit
```

## Variaveis De Ambiente

Consulte `.env.example` para a lista operacional completa. As principais sao:

Gerais:

```text
MINDVOX_API_TOKEN
MINDVOX_MAX_UPLOAD_MB
MINDVOX_PUBLIC_DEPLOYMENT
MINDVOX_ENABLE_DOCS
MINDVOX_TRUSTED_HOSTS
MINDVOX_RUNTIME_PROFILE
```

E02:

```text
MINDVOX_TRANSCRIPTION_MODE
MINDVOX_TRANSCRIPTION_BACKEND
MINDVOX_TRANSCRIPTION_MODEL
MINDVOX_TRANSCRIPTION_FALLBACK_MODEL
MINDVOX_TRANSCRIPTION_OUTPUT_DIR
MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR
```

E03:

```text
MINDVOX_POSTPROCESSING_MODE
MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS
MINDVOX_POSTPROCESSING_CHUNKING_MODE
MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS
MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS
MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED
MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED
MINDVOX_LLM_PROVIDER
MINDVOX_LLM_BASE_URL
MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS
MINDVOX_LLM_MODEL
MINDVOX_LLM_API_KEY
MINDVOX_LLM_MAX_OUTPUT_TOKENS
MINDVOX_LLM_TIMEOUT_SECONDS
MINDVOX_LOCAL_LLM_AUTOSTART
MINDVOX_LLAMA_SERVER_PATH
MINDVOX_LOCAL_LLM_MODEL_PATH
MINDVOX_LLAMA_SERVER_CTX_SIZE
MINDVOX_LLAMA_SERVER_GPU_LAYERS
MINDVOX_LLAMA_SERVER_PARALLEL
MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS
MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR
MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR
MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR
MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR
MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_ENABLED
MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS
MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS
MINDVOX_E03_STUDY_PACKAGE_OUTPUT_DIR
MINDVOX_E03_ACTIVE_COURSE_STORE
MINDVOX_E03_OBSIDIAN_EXPORT_ENABLED
MINDVOX_E03_OBSIDIAN_VAULTS_BASE_DIR
MINDVOX_E03_OBSIDIAN_VAULT_CREATE_ONLY
```

Regras importantes:

- nunca coloque tokens reais no Git
- em desenvolvimento local, token ausente usa `dev-token`
- em producao publica, `dev-token` e tratado como token ausente
- em modo `provider`, o texto bruto da E03 sai da maquina local para
  pos-processamento textual por LLM
- `openai-whisper` e `mlx-whisper` executam STT localmente; o backend
  cross-platform exige FFmpeg instalado e disponivel no `PATH`
- em modo `local`, o backend deve apontar para host local ou rede local
- em modo `provider`, use `https` e configure
  `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS`

## Verificacoes Uteis

Rodar a suite de testes:

```bash
uv run python -m unittest discover -s tests -v
```

Verificar sintaxe dos arquivos Python:

```bash
uv run python -m compileall .
```

Verificar apenas o ponto principal:

```bash
uv run python -m py_compile src/main.py
```
