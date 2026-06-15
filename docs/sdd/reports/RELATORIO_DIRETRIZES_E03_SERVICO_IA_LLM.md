# Relatorio Tecnico: Diretrizes para a E03 como Segundo Servico de IA/LLM

## 1. Identificacao

- `Tipo`: Relatorio tecnico orientador
- `Status`: orientador, nao normativo
- `Data original`: 2026-06-08
- `Atualizacao`: 2026-06-09
- `Escopo`: consolidar a interpretacao dos requisitos academicos sobre endpoints de IA e alinhar a E03 ao estado atual do Mindvox
- `Documentos relacionados`:
  - `docs/sdd/specs/S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md`
  - `docs/sdd/specs/S02_GOVERNANCA_DAS_SPECS_MINDVOX.md`
  - `docs/sdd/specs/E02_ENDPOINT_TRANSCRIPTIONS.md`
  - `docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/plans/P02_IMPLEMENTACAO_E02_TRANSCRIPTIONS.md`
  - `docs/sdd/tasks/T02_TAREFAS_IMPLEMENTACAO_E02_TRANSCRIPTIONS.md`
  - `docs/sdd/reports/RELATORIO_ARQUITETURA_E_ESCOPO_E03_E05.md`
  - `docs/sdd/reports/RELATORIO_BENCHMARK_E03_MODELOS_LLM.md`

---

## 2. Finalidade

Este relatorio consolida a decisao tecnica sobre como o Mindvox deve interpretar a exigencia academica de possuir pelo menos dois endpoints de Inteligencia Artificial.

O objetivo original era evitar perda contextual antes da criacao da E03.

Com a atualizacao de 2026-06-09, este relatorio passa a registrar tambem a evolucao do projeto apos a prova real da E02 e apos a criacao da Spec E03.

Este relatorio nao cria contrato de endpoint por si so. Conforme a S02, ele deve orientar a Spec de endpoint aplicavel ou uma emenda de governanca, caso o autor do projeto aprove a diretriz.

No estado atual do projeto, a Spec E03 ja foi aberta em `E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`. Portanto, sugestoes antigas de nome, rota e contrato devem ser lidas como historico de decisao, nao como alternativas ainda concorrentes.

---

## 3. Texto Oficial Interpretado

O enunciado do trabalho final exige:

- desenvolver uma API funcional;
- disponibilizar pelo menos dois servicos, ou endpoints, de Inteligencia Artificial;
- demonstrar boas praticas de desenvolvimento;
- incluir validacao de dados, tratamento de erros, logs, seguranca e versionamento;
- garantir que os endpoints funcionem com dados validos e invalidos;
- garantir que o codigo execute em outro computador.

O texto oficial nao exige literalmente dois endpoints de LLM.

A formulacao usada pelo professor e mais ampla:

```text
qualquer servico de IA, como classificacao, uso de LLM, uso de agentes, entre outros
```

Interpretacao tecnica:

- LLM e apenas uma das categorias possiveis de servico de IA;
- classificacao, STT, agentes, extracao semantica, resumo e geracao textual tambem podem ser servicos de IA;
- a exigencia principal recai sobre endpoints da API do projeto, nao necessariamente sobre consumo de APIs externas.

---

## 4. O Que Conta como Endpoint de IA

Para fins do trabalho, um endpoint de IA deve ser uma rota da API que:

- receba uma entrada externa via HTTP;
- execute ou acione uma operacao de Inteligencia Artificial;
- devolva uma resposta estruturada;
- possa ser demonstrado funcionalmente;
- possua validacao, erros, logs, seguranca, versionamento e testes.

Um modelo instalado localmente nao basta.

Um modelo so passa a contar para o trabalho quando estiver exposto por um endpoint funcional da Web API.

Exemplo:

- `GET /health`: nao conta como IA; e endpoint operacional.
- `POST /transcriptions/v1.0.0`: conta como IA se acionar STT real ou um modo de contrato claramente identificado para testes e demonstracao do contrato.

---

## 5. Situacao Atual do Mindvox

### 5.1 E01 Health

`GET /health` e um endpoint operacional.

Funcao:

- verificar se a API esta viva;
- demonstrar organizacao inicial, FastAPI, router, testes, documentacao e checklist;
- servir como base didatica e tecnica.

Conclusao:

- nao deve ser apresentado como servico de IA;
- nao deve ser contado entre os dois endpoints de IA exigidos.

### 5.2 E02 Transcriptions

`POST /transcriptions/v1.0.0` recebe audio gravado e devolve transcricao textual.

Funcao de IA:

- STT: speech-to-text;
- processamento de audio por modelo de transcricao;
- preparacao do Mindvox para processamento posterior de aulas.

Conclusao:

- pode ser apresentado como primeiro servico de IA;
- nao e LLM, mas continua sendo endpoint de IA;
- foi validado em prova real humana com transcricao longa, resposta `200 OK`, motor `mlx-whisper` e modelo `mlx-community/whisper-large-v3-turbo-fp16`;
- deve ser demonstrado com clareza como servico de transcricao automatica bruta.

### 5.3 Estado Atual da E03

Apos a E02, a lacuna academica restante foi direcionada para a E03.

A Spec E03 atual define:

- `POST /processed-transcriptions/v1.0.0`;
- pos-processamento de alto nivel;
- entrada por audio ou texto bruto;
- reaproveitamento interno do servico de transcricao quando receber audio;
- saida com texto bruto, texto didatico, temas, termos tecnicos e metadados.

Conclusao:

- a lacuna conceitual de segundo endpoint de IA esta enderecada em Spec;
- a lacuna de implementacao permanece aberta ate a E03 ser codificada, testada e validada por prova real humana;
- nao basta criar outra rota de transcricao, pois o segundo servico deve executar operacao diferente da E02.

---

## 6. Diretriz Recomendada para a E03

A E03 deve ser um endpoint de IA textual baseado em LLM ou motor substituivel equivalente.

Diretriz recomendada:

```text
E02 = IA/STT
E03 = IA/LLM
```

Assim, o Mindvox passa a demonstrar dois tipos diferentes de IA:

- transcricao de fala para texto;
- processamento inteligente de texto transcrito.

Essa escolha e tecnicamente coerente com o produto, pois o Mindvox depende primeiro da transcricao e depois da compreensao pedagogica do conteudo.

---

## 7. Escopo Funcional Atual da E03

A E03 deve receber audio ou transcricao bruta e devolver uma transcricao pos-processada.

Spec atual:

```text
E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md
```

Rota atual:

```text
POST /processed-transcriptions/v1.0.0
```

Operacoes atuais:

- receber `input_type=audio` ou `input_type=raw_text`;
- quando receber audio, usar internamente o servico de transcricao da E02;
- preservar `raw_text` como rastreabilidade do que foi ouvido ou enviado;
- produzir `didactic_text`;
- organizar conteudo por `themes`;
- apontar `technical_terms` normalizados ou provaveis;
- listar `technology_mentions` efetivamente citadas ou fortemente indicadas no bruto;
- registrar `processing_notes` controladas sobre correcoes, incertezas e cuidados;
- devolver metadados e informacao do motor de pos-processamento.

Recomendacao pragmatica:

- evitar escopo grande demais;
- escolher uma resposta estruturada simples e demonstravel;
- nao implementar agente complexo nesta fase;
- nao implementar memoria, busca, embeddings ou banco na E03;
- deixar ingestao em memoria para E04 e recuperacao de informacao para E05.

---

## 8. Arquitetura Recomendada: Local-First com Motor Substituivel

O Mindvox deve continuar local-first, mas a E03 deve prever motor substituivel.

Modos recomendados:

| Modo | Finalidade | Uso permitido |
| --- | --- | --- |
| `local` | Usar modelo local quando disponivel | Desenvolvimento local e demonstracao em maquina preparada |
| `provider` | Usar API externa de LLM quando configurada | Portabilidade, fallback academico e execucao em outro computador |
| `contract` | Retornar resposta controlada para testes | Testes automatizados e demonstracao do contrato HTTP |

Essa arquitetura reduz risco academico.

Motivo:

- local-first preserva a identidade tecnica do Mindvox;
- provider externo aumenta portabilidade;
- contract mode garante testes perenes sem depender de GPU, modelo local ou chave real.

---

## 9. Sobre OpenAI, Groq, Anthropic ou Equivalentes

O enunciado nao obriga usar API externa.

Ainda assim, prever suporte opcional a provider externo e oportuno porque o professor avalia se o codigo executa em outro computador.

Risco do local-only:

- o modelo local pode nao estar instalado;
- a maquina do avaliador pode nao ter hardware adequado;
- dependencias de MLX ou modelos locais podem ser pesadas;
- a demonstracao pode falhar fora do ambiente de desenvolvimento principal.

Beneficio do provider opcional:

- facilita reproducibilidade;
- permite demonstracao com chave de ambiente;
- nao exige instalar modelo local pesado;
- mantem local-first como padrao conceitual, mas nao como gargalo de execucao.

Diretriz:

- nao gravar chave real no codigo;
- documentar variaveis em `.env.example`;
- tratar ausencia de chave como erro controlado ou usar modo `contract`;
- logs nunca devem registrar prompt integral sensivel, resposta integral sensivel, token, chave ou `.env`;
- provider externo deve ser opcional, nao dependencia obrigatoria do MVP local.

---

## 10. Variaveis de Configuracao Sugeridas para a E03

Variaveis possiveis:

| Variavel | Finalidade |
| --- | --- |
| `MINDVOX_POSTPROCESSING_MODE` | Define `contract`, `provider` ou `local` |
| `MINDVOX_LLM_PROVIDER` | Define `openai`, `groq`, `anthropic` ou outro provider suportado |
| `MINDVOX_LLM_MODEL` | Define o modelo usado |
| `MINDVOX_LLM_API_KEY` | Chave do provider externo, quando aplicavel |
| `MINDVOX_LLM_BASE_URL` | URL base opcional para providers compativeis |
| `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` | Allowlist opcional de hostnames externos aceitos em modo `provider`; recomendada e obrigatoria em deploy publico |
| `MINDVOX_LLM_MAX_OUTPUT_TOKENS` | Limite maximo de saida solicitado ao motor textual; padrao local da E03: `20000` |
| `MINDVOX_LLM_TIMEOUT_SECONDS` | Timeout maximo de chamada |
| `MINDVOX_LLAMA_SERVER_CTX_SIZE` | Contexto do `llama-server` local; padrao local da E03: `65536` |
| `MINDVOX_LLAMA_SERVER_PARALLEL` | Slots do `llama-server` local; padrao local da E03: `1` |
| `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS` | Limite de entrada textual; padrao local da E03: `150000` |

Regras:

- `.env` real deve permanecer fora do Git;
- `.env.example` deve conter nomes e exemplos ficticios;
- nenhuma chave real deve aparecer em testes, README, logs ou mensagens de erro;
- chave vazia ou placeholder de exemplo, como `replace-with-provider-key`, deve ser tratado como chave ausente em modo `provider`;
- em modo `provider`, host fora de `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` deve ser rejeitado quando a allowlist estiver configurada;
- em deploy publico, `MINDVOX_PUBLIC_DEPLOYMENT=true` deve exigir host confiavel e docs desabilitados por padrao no app;
- o modo `contract` deve ser explicitamente identificado na resposta;
- em modo `provider`, o conteudo de `raw_text` ou a transcricao gerada a partir de audio sera enviado ao provider externo configurado;
- modo `local` deve ser preferido quando o conteudo nao puder sair da maquina.
- em modo `local`, a decisao tecnica atual e usar contexto `65536`, saida maxima `20000`, timeout `1200s` e `parallel 1`, pois a prioridade da E03 e preservacao semantica de aula de ate aproximadamente duas horas.

---

## 11. Contrato de Resposta Recomendado para a E03

Resposta de sucesso recomendada, alinhada com a Spec E03 atual:

```json
{
  "processed_transcription_id": "ptr_20260609T000000Z_ab12cd34",
  "input_type": "audio",
  "language": "pt-BR",
  "raw_text": "...",
  "didactic_text": "...",
  "themes": [
    {
      "title": "API First",
      "summary": "...",
      "key_points": ["..."]
    }
  ],
  "technical_terms": [
    {
      "term": "REST",
      "normalized_from": ["GRASH"],
      "confidence": "medium"
    }
  ],
  "technology_mentions": [
    {
      "name": "FastAPI",
      "category": "framework",
      "context": "citado como framework Python para criacao de APIs",
      "importance": "high",
      "normalized_from": ["fast api"],
      "confidence": "high",
      "evidence": "..."
    }
  ],
  "processing_notes": [
    {
      "type": "normalization",
      "message": "Correcao ou incerteza registrada sem expor prompt integral."
    }
  ],
  "metadata": {
    "course": "Pos-UFG-T2-Agentes_inteligentes_IA",
    "discipline": "API",
    "class_date": "2026-05-16",
    "class_title": "apifirst_fastapi_dev",
    "session_label": "S02"
  },
  "source": {
    "input_origin": "audio",
    "raw_text_origin": "generated_by_transcription_service",
    "transcription": {
      "transcription_id": "tr_...",
      "duration_seconds": 3093.6,
      "segments_count": 2067,
      "transcription_engine": {
        "name": "mlx-whisper",
        "model": "mlx-community/whisper-large-v3-turbo-fp16",
        "version": "unknown"
      }
    }
  },
  "processing_engine": {
    "name": "contract-processor",
    "model": "contract-mode",
    "version": "contract-mode"
  }
}
```

Campos importantes:

- `processed_transcription_id`: identificador opaco com prefixo controlado;
- `input_type`: indica se a entrada principal foi audio ou texto bruto;
- `raw_text`: texto bruto recebido ou produzido pela transcricao;
- `didactic_text`: texto discursivo, sequencial, logico e didatico, com redundancias semanticas enxugadas;
- `themes`: organizacao tematica da aula;
- `technical_terms`: termos tecnicos normalizados ou sugeridos;
- `technology_mentions`: tecnologias, ferramentas, frameworks, plataformas, bibliotecas, servicos, APIs ou providers citados na aula;
- `processing_notes`: notas controladas sobre correcoes, incertezas e escolhas de processamento;
- `metadata`: metadados normalizados;
- `source`: rastreabilidade da entrada e, quando aplicavel, da transcricao;
- `processing_engine`: informacao controlada sobre o motor, sem segredo ou path sensivel.

---

## 12. Validacoes Minimas Recomendadas

A E03 deve validar:

- presenca de texto de entrada;
- tamanho maximo do texto;
- tipo de entrada;
- idioma, quando informado;
- metadados opcionais;
- formato do token de autenticacao;
- configuracao do motor selecionado.

Erros previsiveis:

| Situacao | Status esperado |
| --- | --- |
| Texto ausente | `422 Unprocessable Entity` |
| Texto vazio | `422 Unprocessable Entity` |
| Texto grande demais | `413 Payload Too Large` |
| Token ausente | `401 Unauthorized` |
| Token invalido | `401 Unauthorized` |
| Header malformado | `401 Unauthorized` |
| Provider/modelo indisponivel | `503 Service Unavailable` |
| Timeout de provider ou servidor local | `504 Gateway Timeout` |
| Erro interno inesperado | `500 Internal Server Error` |

---

## 13. Logs e Seguranca da E03

Dados sensiveis provaveis:

- texto de aula;
- transcricao;
- metadados academicos;
- prompts;
- respostas do LLM;
- chave de API;
- configuracoes internas.

Logs permitidos:

- inicio da requisicao;
- tamanho aproximado da entrada;
- modo usado: `local`, `provider` ou `contract`;
- provider escolhido, sem chave;
- duracao do processamento;
- sucesso ou falha;
- codigo de erro controlado.

Logs proibidos:

- texto integral da transcricao;
- prompt integral;
- resposta integral do LLM;
- chave de API;
- header `Authorization`;
- `.env`;
- paths locais sensiveis;
- dados pessoais desnecessarios.

---

## 14. Testes Minimos Recomendados para a E03

A E03 deve ter pasta propria:

```text
tests/e03_processed_transcriptions/
```

Testes minimos:

- sucesso em modo `contract`;
- schema completo da resposta;
- autenticacao ausente;
- token invalido;
- header malformado;
- entrada principal ausente;
- audio e texto enviados ao mesmo tempo;
- texto ausente;
- texto vazio;
- texto grande demais;
- provider indisponivel;
- erro interno sem vazamento;
- OpenAPI reflete rota, formulario/body, seguranca, sucesso e erros;
- logs/respostas nao vazam token, `.env`, path local, prompt integral ou resposta integral.

README da pasta de testes:

- deve explicar as hipoteses verificadas;
- deve registrar comandos de execucao;
- deve explicar que `contract` nao e resposta real de LLM.

---

## 15. Demonstracao Academica Recomendada

Narrativa sugerida:

1. E01 demonstra saude e organizacao basica da API.
2. E02 demonstra o primeiro servico de IA: transcricao STT.
3. E03 demonstra o segundo servico de IA: processamento textual por LLM ou motor substituivel.

Explicacao para o professor:

- o trabalho exigia dois endpoints de IA, nao necessariamente dois endpoints de LLM;
- STT e um servico de IA diferente de LLM;
- o LLM entra na E03 para transformar a transcricao em material didatico;
- a arquitetura e local-first, mas preparada para provider externo quando necessario;
- chaves e tokens ficam fora do codigo;
- testes usam modo de contrato para serem perenes.

---

## 16. Decisao Atual

A decisao atual e que a Spec E03 seja:

```text
E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md
```

Com rota:

```text
POST /processed-transcriptions/v1.0.0
```

Finalidade:

```text
Receber audio ou transcricao bruta e devolver transcricao pos-processada usando LLM ou motor substituivel.
```

Essa decisao atende simultaneamente:

- ao requisito academico de dois endpoints de IA;
- ao desenho real do Mindvox;
- ao principio local-first;
- ao risco de execucao em outro computador;
- ao contrato didatico de nao iniciar endpoint sem Spec, Plano e Tarefas.
- a arquitetura E03-E05, que reserva memoria e busca para endpoints futuros.

---

## 17. Pendencias para Governanca

Este relatorio ja alimentou a abertura da Spec E03 e deve continuar servindo como documento orientador.

Pontos a converter em governanca:

- todo endpoint que pretenda contar para requisito academico de IA deve declarar expressamente qual operacao de IA executa;
- endpoint operacional nao conta como endpoint de IA;
- modelo instalado ou citado nao conta sem rota de API funcional;
- endpoints de IA devem ter modo de contrato para testes perenes;
- endpoints que dependam de provider externo devem documentar variaveis de ambiente e ausencia de chave real no Git;
- antes de iniciar implementacao de E03, deve haver Spec, Plano e Tarefas proprias;
- antes de fechar E03, deve haver prova real humana, conforme regra ja incorporada a governanca documental.

---

## 18. Conclusao

A E02 pode ser defendida como primeiro endpoint de IA por executar STT real.

A E03 ja foi aberta para atender com seguranca ao requisito academico de dois endpoints de IA.

A melhor escolha tecnica e academica, no estado atual do Mindvox, e uma E03 de pos-processamento de transcricoes por LLM ou motor substituivel, mantendo local-first e prevendo provider externo opcional.

Atualizacao posterior de benchmark:

- o modelo local preferencial da E03 passou a ser `Qwen3.6-35B-A3B-MTP-Q8.gguf`;
- a decisao foi tomada apos comparacao real com Gemma 4 12B Q8 e Qwen 3.6 27B Q8;
- a saida principal da E03 deve ser didatica e semanticamente organizada, removendo apenas redundancia semantica e ruido de fala;
- a resposta publica da E03 deve preservar cinco entregas: `raw_text`, `didactic_text`, `themes`, `technical_terms` e `technology_mentions`;
- `corrected_full_text` quase integral nao deve ser requisito padrao, pois a E02 ja preserva o bruto para conferencia;
- a fundamentacao completa esta em `RELATORIO_BENCHMARK_E03_MODELOS_LLM.md`.

Este relatorio deve ser usado como base interpretativa da Spec E03, sem substituir a criacao formal do Plano P03 e das Tarefas T03.
