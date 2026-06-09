# Spec E02: Endpoint de Transcricoes

## 1. Identificacao

- `ID`: `E02`
- `Tipo`: `Spec de Endpoint`
- `Status`: `fechada`
- `Endpoint`: `POST /transcriptions/v1.0.0`
- `Escopo`: recebimento de arquivo de audio e devolucao de transcricao textual
- `Dependencias normativas`:
  - `S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md`
  - `S02_GOVERNANCA_DAS_SPECS_MINDVOX.md`

---

## 2. Finalidade

Este endpoint recebe um arquivo de audio ja gravado e devolve uma transcricao em texto.

Ele existe porque STT e o primeiro servico de IA essencial do Mindvox. Sem transcricao, nao ha processamento de aula, memoria consultavel, busca semantica ou busca relacional.

---

## 3. Escopo

Este endpoint cobre:

- recebimento de arquivo de audio via API;
- autenticacao da requisicao por token;
- validacao basica do arquivo recebido;
- chamada a uma camada de servico responsavel pela transcricao;
- devolucao da transcricao em resposta estruturada;
- preparacao do schema para segmentos e falantes opcionais, ainda que o MVP nao implemente diarizacao completa;
- documentacao automatica no FastAPI;
- tratamento de erros previsiveis;
- logs operacionais sem vazamento de conteudo sensivel.

Este endpoint nao cobre:

- captura de audio ao vivo;
- streaming de audio;
- TTS;
- speech-to-speech;
- processamento semantico da transcricao;
- persistencia definitiva em memoria;
- busca semantica ou relacional;
- diarizacao final;
- analise afetiva da voz;
- correcao contextual por LLM;
- edicao manual da transcricao.

Esses temas pertencem a Specs futuras.

---

## 4. Metodo e Rota

Metodo HTTP:

```text
POST
```

Rota:

```text
/transcriptions/v1.0.0
```

Interpretacao:

- `transcriptions` indica o recurso produzido pela operacao.
- `v1.0.0` indica a primeira versao estavel do contrato HTTP e fica apos o nome do recurso, conforme o padrao versionado do Mindvox.

---

## 5. Entrada

O endpoint deve receber requisicao `multipart/form-data`.

Campos planejados:

| Campo | Tipo | Obrigatorio | Descricao |
| --- | --- | --- | --- |
| `audio_file` | arquivo | sim | Arquivo de audio a ser transcrito |
| `course` | texto | nao | Curso ou contexto geral da aula |
| `discipline` | texto | nao | Disciplina associada ao audio |
| `class_date` | texto/data ISO | nao | Data da aula, quando conhecida, preferencialmente em `YYYY-MM-DD` |
| `class_title` | texto | nao | Titulo ou identificacao da aula |
| `session_label` | texto | nao | Identificador da sessao, como `s1`, `s2`, `s3` ou `s4` |
| `language` | texto | nao | Idioma esperado do audio; valor padrao previsto: `pt-BR` |

Observacoes:

- os metadados opcionais nao devem bloquear a transcricao quando ausentes;
- a ausencia de `audio_file` deve gerar erro de validacao;
- a forma final dos metadados pode ser refinada antes do fechamento desta Spec.

Descricoes didaticas obrigatorias no OpenAPI:

- cada campo do `multipart/form-data` deve possuir `description` propria em `File(...)` ou `Form(...)`;
- cada descricao deve incluir pelo menos um exemplo curto e facil de reconhecer;
- as descricoes com exemplos devem aparecer na documentacao interativa da API para reduzir ambiguidade de uso, facilitar apresentacao tecnica e diminuir pedidos externos de explicacao;
- as descricoes publicas dos campos devem estar em ingles, coerentes com o restante da documentacao OpenAPI do endpoint;
- `audio_file`: `Required recorded audio file to be transcribed. Supported formats are .wav and .m4a. Example: class-2026-06-09.wav.`;
- `course`: `Optional name of the course or broader learning context. Use it to organize the transcription after it is generated. Example: Postgraduate course at Federal University of Goias.`;
- `discipline`: `Optional name of the discipline, subject, or class area related to the audio. Example: API Engineering for AI.`;
- `class_date`: `Optional date of the class. Use the YYYY-MM-DD format. Example: 2026-06-09.`;
- `class_title`: `Optional title, topic, or human-readable identification of the class. It helps identify the transcription later. Example: Introduction to API contracts.`;
- `session_label`: `Optional short identifier for the recording session. Use a simple value. Example: class-01.`;
- `language`: `Expected language of the audio. For Brazilian Portuguese, use pt-BR. Example: pt-BR.`;
- o teste de OpenAPI deve bloquear remocao futura dessas explicacoes.

---

## 6. Validacoes

Validacoes minimas:

- `audio_file` deve existir;
- o arquivo deve ter nome nao vazio;
- o arquivo deve ter extensao aceita pelo MVP e `content_type` compativel com audio;
- o arquivo nao deve exceder o limite maximo definido para o MVP;
- `class_date`, quando informado, deve usar formato `YYYY-MM-DD`;
- `session_label`, quando informado, deve aceitar valores simples e explicaveis, como `s1`, `s2`, `s3`, `s4` ou texto curto equivalente;
- `language`, quando informado, deve usar formato simples, como `pt-BR`.

Extensoes aceitas no MVP:

```text
.wav
.m4a
```

Justificativa:

- `.wav` cobre o formato bruto ou intermediario do pipeline local de gravacao;
- `.m4a` cobre o formato final comprimido previsto para reduzir tamanho sem complicar o MVP;
- outros formatos poderao ser incluidos em specs futuras sem alterar a natureza do endpoint.

Limite inicial do MVP:

```text
500 MB
```

Regra:

- o limite deve ser configuravel por variavel de ambiente ou configuracao equivalente, com nome inicial `MINDVOX_MAX_UPLOAD_MB`;
- `500 MB` e o valor padrao inicial para desenvolvimento local e uso controlado;
- arquivos `.wav` muito longos devem preferencialmente ser convertidos para `.m4a` antes do envio.

---

## 7. Processamento

Fluxo esperado:

```text
receber requisicao
  -> autenticar token
  -> validar arquivo e metadados
  -> registrar log operacional minimo
  -> encaminhar arquivo para servico de transcricao
  -> receber texto transcrito
  -> montar resposta estruturada
  -> devolver resposta HTTP
```

Separacao esperada de responsabilidades:

- `router`: recebe a requisicao, declara o contrato FastAPI e transforma erros em respostas HTTP;
- `schema`: define modelos de resposta e, quando aplicavel, modelos de erro;
- `service`: executa a transcricao ou chama o motor de STT;
- `settings`: concentra configuracoes externas, como token e limite de upload;
- `utils`: funcoes auxiliares pequenas, como validacao de extensao, tamanho e normalizacao de metadados.

O endpoint nao deve conter toda a logica de STT dentro do router.

---

## 8. Motor STT

O motor STT primario do MVP sera:

```text
mlx-whisper + mlx-community/whisper-large-v3-turbo-fp16
```

Justificativa:

- o Mindvox precisa de transcricao batch confiavel de arquivos ja gravados;
- o hardware de referencia do projeto suporta o modelo com folga;
- `mlx-whisper` e coerente com a referencia tecnica do N02 do Atrium para STT local;
- `whisper-large-v3-turbo-fp16` favorece qualidade e desempenho em Apple Silicon;
- a solucao e mais previsivel para o E02 do que usar um LLM multimodal como primeiro transcritor.

Fallback de desenvolvimento ou smoke test:

```text
mlx-whisper + whisper-small
```

O fallback acima pode ser usado para validar instalacao, contrato da API ou testes rapidos, mas nao deve ser apresentado como motor final de qualidade do E02.

Para permitir implementacao incremental, o endpoint pode iniciar com uma camada de servico substituivel, desde que:

- o contrato HTTP do endpoint permaneca estavel;
- o router nao fique acoplado a um motor especifico;
- a troca futura do motor nao exija reescrita do contrato da API;
- qualquer mock temporario seja explicitamente identificado como temporario e nao seja apresentado como transcricao real.

Decisoes futuras possiveis:

- comparar `fp16` com variante quantizada, como `whisper-large-v3-turbo-q4`, se houver necessidade real de reduzir custo computacional;
- integrar diarizacao acustica antes ou depois da transcricao;
- avaliar Gemma 4 12B multimodal como motor experimental de comparacao, nao como dependencia do MVP;
- usar LLM multimodal ou textual em etapa posterior de processamento semantico, correcao contextual controlada, extracao de temas ou analise afetiva, desde que isso seja especificado em documento proprio.

Regra:

- o E02 deve entregar transcricao confiavel primeiro;
- recursos avancados devem permanecer como portas abertas de arquitetura, nao como obrigacoes do MVP.

---

## 9. Resposta de Sucesso

Status HTTP:

```text
200 OK
```

Formato planejado:

```json
{
  "transcription_id": "tr_20260607T185700Z_ab12cd34",
  "text": "Texto transcrito do audio.",
  "language": "pt-BR",
  "duration_seconds": 123.45,
  "segments": [
    {
      "start_seconds": 0.0,
      "end_seconds": 12.4,
      "text": "Trecho transcrito.",
      "speaker_label": null
    }
  ],
  "metadata": {
    "course": "Pos-Graduacao",
    "discipline": "Construcao de APIs para IA",
    "class_date": "2026-06-07",
    "class_title": "Aula 1",
    "session_label": "s1"
  },
  "engine": {
    "name": "mlx-whisper",
    "model": "mlx-community/whisper-large-v3-turbo-fp16",
    "version": "defined-at-runtime"
  }
}
```

Campos:

| Campo | Descricao |
| --- | --- |
| `transcription_id` | Identificador opaco da transcricao gerada, com prefixo `tr_` |
| `text` | Texto transcrito |
| `language` | Idioma usado ou detectado |
| `duration_seconds` | Duracao estimada do audio, quando disponivel |
| `segments` | Lista de trechos temporais da transcricao; pode ser vazia quando indisponivel |
| `segments[].speaker_label` | Identificacao opcional de falante, quando diarizacao futura estiver disponivel |
| `metadata` | Metadados recebidos e normalizados |
| `engine` | Informacao controlada sobre o motor usado |

Regra de seguranca:

- `engine` nao deve expor caminhos locais, chaves, tokens ou detalhes sensiveis de infraestrutura.
- `speaker_label` pode permanecer `null` no MVP.
- o schema deve permitir evolucao futura para diarizacao sem exigir quebra imediata do contrato.

Regras de estabilidade do contrato:

- `transcription_id` deve ser tratado pelo cliente como identificador opaco;
- o formato inicial recomendado e `tr_<timestamp UTC>_<sufixo curto aleatorio>`, por exemplo `tr_20260607T185700Z_ab12cd34`;
- `segments` deve existir na resposta como lista;
- quando o motor devolver timestamps, `segments` deve conter os trechos temporais;
- quando timestamps nao estiverem disponiveis, `segments` pode ser uma lista vazia;
- `speaker_label` deve existir nos segmentos e pode permanecer `null` ate que haja diarizacao real.

---

## 10. Respostas de Erro

### 10.1 Arquivo Ausente

Status:

```text
422 Unprocessable Entity
```

Uso:

- quando `audio_file` nao for enviado.

### 10.1.1 Nome de Arquivo Vazio

Status:

```text
422 Unprocessable Entity
```

Uso:

- quando o campo `audio_file` existir, mas o arquivo enviado nao possuir nome valido.

### 10.2 Tipo de Arquivo Invalido

Status:

```text
400 Bad Request
```

Resposta exemplo:

```json
{
  "detail": "Unsupported audio file type. Supported formats: .wav, .m4a."
}
```

### 10.3 Arquivo de Audio Invalido ou Corrompido

Status:

```text
422 Unprocessable Entity
```

Resposta exemplo:

```json
{
  "detail": "Audio file cannot be decoded."
}
```

Uso:

- quando o arquivo tiver extensao aceita, mas o conteudo nao puder ser lido como audio;
- quando o arquivo estiver corrompido;
- quando o motor ou etapa preliminar identificar audio tecnicamente invalido.

### 10.4 Arquivo Grande Demais

Status:

```text
413 Payload Too Large
```

Resposta exemplo:

```json
{
  "detail": "Audio file exceeds the maximum allowed size."
}
```

### 10.5 Autenticacao Ausente ou Invalida

Status:

```text
401 Unauthorized
```

Resposta exemplo:

```json
{
  "detail": "Authentication required."
}
```

Uso:

- quando o header `Authorization` estiver ausente;
- quando o token enviado for invalido;
- quando o formato do header nao seguir `Bearer <token>`.

### 10.6 Falha no Motor de Transcricao

Status:

```text
503 Service Unavailable
```

Resposta exemplo:

```json
{
  "detail": "Transcription service is unavailable."
}
```

### 10.7 Erro Interno Inesperado

Status:

```text
500 Internal Server Error
```

Resposta exemplo:

```json
{
  "detail": "Internal transcription error."
}
```

Regra:

- erros internos nao devem expor stack trace, caminhos locais, conteudo integral do audio ou configuracoes privadas.

### 10.8 Metadados Invalidos

Status:

```text
422 Unprocessable Entity
```

Uso:

- quando `class_date` informado nao seguir `YYYY-MM-DD`;
- quando `session_label` informado nao for simples, explicavel e curto;
- quando `language` informado nao seguir formato simples, como `pt-BR`.

---

## 11. Seguranca

Regras minimas:

- nao registrar conteudo integral da transcricao em log;
- nao registrar bytes do arquivo em log;
- nao expor `.env`, chaves, tokens ou caminhos internos;
- validar tipo e tamanho do arquivo antes de processar;
- tratar audio e transcricao como dados sensiveis;
- usar exemplos ficticios na documentacao publica;
- evitar envio externo de audio sem decisao explicita e documentada.

Autenticacao:

- o E02 deve exigir autenticacao desde o MVP;
- a forma inicial deve ser `Authorization: Bearer <token>`;
- o token do MVP deve ser lido de configuracao externa, com nome inicial `MINDVOX_API_TOKEN`;
- o token nao deve ser gravado no codigo-fonte, em logs, em mensagens de erro ou em exemplos reais;
- o uso de `.env`, variaveis de ambiente, `BaseSettings`, `os.environ` ou mecanismo equivalente deve manter segredos fora do codigo versionado;
- requisicoes sem token, com token invalido ou com formato incorreto devem receber `401 Unauthorized`;
- antes de qualquer exposicao em rede, acesso externo ou uso multiusuario, uma spec propria devera definir autenticacao, autorizacao, limites de uso e protecoes contra abuso.

Horizonte de seguranca:

- o MVP deve simular uma API simples, mas preparada segundo padroes de arquitetura, seguranca e configuracao compativeis com AWS;
- essa diretriz nao torna o deploy em AWS obrigatorio no MVP, mas orienta escolhas que nao bloqueiem endurecimento futuro;
- a arquitetura nao deve impedir evolucao futura para JWT assinado, OAuth2, OpenID Connect, Keycloak, API Gateway, Cognito ou outro mecanismo equivalente;
- as camadas de seguranca devem ser proporcionais a sensibilidade dos dados transitados, incluindo audio de aula, transcricao, metadados academicos e eventuais dados pessoais;
- custo e simplicidade nao podem justificar remocao de protecao basica do endpoint.

---

## 12. Logs

Logs devem registrar apenas dados operacionais necessarios.

Permitido:

- inicio da requisicao;
- nome normalizado ou hash do arquivo, se necessario;
- tamanho do arquivo;
- content type;
- resultado da autenticacao, sem registrar o token;
- duracao do processamento;
- sucesso ou falha;
- codigo de erro controlado.

Nao permitido:

- conteudo integral da transcricao;
- audio bruto;
- header `Authorization`;
- chaves, tokens ou valores de `.env`;
- paths locais sensiveis;
- dados pessoais desnecessarios.

---

## 13. Documentacao FastAPI Esperada

A documentacao automatica deve mostrar:

- titulo claro do endpoint;
- descricao curta da finalidade;
- campos aceitos no formulario;
- descricao didatica propria com exemplo curto para cada campo do formulario, visivel na documentacao interativa;
- formatos de arquivo aceitos;
- resposta de sucesso;
- erros principais: `400`, `401`, `413`, `422`, `500` e `503`;
- esquema de autenticacao por `Bearer token`;
- indicacao de que o audio deve ser arquivo ja gravado;
- indicacao de que streaming, TTS e speech-to-speech estao fora deste endpoint.

Observacao:

- `405 Method Not Allowed` deve ser tratado e testado como erro de metodo HTTP invalido, mas nao precisa aparecer como resposta principal documentada do `POST` no OpenAPI.

Texto sugerido para `summary`:

```text
Transcribe audio file
```

Texto sugerido para `description`:

```text
Receives a recorded audio file and returns a text transcription with optional class metadata.
```

---

## 14. Criterios de Aceite

O endpoint podera ser considerado pronto quando:

- a rota `POST /transcriptions/v1.0.0` existir;
- a rota exigir `Authorization: Bearer <token>`;
- a API rejeitar requisicao sem token ou com token invalido;
- a documentacao do FastAPI exibir o endpoint corretamente;
- a API aceitar arquivo valido em `multipart/form-data`;
- a API rejeitar requisicao sem arquivo;
- a API rejeitar arquivo sem nome valido;
- a API rejeitar tipo de arquivo invalido;
- a API rejeitar arquivo com extensao aceita mas conteudo invalido ou corrompido;
- a API rejeitar arquivo acima do limite definido;
- a API rejeitar metadados invalidos em `class_date`, `session_label` ou `language`;
- a resposta de sucesso seguir schema estruturado;
- a resposta de sucesso retornar `transcription_id` opaco com prefixo `tr_`;
- a resposta de sucesso aplicar `pt-BR` como padrao quando `language` estiver ausente;
- a resposta de sucesso informar `engine.version` com versao conhecida ou `unknown`;
- a resposta de sucesso incluir `segments` como lista, mesmo que vazia e sem diarizacao real no MVP;
- erros previsiveis tiverem status HTTP coerente;
- logs nao vazarem dados sensiveis;
- houver teste valido e testes invalidos para ausencia de arquivo, arquivo sem nome, tipo invalido, audio corrompido, arquivo grande, metadados invalidos, token ausente, token invalido, header malformado, falha do motor, OpenAPI e nao vazamento;
- Adalberto conseguir explicar o fluxo completo do endpoint.

---

## 15. Exemplos de Teste

### 15.1 Teste Valido

Entrada:

```text
POST /transcriptions/v1.0.0
Authorization: Bearer <token valido>
multipart/form-data:
  audio_file = aula_s1.m4a
  discipline = Construcao de APIs para IA
  session_label = s1
  language = pt-BR
```

Resultado esperado:

```text
200 OK
```

Com resposta contendo `transcription_id`, `text`, `language`, `segments`, `metadata` e `engine`.

No MVP, `segments` pode ser uma lista vazia; quando houver segmentos, `speaker_label` pode ser `null`.

### 15.2 Teste Invalido: Sem Arquivo

Entrada:

```text
POST /transcriptions/v1.0.0
Authorization: Bearer <token valido>
multipart/form-data:
  discipline = Construcao de APIs para IA
```

Resultado esperado:

```text
422 Unprocessable Entity
```

### 15.3 Teste Invalido: Tipo Nao Suportado

Entrada:

```text
POST /transcriptions/v1.0.0
Authorization: Bearer <token valido>
multipart/form-data:
  audio_file = anotacoes.txt
```

Resultado esperado:

```text
400 Bad Request
```

### 15.4 Teste Invalido: Token Ausente

Entrada:

```text
POST /transcriptions/v1.0.0
multipart/form-data:
  audio_file = aula_s1.m4a
```

Resultado esperado:

```text
401 Unauthorized
```

### 15.5 Teste Invalido: Token Invalido

Entrada:

```text
POST /transcriptions/v1.0.0
Authorization: Bearer <token invalido>
multipart/form-data:
  audio_file = aula_s1.m4a
```

Resultado esperado:

```text
401 Unauthorized
```

### 15.6 Teste Invalido: Audio Corrompido

Entrada:

```text
POST /transcriptions/v1.0.0
Authorization: Bearer <token valido>
multipart/form-data:
  audio_file = aula_corrompida.m4a
```

Resultado esperado:

```text
422 Unprocessable Entity
```

---

## 16. Checklist Aplicavel do Endpoint

Checklist extraido do modelo geral da S02.

Interpretacao:

- itens de contrato ja decididos pela Spec aparecem como `[x]`;
- itens que dependem de codigo, testes ou demonstracao final permanecem como `[ ]`;
- itens pendentes devem ser resolvidos durante a implementacao da E02 antes de iniciar o proximo endpoint.
- apos a criacao posterior do P02/T02, itens de implementacao, testes e Git marcados como `[x]` nesta Spec registram evidencia preliminar da implementacao antecipada, mas o fechamento formal depende de revalidacao item a item na T02 e da auditoria final antes do commit.

| Item | Status | Justificativa |
| --- | --- | --- |
| Metodo HTTP definido | [x] | `POST` aprovado para envio de audio a transcrever |
| Rota definida | [x] | `/transcriptions/v1.0.0` aprovada |
| Padrao de versionamento decidido | [x] | Endpoint de negocio usa versao apos o recurso: `/transcriptions/v1.0.0` |
| Finalidade explicada | [x] | Receber audio gravado e devolver transcricao textual |
| Diferenca entre endpoint operacional e endpoint de negocio esclarecida | [x] | E02 e servico de negocio essencial do Mindvox |
| Parametros de path definidos | N/A | Endpoint nao exige identificador na rota |
| Parametros de query definidos | N/A | Endpoint usa `multipart/form-data`, nao query string |
| Body definido | [x] | `multipart/form-data` com `audio_file` e metadados opcionais |
| Headers exigidos definidos | [x] | `Authorization: Bearer <token>` |
| Tipos, obrigatoriedade e limites de entrada descritos | [x] | Arquivo obrigatorio, metadados opcionais, formatos `.wav`/`.m4a`, limite de `500 MB` |
| Resposta de sucesso definida | [x] | JSON com `transcription_id`, `text`, `language`, `segments`, `metadata` e `engine` |
| Status code de sucesso definido | [x] | `200 OK` |
| Campos da resposta descritos | [x] | Campos documentados em tabela |
| Ausencia de dados sensiveis verificada | [x] | Spec proibe paths locais, chaves, tokens e detalhes sensiveis de infraestrutura |
| Schema de resposta definido | [x] | Modelos Pydantic criados em `src/schemas/transcriptions.py` |
| Erros principais listados | [x] | `422`, `400`, `413`, `401`, `503` e `500` descritos; `405` tratado separadamente como metodo HTTP invalido |
| Status codes de erro definidos | [x] | Cada erro previsivel tem status HTTP planejado |
| Mensagens de erro sem vazamento sensivel | [x] | Spec proibe stack trace, caminhos locais, audio integral e configuracoes privadas |
| Metodo HTTP invalido considerado | [x] | Teste cobre `GET /transcriptions/v1.0.0` retornando `405` |
| Entrada invalida considerada | [x] | Ausencia de arquivo, nome de arquivo vazio, tipo invalido, audio corrompido, arquivo grande, metadados invalidos e token invalido previstos |
| Necessidade de autenticacao decidida | [x] | Autenticacao obrigatoria por `Bearer token` desde o MVP |
| Necessidade de autorizacao decidida | [x] | Autorizacao fina adiada; token unico do MVP protege o endpoint |
| Dados sensiveis identificados | [x] | Audio, transcricao, metadados academicos, token e configuracoes tratados como sensiveis |
| Regras de nao vazamento descritas | [x] | Regras de seguranca e logs definidas |
| Uso de `.env`, tokens ou configuracao externa definido | [x] | `MINDVOX_API_TOKEN` e `MINDVOX_MAX_UPLOAD_MB` previstos |
| Eventos permitidos em log descritos | [x] | Inicio da requisicao, tamanho, content type, duracao, sucesso/falha e codigo controlado |
| Dados proibidos em log descritos | [x] | Audio bruto, transcricao integral, `Authorization`, tokens, `.env`, paths e dados pessoais desnecessarios |
| Logs existentes do servidor considerados | [x] | Logs do servidor sao insuficientes para todo o E02, mas contam como base operacional |
| Necessidade de logger proprio decidida | [x] | Logger `mindvox.transcriptions` criado para eventos operacionais sem dados sensiveis |
| Persistencia de logs decidida | [x] | Persistencia propria adiada; o MVP usa logs operacionais do processo/servidor |
| `summary` definido | [x] | `Transcribe audio file` |
| `description` definida | [x] | `Receives a recorded audio file and returns a text transcription with optional class metadata.` |
| Respostas principais aparecem na documentacao | [x] | Teste de OpenAPI valida respostas `200`, `400`, `401`, `413`, `422`, `500` e `503` |
| Parametros/body aparecem corretamente | [x] | Teste de OpenAPI valida `requestBody` multipart |
| Descricoes didaticas dos campos aparecem na documentacao | [x] | Teste de OpenAPI valida descricoes publicas em ingles, com exemplos curtos, para `audio_file`, `course`, `discipline`, `class_date`, `class_title`, `session_label` e `language` |
| `/openapi.json` reflete o contrato aprovado | [x] | Coberto por teste automatizado da E02 |
| Router definido | [x] | Router criado em `src/routers/transcriptions.py` |
| Handler definido com nome explicavel | [x] | Handler `transcribe_recorded_audio` criado |
| Router registrado no `app` | [x] | `transcriptions_router` registrado em `src/main.py` |
| Endpoint temporario ou exemplo removido | [x] | Rascunho `src/routers/services.py` removido |
| Dependencias fora do escopo nao sao importadas | [x] | Implementacao usa FastAPI, Pydantic e biblioteca padrao; `mlx-whisper` so e importado dentro do servico real |
| Codigo compila | [x] | `py_compile` executado com sucesso |
| Pasta propria de testes criada | [x] | `tests/e02_transcriptions/` criada |
| README da pasta de testes criado | [x] | `tests/e02_transcriptions/README.md` criado |
| README da pasta de testes explica hipoteses verificadas | [x] | README explica sucesso, autenticacao, validacoes, erros, OpenAPI e seguranca |
| README da pasta de testes explica como executar os testes | [x] | README registra comando especifico da E02 e comando geral |
| Teste automatizado de sucesso criado | [x] | Teste cobre envio valido em modo `contract`, schema, `transcription_id`, `language` padrao e `engine.version` |
| Teste automatizado de erro principal criado | [x] | Testes cobrem ausencia de arquivo, nome de arquivo vazio, tipo invalido, audio corrompido, arquivo grande, metadados invalidos, token e falha do motor |
| Teste automatizado de metodo invalido criado | [x] | Teste cobre `GET /transcriptions/v1.0.0` |
| Teste automatizado do OpenAPI criado | [x] | Teste valida `summary`, `description`, formulario, autenticacao e respostas `400`, `401`, `413`, `422`, `500` e `503` |
| Comando de teste registrado | [x] | Comandos registrados no README da pasta de testes |
| Todos os testes passam antes do proximo endpoint | [x] | Suite geral executada com 28 testes passando |
| Teste funcional manual real executado e registrado | [x] | Prova real humana executada em `2026-06-09` com `MINDVOX_TRANSCRIPTION_MODE=real`, audio real de aula, retorno `200 OK`, `engine.name` igual a `mlx-whisper` e modelo `mlx-community/whisper-large-v3-turbo-fp16` |
| Comando de execucao local documentado | [x] | README do projeto documenta execucao local da API |
| Exemplo de chamada valida documentado | [x] | Teste valido descrito nesta Spec |
| Exemplo de falha relevante documentado | [x] | Testes invalidos descritos nesta Spec |
| Endpoint demonstrado com entrada real representativa | [x] | Audio real de aula com `duration_seconds` igual a `3093.6`, texto nao vazio, coerente e segmentado |
| Endpoint explicavel por finalidade, entrada, processamento, saida, erro e teste | [x] | Spec descreve o fluxo completo esperado |
| Limites de escopo claros | [x] | Streaming, TTS, processamento semantico, persistencia, busca e diarizacao final adiados |
| `git status` revisado | [x] | Revisado; mudancas pertencem a E02 e configuracao/documentacao diretamente associada |
| `git diff` revisado | [x] | Revisado; diff tracked inclui `.gitignore`, README, Spec E02, Governanca S02 e `src/main.py` |
| Arquivos alterados pertencem ao escopo da E02 ou estao justificados | [x] | Escopo inclui endpoint, schemas, servico, settings, testes, README, `.env.example` e ajuste de `.gitignore` |
| Nenhum segredo, token, `.env`, path sensivel ou dado privado aparece no diff | [x] | Sem segredo real em linhas adicionadas; `.env` local permanece ignorado |
| Nenhum cache, `__pycache__`, temporario ou artefato gerado indevido aparece no diff | [x] | Caches removidos apos testes |
| Testes automatizados da E02 passaram | [x] | `uv run python -m unittest discover -s tests/e02_transcriptions -v` passou |
| Testes gerais passaram | [x] | `uv run python -m unittest discover -s tests -v` passou |
| Checklist aplicavel da E02 esta todo marcado ou justificado como `N/A` | [x] | Todos os itens funcionais estao concluidos ou justificados; resta apenas commit de fechamento |
| README da pasta de testes esta atualizado | [x] | README criado e atualizado para a E02 |
| Materiais didaticos externos ao repo foram atualizados | [x] | Checklist didatico da E02 no vault atualizado para revisao oral |
| Mensagem de commit planejada identifica a E02 concluida | [x] | Sugestao: `feat(e02): implement real transcription endpoint` |
| Commit de fechamento realizado | [ ] | Ultima acao antes de iniciar a E03 |

---

## 17. Decisoes de MVP e Detalhes de Implementacao

Decisoes adotadas para o MVP:

- formatos aceitos: `.wav` e `.m4a`;
- limite padrao: `500 MB`, configuravel;
- `class_date`: data validada no formato `YYYY-MM-DD`;
- `transcription_id`: identificador opaco com prefixo `tr_`;
- `segments`: campo sempre presente na resposta, podendo ser lista vazia;
- `speaker_label`: campo preparado para diarizacao futura, podendo ser `null`;
- autenticacao: obrigatoria desde o MVP por `Authorization: Bearer <token>`;
- token do MVP: lido de configuracao externa, com nome inicial `MINDVOX_API_TOKEN`;
- limite de upload: lido de configuracao externa, com nome inicial `MINDVOX_MAX_UPLOAD_MB`;
- runtime normal: deve usar o motor STT real definido nesta Spec;
- stub/mock: permitido apenas em testes automatizados ou modo de contrato explicitamente identificado, nunca como transcricao real em runtime;
- `engine.version`: deve ser preenchido com a versao conhecida da biblioteca/modelo quando disponivel; quando indisponivel, deve usar valor controlado como `unknown`, sem expor paths locais.

Detalhes resolvidos na implementacao:

- mecanismo concreto de leitura de configuracao: `src/settings.py`, usando variaveis de ambiente;
- variaveis documentadas para o MVP: `MINDVOX_API_TOKEN`, `MINDVOX_MAX_UPLOAD_MB`, `MINDVOX_TRANSCRIPTION_MODE` e `MINDVOX_TRANSCRIPTION_MODEL`;
- schema de resposta: modelos Pydantic em `src/schemas/transcriptions.py`;
- router: `src/routers/transcriptions.py`;
- servico substituivel: `src/services/transcription_service.py`;
- modo real: tenta usar `mlx-whisper` com o modelo configurado; se o motor nao estiver instalado/disponivel, retorna erro controlado `503`;
- dependencia STT real: declarada como extra opcional `stt`; para instalar, usar `uv sync --extra stt`;
- compatibilidade do modelo final: quando o repositorio `mlx-community/whisper-large-v3-turbo-fp16` entregar pesos como `model.safetensors`, a camada de servico prepara layout local compativel com `mlx-whisper`, expondo o mesmo arquivo como `weights.safetensors`, sem trocar o modelo final de qualidade da E02;
- idioma do motor real: quando o contrato publico receber `pt-BR`, a camada de servico envia `pt` ao `mlx-whisper`, preservando `pt-BR` na resposta publica do Mindvox;
- modo de contrato: habilitado por `MINDVOX_TRANSCRIPTION_MODE=contract`, permitido apenas para testes automatizados e demonstracao controlada do contrato HTTP;
- testes da E02: `tests/e02_transcriptions/test_transcriptions.py`;
- README dos testes da E02: `tests/e02_transcriptions/README.md`.

Comandos de verificacao executados:

```bash
uv run python -m py_compile src/main.py src/settings.py src/routers/health.py src/routers/transcriptions.py src/schemas/transcriptions.py src/services/transcription_service.py tests/e01_health/test_health.py tests/e02_transcriptions/test_transcriptions.py
uv run python -m unittest discover -s tests/e02_transcriptions -v
uv run python -m unittest discover -s tests -v
```

Resultado verificado:

```text
E02: Ran 23 tests in 0.038s
OK

Geral: Ran 28 tests in 0.055s
OK
```

Exemplo de requisicao manual em modo de contrato:

```bash
MINDVOX_API_TOKEN=dev-token MINDVOX_TRANSCRIPTION_MODE=contract uv run fastapi dev src/main.py
curl -X POST "http://127.0.0.1:8000/transcriptions/v1.0.0" \
  -H "Authorization: Bearer dev-token" \
  -F "audio_file=@/caminho/para/audio.wav;type=audio/wav" \
  -F "discipline=API" \
  -F "session_label=s1" \
  -F "language=pt-BR"
```

Teste manual real bloqueante antes do commit:

```bash
uv sync --extra stt
uv run python -c "import mlx_whisper; print('mlx_whisper ok')"
MINDVOX_API_TOKEN=dev-token MINDVOX_TRANSCRIPTION_MODE=real uv run fastapi dev src/main.py
curl -X POST "http://127.0.0.1:8000/transcriptions/v1.0.0" \
  -H "Authorization: Bearer dev-token" \
  -F "audio_file=@/caminho/para/audio-real.wav;type=audio/wav" \
  -F "discipline=API" \
  -F "session_label=teste-real-e02" \
  -F "language=pt-BR"
```

Criterio de aprovacao do teste manual real:

- retorno `200 OK`;
- campo `text` presente e nao vazio;
- texto reconhecivel em relacao ao audio real enviado;
- `engine.name` igual a `mlx-whisper`;
- resposta sem token, path local, `.env` ou dado sensivel indevido;
- logs sem audio bruto, transcricao integral, token, `.env` ou path local sensivel.

Esta Spec adia explicitamente para specs futuras:

- diarizacao completa;
- identificacao robusta da voz do professor;
- analise afetiva de voz;
- uso de Gemma 4 12B multimodal como comparativo de ASR, diarizacao ou compreensao vocal;
- correcao contextual por LLM;
- extracao de temas, resumo e organizacao semantica da aula;
- inclusao de outros formatos de entrada, como `.mp3`, `.mp4` ou `.webm`, se houver necessidade real;
- estrategia de upload indireto, storage intermediario, fila ou processamento assincrono para cenarios cloud ou arquivos maiores, sem alterar a finalidade funcional do endpoint.

---

## 18. Criterios de Fechamento Desta Spec

Esta Spec podera passar de `aberta` para `fechada` quando:

- rota e metodo forem aprovados;
- campos de entrada forem aprovados;
- formato de resposta for aprovado;
- erros principais forem aprovados;
- regras de seguranca e logs forem aprovadas;
- autenticacao por token e configuracao externa forem aprovadas;
- documentacao FastAPI esperada for aprovada;
- criterios de teste valido e invalido estiverem aceitos;
- detalhes de implementacao estiverem resolvidos, delegados ao codigo ou explicitamente adiados;
- checklist aplicavel do endpoint estiver extraido da S02;
- pendencias de implementacao estiverem explicitamente visiveis para o plano/tarefas da E02.

---

## 19. Registro de Fechamento

Status atual: `fechada`.

Fechada em: `2026-06-07`.

Motivo do fechamento:

- rota e metodo aprovados;
- campos de entrada aprovados;
- formatos `.wav` e `.m4a` definidos para o MVP;
- motor STT primario definido;
- resposta de sucesso aprovada;
- respostas de erro aprovadas;
- autenticacao por `Bearer token` aprovada;
- configuracao externa aprovada;
- regras de seguranca e logs aprovadas;
- criterios de teste valido e invalido aceitos;
- decisoes futuras explicitamente adiadas.

Emenda localizada em `2026-06-07`:

- a rota foi ajustada de `POST /api/v1/transcriptions` para `POST /transcriptions/v1.0.0`;
- motivo: adocao do padrao do Mindvox em que endpoints de negocio versionados colocam a versao apos o nome do recurso ou servico.

Emenda localizada em `2026-06-08`:

- checklist aplicavel do endpoint incorporado conforme modelo geral da S02;
- itens de contrato ja decididos foram marcados como concluidos;
- itens que dependem de implementacao, testes automatizados, OpenAPI real e demonstracao ficaram pendentes para orientar o plano/tarefas da E02.

Emenda localizada em `2026-06-08` apos auditoria final da T02:

- itens tecnicos dependentes de implementacao foram revalidados contra codigo, testes, OpenAPI, logs e checklist;
- a suite E02 passou com `23` testes;
- a suite geral passou com `28` testes;
- a unica pendencia operacional restante era o commit manual de fechamento por Adalberto.

Emenda localizada em `2026-06-09` antes do commit:

- reconhecido que os testes automatizados da E02 validam o contrato HTTP em modo `contract`, mas nao comprovam transcricao real por STT;
- `mlx-whisper` foi declarado como dependencia opcional no extra `stt`;
- incluido teste manual real bloqueante com audio real de Adalberto antes do commit de fechamento;
- E02 nao deve ser considerada fechada para commit enquanto o teste manual real nao retornar `200 OK` com texto nao vazio e coerente com o audio.

Emenda localizada em `2026-06-09` para instalacao do motor real:

- extra `stt` instalado no ambiente isolado do Mindvox;
- `mlx-whisper` importavel no `.venv` do Mindvox;
- modelo `mlx-community/whisper-large-v3-turbo-fp16` baixado e preservado como motor final de qualidade da E02;
- camada de servico adaptada para compatibilizar `model.safetensors` com o layout esperado pelo `mlx-whisper`;
- camada de servico adaptada para enviar idioma base ao motor real, preservando o idioma regional no contrato publico;
- testes da E02 passaram com `25` testes;
- suite geral passou com `30` testes;
- smoke test tecnico real via API retornou `200 OK` com texto nao vazio, segmentos temporais, `language` igual a `pt-BR`, `engine.name` igual a `mlx-whisper` e `engine.model` igual a `mlx-community/whisper-large-v3-turbo-fp16`;
- este smoke test tecnico nao substitui a prova real humana bloqueante definida na T02.

Emenda localizada em `2026-06-09` para documentacao didatica dos parametros:

- cada campo do `multipart/form-data` da E02 deve possuir descricao didatica propria no Swagger/OpenAPI;
- as descricoes publicas devem estar em ingles, incluir exemplo curto e ser declaradas diretamente no contrato FastAPI por `File(description=...)` ou `Form(description=...)`;
- objetivo: permitir que o usuario compreenda o que preencher sem depender de explicacao externa, conforme orientacao didatica recebida em aula;
- teste de OpenAPI deve validar a presenca dessas descricoes para evitar regressao futura.

Emenda localizada em `2026-06-09` para prova real humana:

- Adalberto executou manualmente `POST /transcriptions/v1.0.0` em modo `real`;
- o servidor retornou `200 OK` para a requisicao real;
- `transcription_id` retornado: `tr_20260609T154710Z_35969e23`;
- `duration_seconds` retornou `3093.6`, aproximadamente `51min34s` de audio;
- `text` retornou transcricao bruta extensa, nao vazia e coerente com aula sobre APIs;
- o texto retornado tinha cerca de `42.998` caracteres e `7.747` palavras;
- `segments` retornou `2067` segmentos temporais;
- `language` retornou `pt-BR`;
- `engine.name` retornou `mlx-whisper`;
- `engine.model` retornou `mlx-community/whisper-large-v3-turbo-fp16`;
- `engine.version` retornou `unknown`;
- a resposta publica analisada nao expos token, `.env`, path local sensivel, cache local ou audio bruto;
- a qualidade foi aprovada como transcricao bruta real para alimentar o endpoint futuro de pos-processamento;
- a prova real humana exigida pela T02 foi executada e registrada antes do commit de fechamento.
