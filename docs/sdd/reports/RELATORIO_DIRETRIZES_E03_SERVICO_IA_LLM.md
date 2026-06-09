# Relatorio Tecnico: Diretrizes para a E03 como Segundo Servico de IA/LLM

## 1. Identificacao

- `Tipo`: Relatorio tecnico orientador
- `Status`: orientador, nao normativo
- `Data`: 2026-06-08
- `Escopo`: consolidar a interpretacao dos requisitos academicos sobre endpoints de IA e orientar a futura E03
- `Documentos relacionados`:
  - `docs/sdd/specs/S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md`
  - `docs/sdd/specs/S02_GOVERNANCA_DAS_SPECS_MINDVOX.md`
  - `docs/sdd/specs/E02_ENDPOINT_TRANSCRIPTIONS.md`
  - `docs/sdd/plans/P02_IMPLEMENTACAO_E02_TRANSCRIPTIONS.md`
  - `docs/sdd/tasks/T02_TAREFAS_IMPLEMENTACAO_E02_TRANSCRIPTIONS.md`

---

## 2. Finalidade

Este relatorio consolida a decisao tecnica sobre como o Mindvox deve interpretar a exigencia academica de possuir pelo menos dois endpoints de Inteligencia Artificial.

O objetivo e evitar perda contextual antes da criacao da E03.

Este relatorio nao cria contrato de endpoint por si so. Conforme a S02, ele deve orientar uma futura Spec de endpoint ou uma emenda de governanca, caso Adalberto aprove a diretriz.

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
- deve ser demonstrado com clareza como servico de transcricao automatica.

### 5.3 Lacuna Academica Restante

Apos a E02, ainda falta um segundo endpoint de IA para atender com seguranca ao criterio academico.

Esse segundo endpoint deve executar uma operacao diferente da E02.

Nao basta criar outra rota de transcricao, pois o enunciado exige servicos que realizem operacoes diferentes.

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

## 7. Escopo Funcional Recomendado para a E03

A E03 deve receber texto de aula ou transcricao e devolver uma analise didatica estruturada.

Nome possivel da Spec:

```text
E03_ENDPOINT_LESSON_NOTES.md
```

Nome alternativo:

```text
E03_ENDPOINT_TRANSCRIPT_ANALYSIS.md
```

Rota possivel:

```text
POST /lesson-notes/v1.0.0
```

Rota alternativa:

```text
POST /transcriptions/analysis/v1.0.0
```

Operacoes possiveis:

- gerar resumo didatico;
- extrair topicos principais;
- listar conceitos-chave;
- apontar duvidas provaveis de estudante;
- gerar glossario inicial;
- sugerir roteiro de revisao;
- classificar o nivel ou tipo do conteudo, se for util.

Recomendacao pragmatica:

- evitar escopo grande demais;
- escolher uma resposta estruturada simples e demonstravel;
- nao implementar agente complexo nesta fase;
- nao implementar memoria, busca, embeddings ou banco na E03, salvo decisao expressa em Spec propria.

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
| `MINDVOX_LLM_MODE` | Define `local`, `provider` ou `contract` |
| `MINDVOX_LLM_PROVIDER` | Define `openai`, `groq`, `anthropic` ou outro provider suportado |
| `MINDVOX_LLM_MODEL` | Define o modelo usado |
| `MINDVOX_LLM_API_KEY` | Chave do provider externo, quando aplicavel |
| `MINDVOX_LLM_BASE_URL` | URL base opcional para providers compativeis |
| `MINDVOX_LLM_TIMEOUT_SECONDS` | Timeout maximo de chamada |
| `MINDVOX_LLM_MAX_INPUT_CHARS` | Limite de entrada textual |

Regras:

- `.env` real deve permanecer fora do Git;
- `.env.example` deve conter nomes e exemplos ficticios;
- nenhuma chave real deve aparecer em testes, README, logs ou mensagens de erro;
- o modo `contract` deve ser explicitamente identificado na resposta.

---

## 11. Contrato de Resposta Recomendado para a E03

Resposta de sucesso recomendada:

```json
{
  "analysis_id": "an_20260608T120000Z_ab12cd34",
  "summary": "Resumo didatico curto.",
  "key_points": [
    "Ponto principal 1",
    "Ponto principal 2"
  ],
  "concepts": [
    {
      "term": "API",
      "definition": "Interface para comunicacao entre sistemas."
    }
  ],
  "study_questions": [
    "Qual problema este endpoint resolve?"
  ],
  "metadata": {
    "source": "transcription",
    "language": "pt-BR"
  },
  "engine": {
    "type": "llm",
    "provider": "contract",
    "model": "contract",
    "version": "unknown"
  }
}
```

Campos importantes:

- `analysis_id`: identificador opaco com prefixo controlado;
- `summary`: resumo didatico;
- `key_points`: topicos principais;
- `concepts`: conceitos e definicoes;
- `study_questions`: perguntas para estudo;
- `metadata`: metadados normalizados;
- `engine`: informacao controlada sobre o motor, sem segredo ou path sensivel.

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
| Texto grande demais | `413 Payload Too Large` ou `422 Unprocessable Entity`, conforme decisao da Spec |
| Token ausente | `401 Unauthorized` |
| Token invalido | `401 Unauthorized` |
| Header malformado | `401 Unauthorized` |
| Provider/modelo indisponivel | `503 Service Unavailable` |
| Timeout de provider | `503 Service Unavailable` ou `504 Gateway Timeout`, conforme decisao da Spec |
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
tests/e03_lesson_notes/
```

Ou, se a Spec adotar outro nome:

```text
tests/e03_transcript_analysis/
```

Testes minimos:

- sucesso em modo `contract`;
- schema completo da resposta;
- autenticacao ausente;
- token invalido;
- header malformado;
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

## 16. Decisao Recomendada

Recomenda-se que a proxima Spec de endpoint seja:

```text
E03_ENDPOINT_LESSON_NOTES.md
```

Com rota inicial:

```text
POST /lesson-notes/v1.0.0
```

Finalidade:

```text
Receber texto de aula ou transcricao e devolver uma analise didatica estruturada usando LLM ou motor substituivel.
```

Essa decisao atende simultaneamente:

- ao requisito academico de dois endpoints de IA;
- ao desenho real do Mindvox;
- ao principio local-first;
- ao risco de execucao em outro computador;
- ao contrato didatico de nao iniciar endpoint sem Spec, Plano e Tarefas.

---

## 17. Pendencias para Governanca

Este relatorio deve alimentar uma emenda futura na S02 ou uma nova regra transversal, se aprovado.

Pontos a converter em governanca:

- todo endpoint que pretenda contar para requisito academico de IA deve declarar expressamente qual operacao de IA executa;
- endpoint operacional nao conta como endpoint de IA;
- modelo instalado ou citado nao conta sem rota de API funcional;
- endpoints de IA devem ter modo de contrato para testes perenes;
- endpoints que dependam de provider externo devem documentar variaveis de ambiente e ausencia de chave real no Git;
- antes de iniciar E03, deve haver Spec, Plano e Tarefas proprias.

---

## 18. Conclusao

A E02 pode ser defendida como primeiro endpoint de IA por executar STT.

Ainda e necessario criar uma E03 para atender com seguranca ao requisito academico de dois endpoints de IA.

A melhor escolha tecnica e academica e uma E03 de analise didatica de transcricoes por LLM ou motor substituivel, mantendo local-first e prevendo provider externo opcional.

Este relatorio deve ser usado como base para a Spec E03, sem substituir a criacao formal da Spec, do Plano e das Tarefas.
