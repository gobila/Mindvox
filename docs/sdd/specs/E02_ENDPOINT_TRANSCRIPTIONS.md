# Spec E02: Endpoint de Transcricoes

## 1. Identificacao

- `ID`: `E02`
- `Tipo`: `Spec de Endpoint`
- `Status`: `fechada`
- `Endpoint`: `POST /transcriptions/v1`
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
/transcriptions/v1
```

Interpretacao:

- `transcriptions` indica o recurso produzido pela operacao.
- `v1` indica a primeira versao estavel do contrato HTTP e fica apos o nome do recurso, conforme o padrao versionado do Mindvox.

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
- formatos de arquivo aceitos;
- resposta de sucesso;
- erros principais;
- esquema de autenticacao por `Bearer token`;
- indicacao de que o audio deve ser arquivo ja gravado;
- indicacao de que streaming, TTS e speech-to-speech estao fora deste endpoint.

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

- a rota `POST /transcriptions/v1` existir;
- a rota exigir `Authorization: Bearer <token>`;
- a API rejeitar requisicao sem token ou com token invalido;
- a documentacao do FastAPI exibir o endpoint corretamente;
- a API aceitar arquivo valido em `multipart/form-data`;
- a API rejeitar requisicao sem arquivo;
- a API rejeitar tipo de arquivo invalido;
- a API rejeitar arquivo com extensao aceita mas conteudo invalido ou corrompido;
- a API rejeitar arquivo acima do limite definido;
- a resposta de sucesso seguir schema estruturado;
- a resposta de sucesso incluir `segments` como lista, mesmo que vazia e sem diarizacao real no MVP;
- erros previsiveis tiverem status HTTP coerente;
- logs nao vazarem dados sensiveis;
- houver teste valido e testes invalidos para ausencia de arquivo, tipo invalido, audio corrompido, token ausente e token invalido;
- Adalberto conseguir explicar o fluxo completo do endpoint.

---

## 15. Exemplos de Teste

### 15.1 Teste Valido

Entrada:

```text
POST /transcriptions/v1
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
POST /transcriptions/v1
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
POST /transcriptions/v1
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
POST /transcriptions/v1
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
POST /transcriptions/v1
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
POST /transcriptions/v1
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

| Item | Status | Justificativa |
| --- | --- | --- |
| Metodo HTTP definido | [x] | `POST` aprovado para envio de audio a transcrever |
| Rota definida | [x] | `/transcriptions/v1` aprovada |
| Padrao de versionamento decidido | [x] | Endpoint de negocio usa versao apos o recurso: `/transcriptions/v1` |
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
| Schema de resposta definido | [ ] | Deve ser materializado na implementacao, provavelmente com modelos Pydantic |
| Erros principais listados | [x] | `422`, `400`, `413`, `401`, `503` e `500` descritos |
| Status codes de erro definidos | [x] | Cada erro previsivel tem status HTTP planejado |
| Mensagens de erro sem vazamento sensivel | [x] | Spec proibe stack trace, caminhos locais, audio integral e configuracoes privadas |
| Metodo HTTP invalido considerado | [ ] | Deve ser testado na implementacao, por exemplo `GET /transcriptions/v1` ou metodo nao suportado |
| Entrada invalida considerada | [x] | Ausencia de arquivo, tipo invalido, audio corrompido, arquivo grande, data e token invalido previstos |
| Necessidade de autenticacao decidida | [x] | Autenticacao obrigatoria por `Bearer token` desde o MVP |
| Necessidade de autorizacao decidida | [x] | Autorizacao fina adiada; token unico do MVP protege o endpoint |
| Dados sensiveis identificados | [x] | Audio, transcricao, metadados academicos, token e configuracoes tratados como sensiveis |
| Regras de nao vazamento descritas | [x] | Regras de seguranca e logs definidas |
| Uso de `.env`, tokens ou configuracao externa definido | [x] | `MINDVOX_API_TOKEN` e `MINDVOX_MAX_UPLOAD_MB` previstos |
| Eventos permitidos em log descritos | [x] | Inicio da requisicao, tamanho, content type, duracao, sucesso/falha e codigo controlado |
| Dados proibidos em log descritos | [x] | Audio bruto, transcricao integral, `Authorization`, tokens, `.env`, paths e dados pessoais desnecessarios |
| Logs existentes do servidor considerados | [x] | Logs do servidor sao insuficientes para todo o E02, mas contam como base operacional |
| Necessidade de logger proprio decidida | [ ] | Deve ser decidida na implementacao da E02, pois ha processamento sensivel e erros de negocio |
| Persistencia de logs decidida | [ ] | Deve ser decidida ou explicitamente adiada durante a implementacao |
| `summary` definido | [x] | `Transcribe audio file` |
| `description` definida | [x] | `Receives a recorded audio file and returns a text transcription with optional class metadata.` |
| Respostas principais aparecem na documentacao | [ ] | Deve ser validado no OpenAPI depois da implementacao |
| Parametros/body aparecem corretamente | [ ] | Deve ser validado no OpenAPI depois da implementacao |
| `/openapi.json` reflete o contrato aprovado | [ ] | Deve ser coberto por teste automatizado |
| Router definido | [ ] | Implementacao real ainda pendente |
| Handler definido com nome explicavel | [ ] | Implementacao real ainda pendente |
| Router registrado no `app` | [ ] | Deve ocorrer apenas quando E02 estiver pronta para nao quebrar a API |
| Endpoint temporario ou exemplo removido | [ ] | `src/routers/services.py` deve ser corrigido antes de registrar o router |
| Dependencias fora do escopo nao sao importadas | [ ] | Deve ser verificado durante implementacao |
| Codigo compila | [ ] | Deve passar em `py_compile` apos implementacao |
| Pasta propria de testes criada | [ ] | Criar pasta dedicada, por exemplo `tests/e02_transcriptions/` |
| README da pasta de testes criado | [ ] | Criar `tests/e02_transcriptions/README.md` |
| README da pasta de testes explica hipoteses verificadas | [ ] | Deve explicar sucesso, autenticacao, validacoes, erros, OpenAPI e limites de seguranca |
| README da pasta de testes explica como executar os testes | [ ] | Deve registrar comando geral e comando especifico da E02 |
| Teste automatizado de sucesso criado | [ ] | Deve cobrir envio valido com mock/stub de contrato ou motor controlado |
| Teste automatizado de erro principal criado | [ ] | Deve cobrir ausencia de arquivo, tipo invalido, audio corrompido, arquivo grande e falha do motor quando aplicavel |
| Teste automatizado de metodo invalido criado | [ ] | Deve cobrir metodo HTTP nao permitido |
| Teste automatizado do OpenAPI criado | [ ] | Deve validar `summary`, `description`, formulario, autenticacao e respostas principais |
| Comando de teste registrado | [ ] | Deve ser registrado no plano/tarefas da E02 |
| Todos os testes passam antes do proximo endpoint | [ ] | Deve bloquear inicio da E03 |
| Comando de execucao local documentado | [ ] | Deve ser documentado para a E02 implementada |
| Exemplo de chamada valida documentado | [x] | Teste valido descrito nesta Spec |
| Exemplo de falha relevante documentado | [x] | Testes invalidos descritos nesta Spec |
| Endpoint explicavel por finalidade, entrada, processamento, saida, erro e teste | [x] | Spec descreve o fluxo completo esperado |
| Limites de escopo claros | [x] | Streaming, TTS, processamento semantico, persistencia, busca e diarizacao final adiados |
| `git status` revisado | [ ] | Executar imediatamente antes do commit de fechamento da E02 |
| `git diff` revisado | [ ] | Executar imediatamente antes do commit de fechamento da E02 |
| Arquivos alterados pertencem ao escopo da E02 ou estao justificados | [ ] | Verificar antes do commit para nao misturar assuntos |
| Nenhum segredo, token, `.env`, path sensivel ou dado privado aparece no diff | [ ] | Verificar antes do commit |
| Nenhum cache, `__pycache__`, temporario ou artefato gerado indevido aparece no diff | [ ] | Verificar antes do commit |
| Testes automatizados da E02 passaram | [ ] | Executar suite da E02 quando existir |
| Testes gerais passaram | [ ] | Executar suite completa antes de fechar E02 |
| Checklist aplicavel da E02 esta todo marcado ou justificado como `N/A` | [ ] | Depende da implementacao e do pre-commit |
| README da pasta de testes esta atualizado | [ ] | Atualizar `tests/e02_transcriptions/README.md` |
| Materiais didaticos externos ao repo foram atualizados | [ ] | Atualizar checklist didatico da E02 no vault, quando aplicavel |
| Mensagem de commit planejada identifica a E02 concluida | [ ] | Definir antes do commit |
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

Esta Spec ainda precisa detalhar na implementacao:

- mecanismo concreto de leitura de configuracao, preferencialmente coerente com Pydantic Settings, `.env`, variaveis de ambiente ou equivalente;
- forma exata de teste automatizado do mock restrito a contrato;
- exemplos de colecao ou requisicao manual em ferramenta como Postman, se isso for util para apresentacao da disciplina.

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

- a rota foi ajustada de `POST /api/v1/transcriptions` para `POST /transcriptions/v1`;
- motivo: adocao do padrao do Mindvox em que endpoints de negocio versionados colocam a versao apos o nome do recurso ou servico.

Emenda localizada em `2026-06-08`:

- checklist aplicavel do endpoint incorporado conforme modelo geral da S02;
- itens de contrato ja decididos foram marcados como concluidos;
- itens que dependem de implementacao, testes automatizados, OpenAPI real e demonstracao ficaram pendentes para orientar o plano/tarefas da E02.
