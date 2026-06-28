# Spec E03: Endpoint Processed Transcriptions

## 1. Identificacao

- `ID`: `E03`
- `Tipo`: `Spec de Endpoint`
- `Status`: `implementada_em_validacao_real`
- `Endpoint`: `POST /processed-transcriptions/v1.0.0`
- `Escopo`: pos-processamento de alto nivel de audio ou transcricao bruta
- `Estagio`: implementacao automatizada concluida; prova real humana e commit de fechamento pendentes
- `Dependencias normativas`:
  - `S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md`
  - `S02_GOVERNANCA_DAS_SPECS_MINDVOX.md`
  - `E02_ENDPOINT_TRANSCRIPTIONS.md`
- `Documentos orientadores`:
  - `RELATORIO_DIRETRIZES_E03_SERVICO_IA_LLM.md`
  - `RELATORIO_ARQUITETURA_E_ESCOPO_E03_E05.md`
  - `RELATORIO_BENCHMARK_E03_MODELOS_LLM.md`
  - `RELATORIO_SINTESE_E03_CHUNKING_PIPELINE_VAULT.md`
  - `RELATORIO_E03_INTERFACE_STUDY_PACKAGE_E_VAULT_OPCIONAL.md`
  - `RELATORIO_CORRECAO_AUDITORIA_IMPLEMENTACAO_E03.md`
  - `RELATORIO_SEGUNDA_AUDITORIA_IMPLEMENTACAO_E03.md`
  - `RELATORIO_CORRECAO_SEGUNDA_AUDITORIA_IMPLEMENTACAO_E03.md`

---

## 2. Finalidade

O endpoint `POST /processed-transcriptions/v1.0.0` deve receber audio gravado ou transcricao bruta e devolver uma versao pos-processada, mais legivel, organizada e didatica.

Ele existe para transformar a saida bruta da E02 em material de maior utilidade didatica, sem ainda gravar memoria, criar banco vetorial, criar banco relacional ou executar busca.

Na evolucao atual, a E03 tambem deve preparar uma camada humana de uso e leitura: uma pagina de entrada melhor que o Swagger para uso operacional, um `Study Package` como artefato canonico estruturado de saida e uma pagina humana de resultado. Essa camada nao substitui o endpoint HTTP; ela organiza e renderiza os mesmos produtos para usuario humano e prepara o consumo futuro pela E04.

Entregas publicas planejadas:

- `raw_text`: texto bruto recebido ou produzido pela transcricao, preservado como lastro de conferencia;
- `didactic_text`: texto discursivo, sequencial, logico e didatico, sem titulos internos, produzido a partir do bruto com enxugamento de redundancias semanticas, mas sem funcionar como resumo editorial;
- `themes`: organizacao paralela por nucleos semanticos, pronta para orientar a futura ingestao da E04 em memoria relacional e vetorial;
- `technical_terms`: relacao de conceitos tecnicos relevantes, com normalizacao ou correcao provavel quando necessario;
- `technology_mentions`: relacao de tecnologias, frameworks, plataformas, bibliotecas, servicos, ferramentas, APIs e providers citados na aula.

Campo auxiliar:

- `processing_notes`: notas controladas sobre correcoes, incertezas e escolhas de processamento, sem expor prompt integral ou raciocinio interno.

Interpretacao:

- a E02 continua sendo o endpoint de transcricao bruta;
- a E03 deve ser o endpoint de pos-processamento de alto nivel;
- a E03 pode usar internamente o servico de transcricao da E02 quando receber audio;
- a E03 nao deve chamar `POST /transcriptions/v1.0.0` por HTTP dentro do mesmo app;
- a E03 deve chamar servicos internos compartilhados, como a camada de transcricao ja criada.
- a escolha do backend STT pertence a E02 e ao `transcription_service`; a E03 apenas consome o `raw_text` produzido por essa camada quando `input_type=audio`;
- o modo `provider` da E03 e exclusivo do pos-processamento textual por LLM OpenAI-compatible, nao da transcricao de audio.

---

## 3. Papel no MVP

No mapa atual do Mindvox:

```text
E01 - health
E02 - transcricao bruta
E03 - pos-processamento de alto nivel
E04 - ingestao em memoria relacional/vetorial futura
E05 - recuperacao por busca semantica/relacional futura
```

A E03 deve contar como segundo endpoint de IA do trabalho academico, pois realiza processamento inteligente de texto transcrito.

Relacao com a E02:

- E02 = IA/STT, fala para texto;
- E03 = IA textual/LLM ou motor substituivel equivalente, texto bruto para texto processado.

---

## 4. Limites de Escopo

A E03 cobre:

- receber audio gravado ou transcricao bruta;
- se receber audio, transcrever usando internamente o servico de transcricao ja existente;
- produzir texto discursivo didatico, enxuto e sequencialmente logico;
- organizar o conteudo por temas semanticos;
- extrair tecnologias, ferramentas e plataformas citadas;
- corrigir ou normalizar termos tecnicos provaveis;
- devolver resposta estruturada com rastreabilidade para o bruto;
- registrar motor/modo usado no pos-processamento.
- oferecer pagina humana de entrada como camada operacional melhor que Swagger;
- gerar `Study Package` como envelope canonico estruturado da aula processada;
- oferecer pagina humana de saida para leitura elegante dos artefatos;
- preparar `memory_manifest` para consumo futuro pela E04, sem ingerir memoria na E03;
- oferecer exportacao opcional para Obsidian/Student Vault como redundancia local, sem tornar Obsidian dependencia do endpoint.

A E03 nao cobre:

- persistencia definitiva em banco;
- criacao de memoria relacional;
- criacao de memoria vetorial;
- embeddings;
- busca semantica;
- busca relacional;
- recuperacao de informacao;
- frontend completo multiusuario, autenticacao fina de usuarios ou area administrativa geral;
- TTS;
- streaming;
- diarizacao final;
- revisao humana definitiva.
- importacao ou correcao de Vault Obsidian existente.

Esses temas devem ficar para Specs futuras, especialmente E04 e E05.

---

## 5. Contrato HTTP

Metodo:

```text
POST
```

Rota:

```text
/processed-transcriptions/v1.0.0
```

Interpretacao:

- `processed-transcriptions` indica que a resposta principal e uma transcricao processada;
- `v1.0.0` indica a primeira versao estavel do contrato HTTP deste endpoint;
- a rota evita confundir E03 com a E02, que entrega transcricao bruta em `/transcriptions/v1.0.0`.

---

## 6. Entrada

O endpoint deve receber `multipart/form-data`.

Motivo:

- permite enviar arquivo de audio quando o cliente quer fluxo audio -> transcricao -> pos-processamento;
- permite enviar texto bruto colado ou arquivo `.txt` quando o cliente ja possui uma transcricao;
- permite enviar metadados opcionais da aula junto com a entrada principal.

Campos planejados:

| Campo | Tipo | Obrigatorio | Descricao |
| --- | --- | --- | --- |
| `input_type` | Enum/texto | sim | Define o tipo de entrada; deve aparecer no OpenAPI como Enum/lista de selecao no Swagger; valores: `audio`, `raw_text` e alias ergonomico `raw_text_file` para `raw_text` quando houver arquivo `.txt` |
| `audio_file` | arquivo | condicional | Arquivo de audio quando `input_type=audio`; deve ficar vazio quando `input_type=raw_text` |
| `raw_text` | texto | condicional | Transcricao bruta colada quando `input_type=raw_text`; deve ficar vazio quando `input_type=audio` ou quando `raw_text_file` for usado |
| `raw_text_file` | arquivo `.txt` | condicional | Transcricao bruta em arquivo `.txt` quando `input_type=raw_text`; alternativa a `raw_text` para reprocessar transcricoes longas |
| `course` | texto | nao | Curso ou contexto geral |
| `course_id` | texto | nao | Identificador estavel do curso, usado pela interface humana e pelo `Study Package` quando disponivel |
| `course_name` | texto | nao | Nome humano do curso, equivalente mais explicito de `course` em fluxos novos |
| `institution` | texto | nao | Instituicao ou organizacao responsavel pelo curso |
| `discipline` | texto | nao | Disciplina associada |
| `class_number` | texto/inteiro | nao | Numero da aula dentro da disciplina, quando conhecido |
| `class_date` | texto/data ISO | nao | Data da aula, preferencialmente `YYYY-MM-DD` |
| `class_title` | texto | nao | Titulo ou tema da aula |
| `session_number` | texto/inteiro | nao | Numero da sessao dentro da aula, quando houver sessoes |
| `session_label` | texto | nao | Identificador curto da sessao |
| `language` | texto | nao | Idioma esperado; padrao `pt-BR` |
| `processing_profile` | texto | nao | Perfil de processamento; padrao `study_notes` |

Regra de entrada principal:

- se `input_type=audio`, `audio_file` deve existir e `raw_text` e `raw_text_file` devem estar ausentes;
- se `input_type=raw_text`, deve existir exatamente uma entrada textual: `raw_text` colado ou `raw_text_file` em `.txt`;
- quando `input_type=raw_text`, `audio_file` deve estar ausente; se o Swagger enviar placeholder de arquivo vazio, ele deve ser tratado como nao enviado;
- campos textuais opcionais devem iniciar vazios no OpenAPI/Swagger; se cliente antigo ou tela cacheada ainda enviar o valor literal `string` em campo opcional, esse valor deve ser tratado defensivamente como ausente;
- requisicoes sem entrada principal ou com entradas principais conflitantes devem retornar `422 Unprocessable Entity`.
- `course_id`, `course_name` e `institution` sao metadados opcionais do contrato HTTP, mas campos centrais da pagina humana e do `Study Package`;
- em fluxos novos, `course_name` deve ser preferido a `course`; em fluxos legados, `course` pode ser normalizado internamente para `course_name`;
- o curso ativo deve ser persistido pela camada de interface/configuracao do usuario, nao inferido obrigatoriamente a cada chamada isolada do endpoint.

---

## 7. Descricoes Didaticas no OpenAPI

Cada campo do formulario deve possuir descricao didatica com exemplo curto na documentacao interativa.

Descricoes publicas esperadas:

- `input_type` deve ser tipado como `Enum` no OpenAPI, para que o Swagger apresente lista de selecao/dropdown em vez de campo textual livre.
- `input_type`: `Required strict technical selector. Type exactly one lowercase English value: audio or raw_text. In Swagger, raw_text_file is also accepted as a user-friendly alias when uploading a .txt transcript; the backend normalizes it to raw_text. Do not translate these values and do not use accents. Use audio when uploading audio_file. Use raw_text when pasting an existing transcription. Use raw_text_file when uploading the .txt field named raw_text_file. Example: audio for audio upload. Example for pasted text: raw_text. Example for .txt upload in Swagger: raw_text_file.`
- `audio_file`: `Recorded audio file to transcribe before post-processing. Fill this only when input_type is exactly audio. Leave this empty when input_type is raw_text or when uploading raw_text_file. Supported formats are .wav and .m4a. Example: class-2026-06-09.wav.`
- `raw_text`: `Raw transcription text to be post-processed. Fill this only when input_type is exactly raw_text and you want to paste the text directly. For long transcriptions, use raw_text_file instead. This field starts empty by default; leave it empty when uploading raw_text_file. Leave audio_file empty. Example: a rough transcript copied from a previous STT run.`
- `raw_text_file`: `Optional .txt file containing a raw transcription to be post-processed. Use this only when input_type is exactly raw_text, or when the Swagger input_type alias is raw_text_file, and the transcript is too long to paste comfortably in raw_text. Send either raw_text or raw_text_file, not both. Leave raw_text and audio_file empty. Example: e02-transcription.txt.`
- `course`: `Optional name of the course or broader learning context. Example: Postgraduate course at Federal University of Goias.`
- `course_id`: `Optional stable course identifier used by human UI, Study Package and future memory ingestion. Example: ufg_pos_2.`
- `course_name`: `Optional human course name. Prefer this field in new clients. Example: UFG Pos 2.`
- `institution`: `Optional institution or organization responsible for the course. Example: Federal University of Goias.`
- `discipline`: `Optional name of the discipline, subject, or class area. Example: API Engineering for AI.`
- `class_number`: `Optional class number inside the discipline. Example: 1.`
- `class_date`: `Optional date of the class. Leave this empty if there is no date. If filled, use the YYYY-MM-DD format. Example: 2026-06-09.`
- `class_title`: `Optional title or topic of the class. Example: API First and FastAPI.`
- `session_number`: `Optional session number inside the class. Example: 4.`
- `session_label`: `Optional short identifier for the recording or class session. Example: S02.`
- `language`: `Expected language of the source content. For Brazilian Portuguese, use pt-BR. Example: pt-BR.`
- `processing_profile`: `Post-processing profile to apply. Type exactly study_notes or leave the default value unchanged. Example: study_notes.`

---

## 8. Validacoes

Validacoes minimas:

- `input_type` deve ser `audio` ou `raw_text`, em ingles, minusculo e sem acento;
- por ergonomia do Swagger, `input_type=raw_text_file` deve ser aceito como alias de `raw_text` quando o usuario estiver anexando `raw_text_file`;
- `audio_file` deve existir quando `input_type=audio`;
- `raw_text` ou `raw_text_file` deve existir e nao pode ser vazio quando `input_type=raw_text`;
- `raw_text` e `raw_text_file` nao devem ser enviados juntos;
- defesa de compatibilidade: valor literal `string` em campo textual opcional deve ser tratado como ausente, para evitar que cliente antigo ou Swagger cacheado transforme placeholder visual em dado real;
- `audio_file` nao deve ser enviado junto com `raw_text` ou `raw_text_file`;
- `raw_text_file` deve usar extensao `.txt` e conteudo UTF-8;
- `raw_text` nao deve exceder o limite configurado por `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS`;
- `course`, quando informado, nao deve exceder `160` caracteres;
- `course_id`, quando informado, deve ser slug curto e nao deve exceder `80` caracteres;
- `course_name`, quando informado, nao deve exceder `160` caracteres;
- `institution`, quando informado, nao deve exceder `160` caracteres;
- `discipline`, quando informado, nao deve exceder `120` caracteres;
- `class_number`, quando informado, deve ser simples e curto;
- `class_title`, quando informado, nao deve exceder `200` caracteres;
- `session_number`, quando informado, deve ser simples e curto;
- arquivo de audio deve seguir as mesmas extensoes e validacoes basicas da E02: `.wav` e `.m4a`;
- `class_date`, quando informado, deve usar `YYYY-MM-DD`;
- `session_label`, quando informado, deve ser simples e curto;
- `language`, quando informado, deve usar formato simples, como `pt-BR`;
- `processing_profile`, quando informado, deve usar valor aceito.

Limite inicial do MVP:

```text
MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS=150000
```

Configuracao local padrao do LLM da E03:

```text
MINDVOX_LLM_MAX_OUTPUT_TOKENS=20000
MINDVOX_LLM_TIMEOUT_SECONDS=1200
MINDVOX_LLAMA_SERVER_CTX_SIZE=65536
MINDVOX_LLAMA_SERVER_PARALLEL=1
```

Essa configuracao foi definida para o uso local com `Qwen3.6-35B-A3B-MTP-Q8.gguf`,
considerando aula de ate aproximadamente duas horas, preservacao semantica alta
e uma chamada longa por vez. A janela maxima declarada pelo GGUF local e
`262144` tokens; o contexto operacional `65536` fica abaixo desse limite e cobre
entrada, manual operacional, schema e saida maxima de `20000` tokens com folga
pragmatica.

Interpretacao:

- o limite inicial permite processar transcricoes reais longas semelhantes ao teste da E02;
- entradas acima do limite duro configurado devem retornar `413 Payload Too Large`;
- entradas longas abaixo desse limite podem usar o pipeline interno de chunking quando `MINDVOX_POSTPROCESSING_CHUNKING_MODE=tfidf`;
- o valor deve ser configuravel pela instalacao, sem alterar o contrato HTTP.

Perfis planejados para o MVP:

```text
study_notes
```

Perfis futuros possiveis, mas fora do MVP:

```text
technical_review
exam_review
executive_summary
```

---

## 9. Processamento

Fluxo quando `input_type=audio`:

1. autenticar requisicao;
2. validar metadados e arquivo;
3. chamar internamente o servico de transcricao usado pela E02;
4. salvar automaticamente a transcricao bruta gerada como artefatos locais da E02: JSON tecnico em `outputs/transcriptions/` ou `MINDVOX_TRANSCRIPTION_OUTPUT_DIR`, e TXT humano em `outputs/human/transcriptions/` ou `MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR`;
5. registrar a transcricao bruta gerada em fila local de pos-processamento da E03;
6. obter `raw_text`, `segments`, `duration_seconds` e `transcription_engine`;
7. enviar `raw_text` para o servico de pos-processamento;
8. se o pos-processamento falhar por indisponibilidade, timeout ou saida invalida do motor, manter o item na fila para retry automatico;
9. se o pos-processamento concluir, salvar artefato local processado e marcar o item da fila como concluido;
10. devolver resposta estruturada com transcricao bruta e transcricao processada.

Fluxo quando `input_type=raw_text`:

1. autenticar requisicao;
2. validar metadados;
3. aceitar exatamente uma fonte textual: `raw_text` colado ou `raw_text_file` em `.txt`;
4. decodificar `raw_text_file` em UTF-8 quando usado;
5. enviar o texto bruto diretamente para o servico de pos-processamento;
6. devolver resposta estruturada com transcricao bruta fornecida e transcricao processada.

Regra arquitetural:

- E03 nao chama E02 por HTTP;
- E03 reaproveita servicos internos;
- o router da E03 nao deve conter a logica completa de transcricao nem de LLM;
- a logica deve ficar em camada de servico.

### 9.1 Estrategia Interna Para Transcricoes Longas

A E03 deve preservar o fluxo simples para textos curtos, mas deve usar pipeline
interno de estabilizacao quando a transcricao for longa o bastante para elevar
risco de resumo editorial, perda semantica ou erro 500.

Fluxo curto:

```text
raw_text
  -> postprocessing_service
  -> chamada unica ao motor textual
  -> validacao de cobertura
  -> resposta E03
```

Fluxo longo configuravel:

```text
raw_text (+ segmentos/timestamps quando disponiveis)
  -> pre-auditoria lexical da transcricao bruta
  -> raw_text_for_qwen com normalizacoes canonicas controladas
  -> chunking TF-IDF em memoria
  -> Qwen/E03 chunk por chunk
  -> merge canonico deterministico
  -> auditoria final dos artefatos semanticos
  -> resposta E03
```

Regra de ativacao:

- o pipeline longo deve ser controlado por configuracao;
- o default seguro inicial deve permitir desligar o pipeline sem alterar o
  contrato HTTP;
- entradas abaixo do limite configurado continuam podendo usar o fluxo de
  chamada unica;
- entradas longas devem preferir chunking interno quando
  `MINDVOX_POSTPROCESSING_CHUNKING_MODE=tfidf`.

### 9.2 Pre-auditoria Antes do LLM

A pre-auditoria existe para reduzir ruido lexical antes que o texto seja entregue
ao modelo inferencial.

A etapa deve:

- detectar siglas raras e grafias suspeitas no bruto;
- aplicar normalizacoes canonicas conhecidas quando houver regra segura;
- preservar integralmente o `raw_text` original como lastro publico;
- produzir internamente um texto derivado para o motor textual;
- registrar decisoes em `processing_notes` ou metadado operacional interno;
- quando houver audio/timestamps disponiveis, poder evoluir para clipes e
  re-transcricao pontual.

Substituicoes canonicas sistemicas ja validadas em bancada:

| Forma suspeita | Forma canonica |
| --- | --- |
| `CIGA` | `SIGAA` |
| `UFNDE` | `FNDE` |
| `IAC` | `IaC` |
| `ICTI` | `TI` |
| `EPT` | `ChatGPT` |
| `GROC` | `Groq` |

Essas regras nao sao ancoras privadas de uma unica transcricao. Elas compoem a
politica sistemica da pre-auditoria e devem permanecer rastreaveis.

### 9.3 Contexto de Pre-auditoria no Prompt

Quando o texto entregue ao motor textual ja tiver passado por pre-auditoria, o
prompt deve informar isso ao modelo em bloco delimitado de metadado operacional.

Esse bloco deve declarar:

- que a pre-auditoria foi executada;
- quantas suspeitas foram analisadas;
- quais substituicoes canonicas foram aplicadas;
- se ainda existem termos suspeitos remanescentes.

Regra semantica:

- se nao houver suspeitas remanescentes, o modelo deve tratar o corpo da
  transcricao como a melhor evidencia textual disponivel e nao deve criar novas
  incertezas por plausibilidade;
- se houver suspeitas remanescentes, elas nao devem ser promovidas para
  `didactic_text`, `themes`, `technical_terms` ou `technology_mentions` sem
  evidencia semantica independente no corpo da transcricao;
- suspeitas remanescentes podem aparecer em `processing_notes`, de forma curta e
  controlada.

### 9.4 Chunking, Merge Canonico e Auditoria Final

O chunking interno da E03 deve ocorrer em memoria, sem banco vetorial, e deve
usar inicialmente estrategia TF-IDF. O objetivo e reduzir a unidade de trabalho
do LLM, nao criar memoria persistente.

O merge canonico deve:

- recompor `didactic_text` em ordem de chunks;
- manter prosa didatica sequencial com paragrafos;
- impedir headings artificiais e listas editoriais indevidas no `didactic_text`;
- deduplicar `themes`, `technical_terms` e `technology_mentions`;
- preservar rastreabilidade por chunk em `processing_notes`;
- manter `raw_text` publico como o bruto original recebido ou transcrito.

A auditoria final deve examinar os artefatos semanticos entregaveis:

- `didactic_text`;
- `themes`;
- `technical_terms`;
- `technology_mentions`.

`processing_notes` sao rastreabilidade operacional e nao devem, por si so, gerar
alarme automatico de sigla rara ou conteudo semantico.

### 9.5 Pagina Humana de Entrada

A E03 deve evoluir para possuir uma pagina humana de entrada, distinta do Swagger.

O Swagger permanece como:

```text
documentacao tecnica e console de teste da API
```

A pagina humana de entrada deve ser:

```text
interface operacional para desenvolvedor aprendiz e usuario final
```

Requisitos da pagina:

- aceitar `audio_file`, `raw_text` colado ou `raw_text_file`;
- renderizar `raw_text` como area ampla de texto, nao como campo de linha unica;
- permitir preencher metadados de curso, instituicao, disciplina, professor, aula, data e sessao;
- manter curso ativo persistente ate mudanca explicita do usuario;
- oferecer seletor/lista flutuante de cursos ja cadastrados;
- em modo local/dev, poder receber metadados e transcrito preparados a partir de `_captura-rapida.md` de um Vault Obsidian;
- nao depender de Obsidian para funcionar;
- nao reabrir ou destruir estado de tela ja preparado pelo usuario aprendiz.

Fluxo local/dev com Obsidian:

```text
Student Vault/00_Inbox/_captura-rapida.md
  -> propriedades da nota
  -> sessao ativa
  -> transcrito colado na sessao
  -> script extrai a sessao e gera `.txt` em `inputs/e03_raw_texts/`
  -> script gera metadados auxiliares
  -> pagina humana da E03 recebe esses dados de modo visivel
```

Esse fluxo e opcional e local. Usuarios externos devem poder usar a pagina humana sem Vault.

### 9.6 Study Package e Pagina Humana de Saida

A E03 deve produzir um artefato canonico estruturado chamado `Study Package`.

O `Study Package` nao substitui as cinco entregas publicas; ele as envolve e organiza com metadados, rastreabilidade, auditoria e destinos futuros.

Estrutura conceitual:

```text
study_package
  metadata
  source
  raw_transcription
  didactic_text
  themes
  technical_terms
  technology_mentions
  operational_anchors
  concept_candidates
  audit_report
  memory_manifest
  export_targets
```

Regras:

- `metadata` deve incluir `course_id`, `course_name`, `institution`, `discipline`, `professor`, `class_number`, `class_date`, `class_title`, `session_number` e `session_label` quando disponiveis;
- `raw_transcription` deve preservar o bruto ou apontar para o artefato bruto salvo;
- `didactic_text`, `themes`, `technical_terms` e `technology_mentions` devem reutilizar as entregas da E03;
- `operational_anchors` deve separar URLs, prazos, trabalhos, entregas, eventos, contatos, canais e documentos institucionais;
- `concept_candidates` deve listar conceitos candidatos a notas atomicas futuras;
- `audit_report` deve registrar cobertura, suspeitas, retries, chunks, quarentena e rastreabilidade;
- `memory_manifest` deve preparar o consumo futuro pela E04;
- `export_targets` deve listar caminhos ou destinos opcionais, incluindo Obsidian quando ativado.

A pagina humana de saida deve renderizar o `Study Package` em nichos claros:

```text
Visao geral
Texto didatico
Temas
Conceitos candidatos
Termos tecnicos
Tecnologias citadas
Ancoras operacionais
Bruto auditavel
Auditoria
Exportacoes
```

Ao final do processamento iniciado pela pagina humana, o resultado deve ser exibido automaticamente, preferencialmente em modal, drawer, janela flutuante ou pagina de resultado aberta pelo proprio fluxo.

### 9.7 Relacao Com E04 e Obsidian Opcional

A fronteira correta entre E03 e E04 e:

```text
E03
  -> produz Study Package e memory_manifest

E04
  -> ingere, persiste, relaciona e disponibiliza buscas
```

A E03 nao deve gravar memoria relacional ou vetorial. Ela deve preparar os dados para que a E04 possa:

- gravar em SQLite dados como curso, disciplina, aula, sessao, professor, datas, temas, termos, tecnologias, links, prazos, entregas, eventos, contatos e documentos;
- inserir em campo vetorial `didactic_text`, chunks didaticos, resumos, conceitos candidatos e trechos relevantes;
- preservar relacoes entre origem, aula, sessao, chunk, auditoria e artefatos.

O SQLite e a memoria relacional escolhida para o Mindvox. Obsidian nao e banco relacional principal.

O Obsidian deve ser opcao local de exportacao e redundancia positiva:

- Mindvox deve funcionar sem Obsidian;
- se o usuario ativar Obsidian, a primeira versao deve criar um novo Student Vault deterministicamente;
- a primeira versao nao deve importar, selecionar, corrigir ou validar Vault existente;
- o Vault criado deve seguir contrato Student Vault;
- o exportador deve projetar o `Study Package` nos nichos padronizados do Vault criado;
- o `course_id`/`course_name` deve resolver o curso ativo e, quando Obsidian estiver ativado, o `vault_path` correspondente.

---

## 10. Motor de Pos-processamento

A E03 deve prever motor substituivel.

Modos planejados:

| Modo | Finalidade | Uso permitido |
| --- | --- | --- |
| `auto` | Atrelar o modo de E03 ao modo de transcricao | Padrao recomendado: `contract` quando STT estiver em `contract`; `local` quando STT estiver em `real` |
| `contract` | Retornar resposta controlada | Testes automatizados e demonstracao do contrato |
| `provider` | Usar provider externo de LLM quando configurado | Pos-processamento real demonstravel |
| `local` | Usar servidor local OpenAI-compatible, como `llama-server` | Pos-processamento real em maquina preparada |

Fronteira obrigatoria com STT:

- os modos desta secao governam apenas o motor textual da E03;
- `MINDVOX_POSTPROCESSING_MODE=provider` nao significa STT remoto;
- em modo `provider`, a E03 envia texto bruto ao provider LLM configurado para gerar `didactic_text`, `themes`, `technical_terms`, `technology_mentions` e `processing_notes`;
- quando a entrada da E03 for audio, a transcricao continua sendo responsabilidade interna da E02, via `transcription_service`;
- se a E02 evoluir para backends STT multiplataforma, como selecao automatica entre `mlx-whisper` em macOS Apple Silicon e `openai-whisper` em Windows/Linux, a E03 deve herdar essa evolucao sem alterar o contrato de pos-processamento;
- um eventual STT remoto/provider futuro deve ser especificado na E02 ou em Spec propria, com variavel e contrato separados do `MINDVOX_POSTPROCESSING_MODE`.

Variaveis planejadas:

| Variavel | Finalidade |
| --- | --- |
| `MINDVOX_POSTPROCESSING_MODE` | Define `auto`, `contract`, `provider` ou `local`; padrao recomendado: `auto` |
| `MINDVOX_LLM_PROVIDER` | Define provider externo, quando aplicavel |
| `MINDVOX_LLM_MODEL` | Define modelo textual |
| `MINDVOX_LLM_API_KEY` | Chave externa, quando aplicavel |
| `MINDVOX_LLM_BASE_URL` | URL base opcional |
| `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` | Allowlist opcional de hostnames externos aceitos em modo `provider`; obrigatoria em exposicao publica com provider |
| `MINDVOX_LLM_MAX_OUTPUT_TOKENS` | Limite maximo de tokens solicitados ao motor LLM |
| `MINDVOX_LLM_TIMEOUT_SECONDS` | Timeout maximo |
| `MINDVOX_LOCAL_LLM_AUTOSTART` | Controla se o app tenta iniciar `llama-server` automaticamente em modo `local` |
| `MINDVOX_LLAMA_SERVER_PATH` | Caminho opcional do binario `llama-server` |
| `MINDVOX_LOCAL_LLM_MODEL_PATH` | Caminho opcional do arquivo GGUF local |
| `MINDVOX_LLAMA_SERVER_CTX_SIZE` | Contexto usado ao iniciar `llama-server` automaticamente |
| `MINDVOX_LLAMA_SERVER_GPU_LAYERS` | Quantidade de camadas GPU enviada ao `llama-server` automatico |
| `MINDVOX_LLAMA_SERVER_PARALLEL` | Quantidade de slots do `llama-server` automatico; padrao local da E03 deve ser `1` |
| `MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS` | Tempo maximo para o `llama-server` automatico ficar pronto |
| `MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR` | Diretorio local de artefatos processados da E03 |
| `MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR` | Diretorio local do Markdown humano processado da E03 |
| `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_ENABLED` | Liga ou desliga a fila local de retry da E03 |
| `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS` | Intervalo de retry automatico dos jobs pendentes da E03 |
| `MINDVOX_TRANSCRIPTION_OUTPUT_DIR` | Diretorio local do JSON tecnico da transcricao bruta herdada da E02 |
| `MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR` | Diretorio local do TXT humano da transcricao bruta herdada da E02 |
| `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS` | Limite maximo de texto bruto; padrao local do MVP: `150000`, definido para aula de ate aproximadamente duas horas com margem pragmatica |
| `MINDVOX_POSTPROCESSING_CHUNKING_MODE` | Liga o pipeline longo interno; no perfil `dev` padrao fica `tfidf`; `off` preserva chamada unica para diagnostico; `tfidf` ativa pre-auditoria, chunking, merge canonico e auditoria final |
| `MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS` | Tamanho minimo para acionar o pipeline longo quando `CHUNKING_MODE=tfidf`; padrao inicial: `20000` |
| `MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS` | Tamanho alvo aproximado de cada chunk interno; padrao inicial: `5000` |
| `MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED` | Liga a pre-auditoria lexical sistemica antes do motor textual |
| `MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED` | Liga a auditoria final deterministica dos artefatos semanticos depois do merge |
| `MINDVOX_PUBLIC_DEPLOYMENT` | Ativa endurecimento para exposicao publica |
| `MINDVOX_ENABLE_DOCS` | Controla exposicao de `/docs`, `/redoc` e `/openapi.json` |
| `MINDVOX_TRUSTED_HOSTS` | Hosts aceitos pelo app quando houver exposicao publica |
| `MINDVOX_RUNTIME_PROFILE` | Perfil operacional exibido no Swagger: `dev`, `contract` ou `prod`; normalmente inferido ou definido pelos perfis de inicializacao |

Perfis operacionais canonicos:

| Perfil | Comando local curto | Efeito |
| --- | --- | --- |
| desenvolvimento real local | `fastapi dev` dentro de `src` ou `uv run fastapi dev src/main.py` na raiz | Usa `MINDVOX_PUBLIC_DEPLOYMENT=false`, `MINDVOX_TRANSCRIPTION_MODE=real`, `MINDVOX_POSTPROCESSING_MODE=auto`, `MINDVOX_POSTPROCESSING_CHUNKING_MODE=tfidf`, token local `dev-token` quando nenhum token privado estiver configurado, STT real, Llama local automatico e pipeline longo da E03 ativo |
| contrato | `fastapi dev contract` dentro de `src` ou `uv run fastapi dev src/contract` na raiz | Forca `MINDVOX_TRANSCRIPTION_MODE=contract`, resolve E03 como `contract`, nao inicia `llama-server` e preserva Bearer token local `dev-token` para testar endpoints protegidos |
| producao publica | `fastapi run prod` dentro de `src` ou `uv run fastapi run src/prod` na raiz | Liga `MINDVOX_PUBLIC_DEPLOYMENT=true`, desabilita docs por padrao, bloqueia `dev-token`, exige `MINDVOX_TRUSTED_HOSTS`, exige token forte externo e nao inicia Llama local |

Regras:

- nenhuma chave real deve entrar no codigo, README, logs ou testes;
- o Swagger/OpenAPI deve informar no cabecalho qual perfil esta ativo, usando a formula `Active startup profile: dev`, `contract` ou `prod`;
- ausencia de provider configurado deve gerar erro controlado em modo `provider`;
- modo `contract` deve ser explicitamente identificado na resposta;
- texto bruto acima do limite configurado deve gerar erro controlado;
- timeout do provider externo ou servidor local deve gerar erro controlado proprio;
- modo `provider` deve aceitar apenas URL externa `https`, nao local, loopback ou privada;
- em modo `provider`, hostnames devem ser resolvidos e rejeitados se qualquer endereco resolvido for local, privado, loopback, link-local, reservado, multicast ou indefinido;
- em modo `provider`, se `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` estiver configurado, o hostname de `MINDVOX_LLM_BASE_URL` deve estar nessa allowlist;
- em exposicao publica com `MINDVOX_PUBLIC_DEPLOYMENT=true`, modo `provider` deve exigir allowlist de host por `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS`;
- modo `local` deve aceitar apenas endpoint local, loopback, privado ou equivalente operacional local, como `host.docker.internal`;
- modo `local` com `MINDVOX_LOCAL_LLM_AUTOSTART=true` deve tentar iniciar `llama-server` automaticamente no startup da aplicacao;
- em modo `contract`, a aplicacao nao deve tentar iniciar `llama-server`;
- se o modo `local` exigir autostart e o binario, modelo, porta ou prontidao do servidor falhar, a inicializacao deve falhar com mensagem clara no terminal, sem erro silencioso;
- quando `input_type=audio` gerar transcricao bruta dentro da E03, a transcricao deve entrar em fila local antes do pos-processamento;
- se o pos-processamento falhar apos a transcricao bruta ter sido gerada, o item deve permanecer pendente para retry automatico, sem exigir que o usuario selecione novamente o audio;
- se o retry posterior concluir, a resposta processada deve salvar JSON tecnico em `MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR` e Markdown humano em `MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR`;
- `MINDVOX_LLM_MAX_OUTPUT_TOKENS` deve ser enviado ao motor LLM para reduzir custo e respostas excessivas;
- o cliente LLM deve limitar a quantidade de bytes lidos da resposta antes de parsear JSON;
- o script interno de benchmark deve aplicar limite equivalente de leitura da resposta;
- `processing_engine.name` deve sanitizar o nome do provider antes de expor resposta publica;
- upload de audio deve ser lido em blocos com rejeicao imediata ao exceder `MINDVOX_MAX_UPLOAD_MB`, sem exigir leitura integral previa do arquivo;
- logs nao devem registrar prompt integral, transcricao integral, resposta integral, token, chave ou `.env`.

### 10.1 Modelo Local Preferencial para o Motor Real

A E03 deve ser implementada de modo independente do modelo especifico.

A camada de pos-processamento deve conversar com um servidor compativel com a API OpenAI, especialmente `llama-server`, usando `MINDVOX_LLM_BASE_URL` e `MINDVOX_LLM_MODEL`.

Quando a E03 estiver em modo `local` e `MINDVOX_LOCAL_LLM_AUTOSTART=true`, a aplicacao deve tentar iniciar o `llama-server` automaticamente no ciclo de vida de startup. A implementacao deve:

- reaproveitar servidor local ja ativo se `/v1/models` responder corretamente;
- localizar o binario pelo `PATH`, por `MINDVOX_LLAMA_SERVER_PATH` ou por caminho local padrao documentado;
- localizar o modelo por `MINDVOX_LOCAL_LLM_MODEL_PATH` ou por caminho local padrao documentado;
- iniciar o processo sem shell, com lista de argumentos, evitando injecao de comando;
- aguardar prontidao por `MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS`;
- falhar a inicializacao com mensagem clara se o motor local nao puder ficar pronto;
- nao iniciar `llama-server` em modo `contract`.

Em modo `local`, o cliente OpenAI-compatible deve enviar `chat_template_kwargs.enable_thinking=false` ao `llama-server`. Essa regra operacional evita que modelos Qwen consumam o limite de saida com `reasoning_content` e deixem `content` vazio; a E03 exige JSON final validavel em `content`.

Com base no benchmark real registrado em `RELATORIO_BENCHMARK_E03_MODELOS_LLM.md`, o modelo local preferencial da E03 passa a ser:

```text
Qwen3.6-35B-A3B-MTP-Q8.gguf
```

Nome operacional recomendado:

```text
qwen35a3b-q8
```

Resultado resumido da prova comparativa:

| Modelo | Status | Tempo total | Temas | Termos tecnicos |
| --- | --- | ---: | ---: | ---: |
| `Gemma 4 12B Q8` | passou | `77,26s` | `4` | `8` |
| `Qwen3.6-27B-MTP-Q8_0.gguf` | passou | `188,46s` | `5` | `8` |
| `Qwen3.6-35B-A3B-MTP-Q8.gguf` | passou | `55,83s` | `6` | `10` |

Decisao atual:

- `Qwen3.6-35B-A3B-MTP-Q8.gguf` e o candidato local preferencial para a E03;
- a escolha se baseia em teste real com transcricao bruta longa produzida pela E02;
- o modelo deve continuar substituivel por configuracao;
- a E03 nao deve acoplar o contrato HTTP ao path local do modelo;
- a implementacao deve permitir trocar o modelo por `MINDVOX_LLM_BASE_URL` e `MINDVOX_LLM_MODEL`.

Consequencia:

- `Gemma 4 12B Q8` permanece como candidato alternativo;
- `Qwen3.6-27B-MTP-Q8_0.gguf` permanece como baseline historico;
- nenhum deles deve substituir o preferencial sem nova prova real demonstravel.

### 10.2 Cinco Entregas Publicas da E03

A E03 deve entregar pos-processamento semantico enxuto, nao uma segunda transcricao quase integral.

O contrato publico da E03 deve ter cinco entregas:

1. `raw_text`: lastro bruto para conferencia.
2. `didactic_text`: texto discursivo continuo, sequencial, logico e didatico.
3. `themes`: lista estruturada de temas semanticos.
4. `technical_terms`: lista de conceitos tecnicos relevantes, normalizados ou corrigidos.
5. `technology_mentions`: lista de tecnologias, ferramentas, frameworks, plataformas, bibliotecas, servicos, APIs e providers citados na aula.

Entre essas entregas, `didactic_text`, `themes`, `technical_terms` e `technology_mentions` sao produtos processados. `raw_text` nao e reprocessamento: e o lastro bruto que permite conferencia e auditoria.

Decisao:

- `raw_text` deve permanecer preservado para rastreabilidade e conferencia;
- `raw_text` deve ser retornado integralmente no MVP, salvo erro por limite de tamanho;
- `didactic_text` deve ser a versao discursiva pos-processada, organizada e didatica, nao um resumo breve;
- `didactic_text` deve formar um corpo textual fluido, sem titulos internos, com progressao logica entre as ideias;
- `didactic_text` deve conservar a quase totalidade dos nucleos semanticos relevantes da aula, removendo apenas redundancias semanticas, hesitacoes, falsos comecos, ruido de fala e repeticoes que nao acrescentam informacao nova;
- `didactic_text` deve preservar projetos citados, cases profissionais, contribuicoes relevantes de alunos, dores reais de implementacao, exemplos, metaforas, arquiteturas, tecnologias e decisoes metodologicas quando esses elementos trouxerem informacao semantica nova;
- para transcricoes longas, a implementacao deve aplicar freio automatico contra resumo excessivo: se a saida do LLM for estruturalmente valida, mas pequena demais, pobre em temas ou omitir ancoras semanticas protegidas extraidas do bruto, a E03 deve rejeitar a primeira saida, tentar uma segunda geracao com instrucao mais rigorosa de preservacao e, se ainda falhar, retornar erro controlado;
- quando uma saida estruturalmente valida for rejeitada pela auditoria de cobertura semantica, a E03 deve salvar a saida rejeitada em quarentena tecnica e humana (`outputs/processed_transcriptions/rejected/` e `outputs/human/processed_transcriptions/rejected/`), incluindo motivo, tentativa, metricas, excerto do bruto, `runtime_snapshot` e payload rejeitado para auditoria humana;
- rejeicoes finais de qualidade semantica devem retornar `502 Bad Gateway` com `error_code=postprocessing_quality_rejected`, `retry_hint`, `attempt`, `max_attempts`, `will_retry` e caminhos dos artefatos rejeitados, evitando `500` generico sem material auditavel;
- jobs de audio enfileirados devem ter limite configuravel de tentativas por `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS`; ao atingir o limite, o job deve sair de `pending` e ir para `queue/failed/`, encerrando retries automaticos e preservando o diagnostico;
- quando o fluxo longo usar chunking TF-IDF e merge canonico, a validacao final deve usar politica propria: a regua minima de tamanho do `didactic_text` pode ser menor que a do fluxo monolitico, porque o texto ja foi saneado por chunks; tamanho minimo e quantidade minima de temas continuam bloqueantes, mas ancoras protegidas ausentes devem gerar nota `semantic_anchor_audit` em `processing_notes`, nao erro terminal, pois a extracao automatica de ancoras ainda e heuristica;
- a verificacao de ancoras protegidas nao deve usar `processing_notes` como evidencia de cobertura semantica, pois notas operacionais sao rastreabilidade interna, nao conteudo estudantil entregue;
- a validacao automatica de cobertura deve tratar como ancoras semanticas protegidas itens de alto valor como projetos, empresas, instituicoes, tecnologias, arquiteturas, dores reais de implementacao, cases e autoria de contribuicoes relevantes de alunos, pois esses elementos nao podem ser removidos por um filtro editorial;
- `themes` deve conter os nucleos tematicos principais em forma estruturada;
- `themes` deve organizar os conteudos por semantica, preparando a futura E04 para ingestao em memoria relacional e vetorial;
- `themes` deve manter ordem logica, resumo, pontos-chave, papel semantico e alguma evidencia textual curta;
- `technology_mentions` deve listar somente tecnologias, frameworks, plataformas, bibliotecas, servicos, ferramentas, APIs ou providers efetivamente citados ou fortemente indicados no bruto;
- `technology_mentions` deve separar mencao tecnologica de conceito tecnico abstrato;
- `technology_mentions` nao deve sugerir tecnologias relacionadas que nao apareceram na aula;
- `technology_mentions` deve ajudar a futura E04 a deduplicar tecnologias repetidas entre aulas e enriquecer a memoria do app;
- `technical_terms` deve conter termos normalizados e correcoes provaveis;
- quando `raw_text_file` tiver nome preparado pelo Mindvox no padrao `YYYY-MM-DD-...-aula-N-sessao-M.txt`, a E03 deve usar esse nome apenas como fonte de defaults para metadados ausentes, preservando o contrato publico do endpoint;
- quando o arquivo preparado trouxer esse padrao e `class_date`, `discipline`, `class_title` ou `session_label` forem explicitamente enviados pelo usuario, esses valores recebidos devem prevalecer mesmo que sejam diferentes do nome do arquivo, pois continuam sendo metadados opcionais do formulario;
- diferencas entre metadados recebidos e defaults inferidos do nome preparado devem ser registradas em log saneado para auditoria, mas nao devem gerar `422`;
- logs operacionais da E03 devem registrar filename e metadados saneados recebidos, sem registrar transcricao bruta, prompt integral, token ou chave, para permitir auditoria de divergencia de metadados;
- `processing_notes` deve registrar correcoes, incertezas e cuidados relevantes.

Motivo:

- aulas longas possuem alta redundancia semantica;
- repeticoes, retomadas, hesitacoes e perguntas sobre o mesmo ponto aumentam o tamanho do bruto sem necessariamente acrescentar conteudo novo;
- nomes de tecnologias citados em aula costumam ser informacao relevante para trabalhos praticos da disciplina;
- uma relacao estruturada dessas mencoes facilita recuperacao futura mesmo quando a tecnologia foi citada rapidamente;
- a transcricao bruta da E02 ja e o lastro mais fiel para auditoria;
- uma segunda versao quase integral encarece o processamento e duplica a funcao da E02;
- um resumo curto tambem e invalido, porque omite conteudo empirico, exemplos e debates que possuem valor didatico;
- o valor especifico da E03 e transformar o bruto em material semanticamente organizado e didaticamente legivel.

Assim, `corrected_full_text` quase integral nao deve ser requisito padrao do MVP.

Perfis futuros podem oferecer revisao integral, mas isso deve ser opcional e separado do perfil `study_notes`.

Interpretacao dos campos principais:

| Campo | Papel |
| --- | --- |
| `raw_text` | Lastro bruto para conferencia do que foi ouvido ou enviado |
| `didactic_text` | Texto corrido, didatico e logico para leitura humana, com redundancia semantica reduzida sem perda deliberada de conteudo |
| `themes` | Estrutura tematica para navegacao, estudo e futura ingestao pela E04 |
| `technical_terms` | Normalizacao e explicacao curta de termos tecnicos |
| `technology_mentions` | Inventario de tecnologias e ferramentas citadas, util para memoria e trabalhos futuros |
| `processing_notes` | Registro de correcoes, incertezas e escolhas de processamento |

Distincao entre `technical_terms` e `technology_mentions`:

- `technical_terms` registra conceitos que precisam ser compreendidos, como `REST`, `API First`, `microservicos` ou `LGPD`;
- `technology_mentions` registra nomes de ferramentas, plataformas, frameworks, bibliotecas, servicos, APIs ou providers, como `FastAPI`, `Django`, `Fetch API`, `Playwright`, `Selenium`, `OpenAI Vision`, `Groq`, `Cloudflare`, `Docker` ou `Kubernetes`;
- um item pode aparecer nos dois campos apenas quando cumprir as duas funcoes;
- quando houver incerteza de normalizacao, a forma provavel deve vir com `confidence` menor e com `normalized_from`.

### 10.3 Provider Externo Padrao Sugerido

A E03 tambem deve prever uso de provider externo OpenAI-compatible para teste real e portabilidade.

Provider padrao sugerido para a configuracao inicial:

| Campo | Valor sugerido |
| --- | --- |
| `MINDVOX_LLM_PROVIDER` | `groq` |
| `MINDVOX_LLM_BASE_URL` | `https://api.groq.com/openai/v1` |
| `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` | `api.groq.com` |
| `MINDVOX_LLM_MODEL` | `llama-3.3-70b-versatile` |
| `MINDVOX_LLM_API_KEY` | Deve vir do `.env` da instalacao |

Motivo:

- Groq oferece API compativel com OpenAI;
- `llama-3.3-70b-versatile` e modelo de producao adequado a processamento textual;
- a opcao permite que o professor ou usuario tecnico rode a E03 mesmo sem iniciar modelo local;
- a configuracao por `.env` preserva seguranca e evita exposicao da chave no Swagger, logs ou Git.

Regras:

- nenhuma chave real da Groq deve ser gravada no repo;
- `.env.example` pode citar o nome da variavel e o formato esperado, mas deve usar valor ficticio ou vazio;
- em modo `provider`, ausencia de `MINDVOX_LLM_API_KEY` deve gerar erro controlado;
- em modo `provider`, valor vazio ou placeholder de exemplo em `MINDVOX_LLM_API_KEY`, como `replace-with-provider-key` ou `<set-real-key-only-in-local-env>`, deve ser tratado como chave ausente;
- em modo `provider`, `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` pode restringir os hosts externos aceitos;
- Groq deve ser tratado como provider padrao sugerido, nao como unico provider possivel;
- qualquer provider OpenAI-compatible podera ser usado se `MINDVOX_LLM_BASE_URL`, `MINDVOX_LLM_MODEL` e `MINDVOX_LLM_API_KEY` estiverem configurados;
- em modo `provider`, o conteudo de `raw_text` ou a transcricao gerada a partir do audio sera enviado ao provider externo configurado;
- modo `local` deve ser preferido quando o conteudo nao puder sair da maquina;
- a documentacao da API e a prova humana devem deixar essa diferenca de privacidade explicita.

---

## 11. Saida de Sucesso

Status:

```text
200 OK
```

Schema conceitual:

```json
{
  "processed_transcription_id": "ptr_20260609T000000Z_ab12cd34",
  "input_type": "audio",
  "language": "pt-BR",
  "raw_text": "...",
  "didactic_text": "...",
  "themes": [
    {
      "order": 1,
      "title": "API First",
      "summary": "...",
      "key_points": ["..."],
      "semantic_role": "fundamento",
      "evidence": "..."
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
      "message": "Termo tecnico normalizado com baixa exposicao de detalhes sensiveis."
    }
  ],
  "metadata": {
    "course": "Pós-UFG-T2-Agentes_inteligentes_IA",
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
  },
  "study_package": {
    "metadata": {
      "course_id": "ufg_pos_2",
      "course_name": "UFG Pos 2",
      "institution": "Federal University of Goias",
      "discipline": "API",
      "class_number": "1",
      "class_date": "2026-05-16",
      "session_number": "2",
      "session_label": "S02"
    },
    "operational_anchors": [],
    "concept_candidates": [],
    "audit_report": {
      "status": "passed"
    },
    "memory_manifest": {
      "relational_target": "sqlite",
      "vector_candidates": ["didactic_text"]
    },
    "export_targets": []
  }
}
```

Campos esperados:

| Campo | Descricao |
| --- | --- |
| `processed_transcription_id` | Identificador opaco da transcricao processada |
| `input_type` | Tipo de entrada usada |
| `language` | Idioma considerado |
| `raw_text` | Texto bruto recebido ou produzido pela transcricao |
| `didactic_text` | Texto discursivo, sequencial, logico e didatico, com redundancias semanticas enxugadas |
| `themes` | Lista de temas semanticos principais, pronta para orientar processamento futuro pela E04 |
| `themes[].order` | Ordem logica do tema dentro da aula processada |
| `themes[].title` | Titulo curto do nucleo tematico |
| `themes[].summary` | Resumo semantico do tema |
| `themes[].key_points` | Pontos principais do tema |
| `themes[].semantic_role` | Papel do tema no conteudo, como fundamento, exemplo, risco, comparacao, pratica ou conclusao |
| `themes[].evidence` | Trecho curto ou pista textual que justifica a extracao do tema |
| `technical_terms` | Termos tecnicos normalizados ou sugeridos |
| `technical_terms[].term` | Termo tecnico normalizado |
| `technical_terms[].normalized_from` | Formas brutas ou artefatos de STT que originaram a normalizacao |
| `technical_terms[].confidence` | Confianca da normalizacao: `low`, `medium` ou `high` |
| `technology_mentions` | Tecnologias, ferramentas, frameworks, plataformas, bibliotecas, servicos ou providers citados |
| `technology_mentions[].name` | Nome normalizado da tecnologia ou ferramenta |
| `technology_mentions[].category` | Categoria, como framework, library, platform, service, provider, protocol, language, database, infrastructure, tool ou api |
| `technology_mentions[].context` | Contexto curto da mencao na aula |
| `technology_mentions[].importance` | Importancia estimada para estudo ou trabalho: `low`, `medium` ou `high` |
| `technology_mentions[].normalized_from` | Formas brutas ou artefatos de STT que originaram a normalizacao |
| `technology_mentions[].confidence` | Confianca da extracao: `low`, `medium` ou `high` |
| `technology_mentions[].evidence` | Trecho curto ou pista textual que justifica a mencao |
| `processing_notes` | Notas controladas sobre correcoes, incertezas e cuidados do processamento |
| `metadata` | Metadados opcionais da aula |
| `source` | Rastreabilidade da entrada e, quando aplicavel, da transcricao |
| `source.input_origin` | Origem operacional da entrada: `audio` ou `raw_text` |
| `source.raw_text_origin` | Origem do bruto: `generated_by_transcription_service` ou `provided_by_client` |
| `source.transcription` | Objeto com dados de STT quando `input_type=audio`; `null` quando `input_type=raw_text` |
| `processing_engine` | Motor/modo usado no pos-processamento |
| `artifact_locations` | Caminhos relativos dos artefatos gerados, sem expor path absoluto local |
| `artifact_locations.human_text_path` | Caminho relativo do Markdown humano processado |
| `artifact_locations.technical_json_path` | Caminho relativo do JSON tecnico processado |
| `study_package` | Envelope canonico estruturado da aula processada, usado pela pagina humana de saida, por artefatos locais e pela futura E04 |
| `study_package.operational_anchors` | URLs, prazos, trabalhos, entregas, eventos, contatos, canais e documentos detectados |
| `study_package.concept_candidates` | Conceitos candidatos a notas atomicas futuras |
| `study_package.audit_report` | Relatorio de cobertura, suspeitas, chunks, retries e qualidade do processamento |
| `study_package.memory_manifest` | Mapa para ingestao futura pela E04 em SQLite e campo vetorial |
| `study_package.export_targets` | Destinos opcionais de exportacao, como artefatos locais e Obsidian quando ativado |

Observacao:

- quando `input_type=raw_text`, `source.transcription` deve ser `null`;
- `raw_text` permanece na resposta para rastreabilidade e valor probatorio;
- `didactic_text`, `themes`, `technical_terms` e `technology_mentions` representam os produtos processados da E03;
- `didactic_text` nao e revisao humana definitiva;
- `themes` deve ser suficientemente estruturado para futura ingestao pela E04, mas a E03 ainda nao grava memoria;
- `technology_mentions` deve servir como inventario de tecnologias citadas, mas a deduplicacao historica entre aulas fica para a E04/E05.
- `study_package`, quando presente no HTTP ou artefato tecnico, deve manter as cinco entregas publicas disponiveis e nao remover compatibilidade com clientes que leem os campos de topo;
- o `memory_manifest` prepara a E04, mas nao executa persistencia na E03;
- `export_targets` pode listar Obsidian como destino opcional, mas nao torna Obsidian requisito de uso.

---

## 12. Erros

Formato geral de erro controlado:

```json
{
  "detail": "Mensagem curta, sem stack trace, path local, prompt integral, transcricao integral, resposta integral, token ou chave."
}
```

### 12.1 Autenticacao Ausente ou Invalida

Status:

```text
401 Unauthorized
```

Uso:

- quando `Authorization: Bearer <token>` estiver ausente, invalido ou malformado.

### 12.1.1 Transporte Inseguro em Deploy Publico

Status:

```text
403 Forbidden
```

Uso:

- quando `MINDVOX_PUBLIC_DEPLOYMENT=true`;
- quando `POST /processed-transcriptions/v1.0.0` for chamado sem que a aplicacao receba `request.url.scheme == "https"`;
- quando a requisicao chegar ao endpoint protegido por transporte que nao atende a regra publica de seguranca.

### 12.2 Motor Indisponivel

Status:

```text
503 Service Unavailable
```

Uso:

- quando modo `provider` estiver configurado sem chave;
- quando provider externo estiver indisponivel;
- quando modo `local` estiver configurado sem modelo local disponivel;
- quando audio exigir transcricao real e o motor de STT estiver indisponivel.

Exemplo:

```json
{
  "detail": "Post-processing service is unavailable."
}
```

### 12.3 Entrada Invalida

Status:

```text
422 Unprocessable Entity
```

Uso:

- `input_type` ausente ou invalido;
- `audio_file` ausente quando `input_type=audio`;
- `raw_text` e `raw_text_file` ausentes quando `input_type=raw_text`;
- `raw_text` vazio quando enviado;
- `raw_text_file` vazio ou nao decodificavel como UTF-8;
- `raw_text` e `raw_text_file` enviados juntos;
- `audio_file` enviado junto com `raw_text` ou `raw_text_file`;
- `processing_profile` fora dos valores aceitos;
- metadados invalidos.

### 12.4 Arquivo Invalido

Status:

```text
400 Bad Request
```

Uso:

- extensao nao aceita;
- `content_type` incompativel.

### 12.5 Entrada Grande Demais

Status:

```text
413 Payload Too Large
```

Uso:

- quando audio exceder limite configurado;
- quando `raw_text` exceder `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS`.

### 12.6 Timeout do Motor

Status:

```text
504 Gateway Timeout
```

Uso:

- provider externo ou servidor local compativel com OpenAI nao respondeu dentro de `MINDVOX_LLM_TIMEOUT_SECONDS`;
- erro deve ser registrado sem prompt integral, texto bruto integral, resposta integral ou chave.

### 12.7 Metodo HTTP Invalido

Status:

```text
405 Method Not Allowed
```

Uso:

- quando cliente tentar usar outro metodo HTTP na rota `POST /processed-transcriptions/v1.0.0`.

### 12.8 Saida LLM Rejeitada por Qualidade Semantica

Status:

```text
502 Bad Gateway
```

Uso:

- o motor LLM retornou JSON estruturalmente valido, mas a auditoria deterministica de cobertura semantica concluiu que a saida preservou conteudo insuficiente;
- a resposta deve conter `error_code=postprocessing_quality_rejected`, tentativa, limite de tentativas, indicacao de retry e caminhos para os artefatos rejeitados;
- a saida recusada deve ser preservada em `outputs/processed_transcriptions/rejected/` e `outputs/human/processed_transcriptions/rejected/` para auditoria humana;
- o JSON de quarentena deve conter `runtime_snapshot` com modo de chunking, quantidade de chunks, limite de saida do LLM, modelo, tamanho do bruto e regua semantica aplicada.

### 12.9 Erro Interno

Status:

```text
500 Internal Server Error
```

Uso:

- erro inesperado, sem vazamento de stack trace, paths, tokens, prompts, transcricao integral ou chaves.

---

## 13. Seguranca

A E03 manipula dados sensiveis:

- audio;
- transcricao bruta;
- texto processado;
- metadados de aula;
- possiveis prompts;
- possiveis respostas de LLM;
- tokens e chaves de provider.

Regras:

- autenticacao por Bearer token e obrigatoria;
- configuracoes sensiveis devem vir de ambiente;
- `.env` real nao entra no Git;
- `.env.example` pode conter apenas valores ficticios;
- em desenvolvimento local (`MINDVOX_PUBLIC_DEPLOYMENT=false`), `MINDVOX_API_TOKEN` ausente ou vazio deve usar automaticamente o token didatico `dev-token`;
- placeholder de exemplo, como `replace-with-local-token` ou `<set-real-token-only-in-local-env>`, deve ser tratado como token ausente;
- `dev-token` so e permitido como token didatico local; em `MINDVOX_PUBLIC_DEPLOYMENT=true`, deve ser tratado como token ausente;
- modo `contract` deve continuar exigindo Bearer token, pois o contrato de seguranca dos endpoints tambem precisa ser testado;
- logs nao devem conter texto integral da transcricao, prompt integral, resposta integral ou chave;
- se provider externo for usado, isso deve ser explicito e configurado;
- se modo `provider` for usado, deve ficar claro que o conteudo transcrito pode ser enviado ao provider externo configurado;
- modo `provider` nao deve aceitar `MINDVOX_LLM_BASE_URL` local, loopback ou privada, para evitar falsa configuracao de provider;
- modo `provider` deve rejeitar hostname que resolva para endereco local, privado, loopback, link-local, reservado, multicast ou indefinido;
- modo `provider` deve rejeitar hostname fora de `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` quando allowlist estiver configurada;
- em modo publico (`MINDVOX_PUBLIC_DEPLOYMENT=true`), a aplicacao deve exigir `MINDVOX_TRUSTED_HOSTS`, rejeitar `MINDVOX_TRUSTED_HOSTS=*` e desabilitar docs por padrao, salvo decisao explicita;
- em modo publico (`MINDVOX_PUBLIC_DEPLOYMENT=true`), `POST /processed-transcriptions/v1.0.0` deve exigir transporte seguro, aceitando apenas requisicao que chegue a aplicacao com scheme `https`;
- se TLS terminar em proxy, o proxy e o servidor ASGI devem ser configurados de modo confiavel para repassar o scheme `https`; a aplicacao nao deve confiar em header `X-Forwarded-Proto` enviado livremente pelo cliente;
- a checagem de transporte seguro nao substitui TLS, rate limiting, limite de corpo e bloqueio de acesso direto ao processo ASGI na camada de deploy;
- modo `local` nao deve aceitar `MINDVOX_LLM_BASE_URL` publica, para evitar envio acidental de conteudo sensivel a destino externo;
- o cliente LLM deve enviar limite de tokens e impor limite de leitura da resposta antes de interpretar JSON;
- a saida do LLM pode passar por normalizacao defensiva antes da validacao final, aceitando variacoes previsiveis como cerca Markdown, texto externo ao JSON, aliases de campos, `alta/media/baixa` para `high/medium/low` e categorias em portugues, desde que o produto humano principal (`didactic_text` ou alias equivalente) exista;
- a normalizacao defensiva nao deve inventar o produto principal nem aceitar saida inutil: ausencia de texto didatico ou JSON irrecuperavel continua gerando erro controlado sem vazamento da resposta integral;
- ferramentas internas de benchmark devem impor limite de leitura da resposta HTTP;
- nomes de provider exibidos em `processing_engine` devem ser tratados como dados publicos e sanitizados contra termos sensiveis;
- upload de audio deve respeitar limite por leitura incremental, evitando consumo de memoria desnecessario em arquivo acima do limite;
- exemplos publicos devem usar dados ficticios ou seguros.

---

## 14. Logs

Eventos permitidos:

- inicio da requisicao;
- `input_type`;
- tamanho aproximado da entrada;
- modo de processamento;
- provider/motor sem chave;
- sucesso/falha;
- status code;
- codigo de erro controlado para falhas previstas;
- falhas de autenticacao com `status_code`, `error_code`, `phase=auth` e duracao;
- duracao do processamento;
- contagem de caracteres e temas, sem texto integral.

Persistencia:

- no MVP, a E03 nao deve criar armazenamento proprio de logs;
- os eventos devem usar o logger da aplicacao/servidor com mensagens sanitizadas;
- persistencia externa de logs fica fora do escopo da E03, salvo configuracao operacional da instalacao.
- quando a E03 receber `input_type=audio`, a transcricao bruta gerada pelo servico STT deve ser preservada automaticamente pelos mesmos artefatos locais da E02: JSON tecnico em `outputs/transcriptions/[metadados-seguros_]<transcription_id>.json` e texto humano em `outputs/human/transcriptions/[metadados-seguros_]<transcription_id>.txt`;
- quando a E03 receber `input_type=raw_text`, ela nao cria novo artefato de STT, pois o texto bruto foi fornecido pelo cliente.
- toda resposta processada da E03 deve ser preservada em `outputs/processed_transcriptions/[metadados-seguros_]<processed_transcription_id>.json` para contrato tecnico e em `outputs/human/processed_transcriptions/[metadados-seguros_]<processed_transcription_id>.md` para leitura humana direta;
- quando existirem `class_date`, `class_title`, `session_label` ou metadado equivalente, o nome do arquivo pode usar prefixo humano sanitizado para facilitar localizacao da aula, mas deve terminar com o identificador opaco correspondente;
- o artefato Markdown deve conter titulo humano derivado dos metadados quando disponiveis, bloco curto de metadados, texto didatico, temas, termos tecnicos, tecnologias citadas e notas de processamento, sem substituir o JSON necessario ao E04.
- a resposta deve indicar `artifact_locations.human_text_path` e `artifact_locations.technical_json_path`, sem expor path absoluto local;
- essa estrategia de pasta local e propria do modo `dev`/instalacao local; em producao publica, usuario final nao acessa o filesystem do servidor e a evolucao correta e endpoint/interface de download em Markdown, TXT, PDF ou outro formato de exportacao.

Dados proibidos em log:

- audio bruto;
- transcricao integral;
- texto processado integral;
- prompt integral;
- resposta integral de provider;
- token;
- chave;
- `.env`;
- paths locais sensiveis.

---

## 15. Documentacao FastAPI Esperada

A documentacao automatica deve mostrar:

- `summary` claro;
- `description` curta da finalidade;
- entrada `multipart/form-data`;
- descricoes didaticas com exemplos para cada campo;
- autenticacao Bearer;
- resposta `200`;
- respostas principais `400`, `401`, `405`, `413`, `422`, `500`, `502`, `503` e `504`;
- indicacao de que E03 nao grava memoria e nao executa busca;
- indicacao de que E03 pode receber audio ou transcricao bruta;
- indicacao de que modo `provider` envia o conteudo bruto ao provider externo configurado;
- indicacao direta das cinco entregas produzidas pelo endpoint.
- indicacao de que a pagina humana da E03, quando disponivel, e a interface recomendada para uso operacional por usuario final ou desenvolvedor aprendiz;
- indicacao de que Swagger permanece documentacao tecnica e console de teste;
- indicacao de que o `Study Package` e o artefato estruturado para pagina humana, exportacoes e futura E04.

As cinco entregas abaixo devem aparecer na informacao ao usuario da documentacao da API:

| Entrega | Explicacao para a documentacao |
| --- | --- |
| `raw_text` | Transcricao bruta recebida ou produzida a partir do audio. Serve como lastro de conferencia do que foi ouvido ou enviado. |
| `didactic_text` | Texto didatico corrido, em sequencia logica, sem titulos internos, com redundancias semanticas reduzidas. Serve para leitura humana apos a aula. |
| `themes` | Lista de temas semanticos da aula, com resumo, pontos principais, papel do tema e evidencia. Serve para estudo e prepara a futura ingestao pela E04. |
| `technical_terms` | Lista de conceitos tecnicos relevantes, normalizados ou corrigidos quando houver artefato de transcricao. Serve para compreensao conceitual. |
| `technology_mentions` | Lista de tecnologias, ferramentas, frameworks, plataformas, bibliotecas, servicos, APIs ou providers citados na aula. Serve para consulta posterior e memoria tecnica. |

Texto sugerido para `summary`:

```text
Post-process class transcription
```

Texto sugerido para `description`:

```text
Receives a recorded audio file or an existing raw transcription and turns it into study-ready material. It returns five deliveries: raw_text, the auditable raw transcription; didactic_text, a logical continuous didactic text with semantic redundancies reduced; themes, the main semantic topics prepared for future memory ingestion; technical_terms, relevant technical concepts and corrections; and technology_mentions, technologies, frameworks, platforms, tools, services, libraries, APIs, or providers mentioned in class. This endpoint does not store memory, create embeddings, or perform search. When provider mode is configured, raw transcription content is sent to the configured external LLM provider; use local mode when content must remain on this machine.
```

---

## 16. Exemplos de Uso

### 16.1 Chamada Valida com Texto Bruto

Entrada:

```text
POST /processed-transcriptions/v1.0.0
Authorization: Bearer <token valido>
multipart/form-data:
  input_type = raw_text
  raw_text = Boa tarde novamente...
  discipline = API
  class_date = 2026-05-16
  class_title = apifirst_fastapi_dev
  session_label = S02
  language = pt-BR
```

Resultado esperado:

```text
200 OK
```

Com resposta contendo `raw_text`, `didactic_text`, `themes`, `technology_mentions`, `technical_terms`, `processing_notes`, `metadata`, `source` e `processing_engine`.

### 16.2 Chamada Valida com Audio

Entrada:

```text
POST /processed-transcriptions/v1.0.0
Authorization: Bearer <token valido>
multipart/form-data:
  input_type = audio
  audio_file = aula_s02.wav
  discipline = API
  session_label = S02
  language = pt-BR
```

Resultado esperado:

```text
200 OK
```

Com transcricao bruta gerada internamente e pos-processamento aplicado em seguida.

### 16.3 Falha por Entrada Principal Ausente

Entrada:

```text
POST /processed-transcriptions/v1.0.0
Authorization: Bearer <token valido>
multipart/form-data:
  input_type = raw_text
```

Resultado esperado:

```text
422 Unprocessable Entity
```

### 16.4 Falha por Token Ausente

Entrada:

```text
POST /processed-transcriptions/v1.0.0
multipart/form-data:
  input_type = raw_text
  raw_text = texto bruto
```

Resultado esperado:

```text
401 Unauthorized
```

### 16.5 Falha por Entradas Conflitantes

Entrada:

```text
POST /processed-transcriptions/v1.0.0
Authorization: Bearer <token valido>
multipart/form-data:
  input_type = audio
  audio_file = aula_s02.wav
  raw_text = texto bruto enviado indevidamente junto com audio
```

Resultado esperado:

```text
422 Unprocessable Entity
```

---

## 17. Criterios de Aceite

A E03 podera ser considerada pronta para plano/tarefas quando:

- rota e metodo estiverem aprovados;
- escopo de pos-processamento estiver claro;
- limite entre E02, E03, E04 e E05 estiver claro;
- entrada por audio e por texto bruto estiver definida;
- resposta estruturada estiver definida;
- erros principais estiverem definidos;
- regras de seguranca e logs estiverem definidas;
- modo de contrato estiver previsto;
- modelo local preferencial estiver definido por prova real comparativa ou claramente adiado;
- provider externo padrao sugerido estiver definido sem chave real no repo;
- cinco entregas da E03 estiverem definidas e descritas para a documentacao da API;
- pagina humana de entrada estiver especificada como camada operacional distinta do Swagger;
- `Study Package` estiver definido como artefato canonico estruturado;
- pagina humana de saida estiver especificada;
- relacao com E04 por `memory_manifest` estiver explicitada sem iniciar ingestao de memoria na E03;
- Obsidian opcional estiver definido como exportacao e redundancia positiva, com criacao deterministica de Vault novo;
- prova real humana for exigida antes do commit de fechamento;
- Adalberto aprovar esta Spec.

Esta aprovacao teorica nao equivale ao fechamento canonico do endpoint.

O status da E03 so podera mudar para `fechada` quando, alem das decisoes teoricas acima:

- P03 e T03 tiverem sido criados ou atualizados a partir desta Spec;
- implementacao real estiver concluida;
- OpenAPI real refletir o contrato aprovado;
- testes automatizados da E03 e testes gerais passarem;
- prova funcional manual real for executada por humano e registrada;
- checklist aplicavel do endpoint estiver integralmente marcado ou justificado como `N/A`;
- revisao de Git estiver concluida antes do commit de fechamento.

### 17.1 Matriz Obrigatoria de Testes da E03

A implementacao da E03 deve criar testes automatizados em:

```text
tests/e03_processed_transcriptions/
```

Essa pasta deve conter `README.md` explicando hipoteses, escopo e comandos de execucao dos testes.

Testes automatizados obrigatorios:

| Area | Teste obrigatorio | Verificacao minima |
| --- | --- | --- |
| Documentacao do plano de testes | `test_e03_test_plan_documents_required_contract` | README da pasta e Spec registram matriz obrigatoria, comandos, cinco entregas, erros principais e regras de seguranca |
| Sucesso com texto bruto | `test_post_processed_transcriptions_raw_text_contract_success` | `POST /processed-transcriptions/v1.0.0` com `input_type=raw_text`, token valido e modo `contract` retorna `200 OK` |
| Sucesso com arquivo de texto bruto | `test_post_processed_transcriptions_raw_text_file_contract_success` | `POST /processed-transcriptions/v1.0.0` com `input_type=raw_text`, `raw_text_file=.txt`, token valido e modo `contract` retorna `200 OK` |
| Alias `raw_text_file` no `input_type` | `test_raw_text_file_input_type_alias_is_normalized_to_raw_text` | `input_type=raw_text_file` com arquivo `.txt` e normalizado para `raw_text` |
| Placeholder legado `string` do Swagger | `test_raw_text_file_ignores_legacy_swagger_string_placeholder` | Valor literal `string` enviado por cliente antigo/cacheado em campo opcional e tratado como ausente, sem virar conflito real |
| Schema de sucesso | `test_success_response_contains_five_deliveries_and_auxiliary_fields` | Resposta contem `raw_text`, `didactic_text`, `themes`, `technical_terms`, `technology_mentions`, `processing_notes`, `metadata`, `source`, `processing_engine` e `artifact_locations` |
| Origem com texto bruto | `test_raw_text_source_has_no_transcription_object` | Quando `input_type=raw_text`, `source.input_origin=raw_text`, `source.raw_text_origin=provided_by_client` e `source.transcription=null` |
| Sucesso com audio em contract | `test_post_processed_transcriptions_audio_contract_success` | Quando viavel em modo `contract`, audio aceito reutiliza fluxo interno de transcricao e retorna cinco entregas |
| Artefato bruto com audio | `test_audio_flow_saves_internal_raw_transcription_artifacts` | Quando `input_type=audio`, a transcricao bruta interna gera `.json` e `.txt` antes do pos-processamento |
| Fila concluida e artefatos processados | `test_audio_flow_completes_generated_transcription_queue_job` | Transcricao gerada por E03 entra na fila, passa para `completed` e salva `.json` tecnico e `.md` humano quando o pos-processamento conclui |
| Titulo humano por metadados | `test_processed_markdown_artifact_uses_class_metadata_title` | Markdown processado usa data, titulo e sessao no nome seguro do arquivo e no titulo legivel do documento |
| Nome seguro de artefato | `test_artifact_stem_uses_safe_class_metadata_prefix` | Servico compartilhado de nomeacao usa prefixo sanitizado e mantem identificador opaco como sufixo |
| Fila pendente apos falha | `test_audio_flow_keeps_queue_job_pending_when_postprocessing_fails` | Falha de motor apos STT deixa job pendente para retry sem reenviar audio |
| Retry de fila sem reupload | `test_pending_generated_transcription_job_can_be_retried_without_reupload` | Job pendente e reprocessado a partir da fila local |
| Nao invencao de tecnologia | `test_contract_mode_does_not_invent_technology_mentions` | Modo `contract` nao inventa tecnologias ausentes do bruto |
| Autenticacao ausente | `test_missing_token_returns_401` | Requisicao sem `Authorization` retorna `401 Unauthorized` |
| Token invalido | `test_invalid_token_returns_401` | Bearer invalido retorna `401 Unauthorized` |
| Header de autenticacao malformado | `test_malformed_authorization_header_returns_401` | Header `Authorization` fora do formato `Bearer <token>` retorna `401 Unauthorized` |
| Token local automatico | `test_local_development_without_api_token_uses_dev_token` | Em desenvolvimento local, ausencia ou valor vazio de `MINDVOX_API_TOKEN` usa `dev-token` automaticamente |
| Token didatico em deploy publico | `test_dev_token_configuration_returns_503_in_public_deployment` | `dev-token` configurado em `MINDVOX_PUBLIC_DEPLOYMENT=true` e tratado como token ausente |
| Deploy publico sem token padrao | `test_public_deployment_without_api_token_has_no_default_token` | Em `MINDVOX_PUBLIC_DEPLOYMENT=true`, ausencia de `MINDVOX_API_TOKEN` nao cria token padrao |
| Perfil CLI de contrato | `test_contract_profile_forces_contract_modes_and_disables_llama_autostart` | Perfil `contract` forca STT/E03 em contrato e desliga autostart do Llama |
| Perfil CLI de producao | `test_prod_profile_enables_public_hardening_without_dev_token_default` | Perfil `prod` liga hardening publico, exige host confiavel/token externo e desliga Llama local |
| Transporte inseguro em deploy publico | `test_public_deployment_requires_https_for_processed_transcriptions` | `POST /processed-transcriptions/v1.0.0` retorna `403 Forbidden` quando a aplicacao nao recebe scheme `https` |
| Transporte seguro HTTPS | `test_public_deployment_accepts_https_for_processed_transcriptions` | Requisicao em deploy publico com scheme `https` passa pela verificacao de transporte seguro |
| Entrada ausente | `test_missing_main_input_returns_422` | `input_type=raw_text` sem `raw_text` ou `raw_text_file` retorna `422 Unprocessable Entity` |
| Tipo de entrada invalido | `test_invalid_input_type_returns_422` | `input_type` fora de `audio`, `raw_text` ou alias `raw_text_file` retorna `422 Unprocessable Entity` |
| Audio ausente | `test_audio_input_without_audio_file_returns_422` | `input_type=audio` sem `audio_file` retorna `422 Unprocessable Entity` |
| Placeholder vazio de upload | `test_raw_text_flow_ignores_empty_audio_file_placeholder` | Placeholder vazio de `audio_file` enviado pelo Swagger nao bloqueia fluxo valido de `raw_text` |
| Entrada conflitante audio/texto | `test_audio_and_raw_text_conflict_returns_422` | Enviar `audio_file` e `raw_text` juntos retorna `422 Unprocessable Entity` |
| Entrada conflitante texto/arquivo | `test_raw_text_and_raw_text_file_conflict_returns_422` | Enviar `raw_text` e `raw_text_file` juntos retorna `422 Unprocessable Entity` |
| Entrada conflitante audio/arquivo texto | `test_audio_and_raw_text_file_conflict_returns_422` | Enviar `audio_file` e `raw_text_file` juntos retorna `422 Unprocessable Entity` |
| Arquivo de texto invalido | `test_invalid_raw_text_file_extension_returns_400` | `raw_text_file` fora de `.txt` retorna `400 Bad Request` |
| Perfil invalido | `test_invalid_processing_profile_returns_422` | `processing_profile` fora dos valores aceitos retorna `422 Unprocessable Entity` |
| Arquivo invalido | `test_invalid_audio_extension_returns_400` | Extensao fora de `.wav` e `.m4a` retorna `400 Bad Request` |
| Content type invalido | `test_incompatible_audio_content_type_returns_400` | Content type incompativel com audio retorna `400 Bad Request` |
| Metadado invalido | `test_invalid_metadata_returns_422` | Metadado fora da regra retorna `422 Unprocessable Entity` |
| Metadado opcional grande demais | `test_oversized_optional_metadata_returns_422` | `course`, `discipline` ou `class_title` acima dos limites retorna `422 Unprocessable Entity` |
| Entrada grande demais | `test_raw_text_over_limit_returns_413` | `raw_text` acima de `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS` retorna `413 Payload Too Large` |
| Upload de audio grande demais | `test_audio_over_upload_limit_returns_413` | Audio acima de `MINDVOX_MAX_UPLOAD_MB` retorna `413 Payload Too Large` |
| Leitura incremental de upload | `test_limited_upload_reader_rejects_before_reading_full_oversized_upload` | Leitor compartilhado interrompe upload acima do limite sem ler o arquivo inteiro |
| Motor indisponivel | `test_unavailable_processing_engine_returns_503` | Modo `provider` sem chave, modo `local` sem servidor ou STT indisponivel retorna `503 Service Unavailable` |
| Chave placeholder de provider | `test_placeholder_provider_key_returns_503` | Modo `provider` com `MINDVOX_LLM_API_KEY` vazio ou placeholder retorna `503 Service Unavailable` e nao trata o placeholder como chave real |
| Chave vazia de provider | `test_empty_provider_key_returns_503` | Modo `provider` com chave vazia retorna `503 Service Unavailable` |
| Token placeholder do app | `test_placeholder_api_token_configuration_returns_503` | `MINDVOX_API_TOKEN` com placeholder e tratado como ausente |
| Destino provider invalido | `test_provider_mode_rejects_localhost_endpoint` | Modo `provider` rejeita URL local, loopback ou privada |
| Hostname provider resolvido para IP privado | `test_provider_mode_rejects_hostname_resolving_to_private_address` | Modo `provider` rejeita hostname externo aparente quando DNS resolve para IP local/privado |
| Provider fora da allowlist | `test_provider_mode_rejects_hostname_outside_allowed_list` | Modo `provider` rejeita host fora de `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` |
| Provider dentro da allowlist | `test_provider_mode_accepts_hostname_inside_allowed_list` | Modo `provider` aceita host previsto na allowlist |
| Destino local invalido | `test_local_mode_rejects_public_endpoint` | Modo `local` rejeita URL publica |
| Local indisponivel | `test_local_unavailable_processing_engine_returns_503` | Servidor local indisponivel retorna `503 Service Unavailable` |
| Autostart nao roda em contrato | `test_contract_mode_does_not_start_llama_server` | Modo `contract` nao inicia `llama-server` |
| Autostart local desabilitado | `test_local_autostart_disabled_does_not_start_llama_server` | `MINDVOX_LOCAL_LLM_AUTOSTART=false` nao inicia `llama-server` |
| Servidor local existente reutilizado | `test_existing_openai_compatible_server_is_reused` | Servidor local ja pronto em `/v1/models` e reaproveitado |
| Autostart local executado | `test_local_autostart_starts_llama_server_until_ready` | Modo `local` inicia `llama-server` com modelo, host, porta, contexto e camadas configuradas |
| Autostart sem binario | `test_missing_llama_server_path_fails_with_clear_message` | Falta de `llama-server` falha com referencia a `MINDVOX_LLAMA_SERVER_PATH` |
| Autostart sem modelo | `test_missing_model_path_fails_with_clear_message` | Falta de GGUF falha com referencia a `MINDVOX_LOCAL_LLM_MODEL_PATH` |
| Autostart timeout | `test_startup_timeout_terminates_started_process` | Processo iniciado e encerrado se nao ficar pronto no timeout |
| Saida invalida de LLM | `test_invalid_llm_output_returns_500` | Saida sem campos obrigatorios retorna erro controlado sem vazar resposta integral |
| Saida longa semanticamente insuficiente | `test_long_llm_output_with_insufficient_semantic_coverage_returns_502_with_rejected_artifact` | Para bruto longo, saida curta demais ou com poucos temas e rejeitada apos retry, gera `502` estruturado e salva artefato rejeitado |
| Fila encerra falha de qualidade | `test_audio_flow_moves_quality_failure_to_failed_after_max_attempts` | Falha de cobertura semantica em audio sai de `pending`, vai para `queue/failed/` apos max attempts e preserva artefato rejeitado |
| Retry de cobertura semantica | `test_long_llm_output_retry_can_recover_semantic_coverage` | Primeira saida insuficiente aciona segunda chamada mais rigorosa; saida suficiente e aceita e registra nota de controle |
| Ancora Positivo generica | `test_semantic_anchors_do_not_treat_generic_positive_as_company` | Uso comum de "positivo" nao aciona a ancora da empresa Positivo |
| Ancora Positivo nominal | `test_semantic_anchors_detect_possibly_named_positivo_company` | Contexto nominal minimo continua acionando a ancora da empresa Positivo |
| Ancora score generica | `test_semantic_anchors_do_not_treat_generic_score_as_viability_case` | "Score" isolado nao aciona o case de score de viabilidade |
| Ancora microsservicos acentuada | `test_semantic_coverage_matches_microsservicos_accented_spelling` | `microsserviços` acentuado satisfaz a ancora `microservicos` |
| Timeout do motor | `test_processing_engine_timeout_returns_504` | Timeout de provider externo ou servidor local retorna `504 Gateway Timeout` |
| Metodo invalido | `test_get_processed_transcriptions_returns_405` | Metodo diferente de `POST` retorna `405 Method Not Allowed` |
| Deploy publico sem hosts confiaveis | `test_public_deployment_requires_trusted_hosts` | `MINDVOX_PUBLIC_DEPLOYMENT=true` sem `MINDVOX_TRUSTED_HOSTS` impede inicializacao |
| Deploy publico endurecido | `test_public_deployment_disables_docs_and_enforces_trusted_hosts` | Docs desabilitados por padrao e host invalido rejeitado |
| Deploy publico sem wildcard | `test_public_deployment_rejects_wildcard_trusted_hosts` | `MINDVOX_TRUSTED_HOSTS=*` impede inicializacao quando `MINDVOX_PUBLIC_DEPLOYMENT=true` |
| OpenAPI | `test_openapi_documents_e03_contract` | `/openapi.json` contem perfil ativo (`Active startup profile`), rota, Bearer, multipart, descricoes didaticas, cinco entregas e respostas `400`, `401`, `403`, `405`, `413`, `422`, `500`, `502`, `503`, `504` |
| Seguranca de resposta | `test_response_and_errors_do_not_expose_sensitive_values` | Respostas e erros nao expõem token, `.env`, path local, prompt integral, transcricao integral ou resposta integral do provider |
| Logs | `test_e03_logs_are_sanitized` | Logs operacionais nao registram audio bruto, transcricao integral, prompt integral, resposta integral, token, chave ou path sensivel |
| Logs de autenticacao | `test_processed_transcription_auth_failure_logs_status_error_and_duration` | Falha de autenticacao registra status, codigo, fase e duracao sem expor credencial |
| Logs de falhas controladas | `test_controlled_validation_errors_are_logged_without_sensitive_values` | Falhas previstas registram status, codigo e duracao sem dados sensiveis |
| Nome publico do provider | `test_processing_engine_redacts_sensitive_provider_name` | `processing_engine.name` redige provider configurado com marcador sensivel |
| Limite enviado ao LLM | `test_llm_client_sends_max_tokens_and_limits_response_size` | Cliente envia `max_tokens` e limita leitura da resposta |
| Prompt operacional da E03 | `test_llm_prompt_uses_e03_manual_without_concise_instruction` | Prompt inclui manual operacional, exige preservacao semantica e nao reintroduz instrucao de concisao/resumo |
| Thinking local desativado | `test_llm_client_disables_thinking_for_local_llama_server` | Cliente envia `chat_template_kwargs.enable_thinking=false` ao `llama-server` em modo `local` |
| Provider sem parametro local | `test_llm_client_does_not_send_local_template_kwargs_to_provider` | Cliente nao envia parametro especifico de `llama-server` para provider externo |
| Resposta LLM excessiva | `test_llm_client_rejects_excessive_response_body` | Resposta acima do limite e rejeitada antes do parse |
| Resposta excessiva no benchmark | `test_benchmark_script_rejects_excessive_response_body` | Script interno de benchmark tambem limita leitura da resposta HTTP |
| Limite LLM invalido | `test_zero_llm_max_output_tokens_falls_back_to_default` | Valor zero de `MINDVOX_LLM_MAX_OUTPUT_TOKENS` volta ao padrao seguro |
| Slots Llama invalidos | `test_zero_llama_server_parallel_falls_back_to_default` | Valor zero de `MINDVOX_LLAMA_SERVER_PARALLEL` volta ao padrao seguro `1` |

Comandos de teste obrigatorios:

```bash
uv run python -m unittest discover -s tests/e03_processed_transcriptions -v
uv run python -m unittest discover -s tests -v
```

Regra de modo `contract`:

- testes automatizados devem usar modo `contract` para validar contrato HTTP sem depender de provider externo ou modelo local;
- modo `contract` deve aparecer explicitamente em `processing_engine`;
- testes reais com modelo local ou provider externo nao substituem esses testes automatizados.

Regra de prova humana:

- antes do commit de fechamento da E03, humano deve executar teste funcional real do endpoint com entrada representativa;
- o registro deve indicar modo usado (`local` ou `provider`), modelo/provider, tempo aproximado, status HTTP e avaliacao humana da coerencia das cinco entregas;
- se o modo usado for `provider`, o registro deve declarar que o conteudo bruto foi enviado ao provider externo configurado;
- a prova humana real nao substitui os testes automatizados.

Regra definitiva para entrada longa:

- `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS` permanece como limite duro de seguranca HTTP;
- `raw_text` acima desse limite deve ser rejeitado com `413 Payload Too Large`;
- `raw_text` abaixo desse limite pode seguir fluxo curto de chamada unica ou fluxo longo interno, conforme configuracao;
- o fluxo longo interno usa pre-auditoria, chunking TF-IDF em memoria, processamento chunk-by-chunk, merge canonico e auditoria final;
- chunking acima do limite duro, processamento distribuido em lotes externos ou ingestao persistente ficam fora da E03.

---

## 18. Checklist Aplicavel do Endpoint

Checklist extraido do modelo geral da S02.

Interpretacao:

- itens de contrato ja decididos pela Spec aparecem como `[x]`;
- itens que dependem de plano, implementacao, testes, OpenAPI real, prova humana ou demonstracao permanecem como `[ ]` e bloqueiam o fechamento canonico do endpoint;
- itens nao aplicaveis aparecem como `N/A`.

Consequencia canonica:

- este checklist orienta a validacao final enquanto a E03 estiver `implementada_em_validacao_real`;
- a E03 nao deve ser marcada como `fechada` enquanto houver item aplicavel em `[ ]`;
- a conclusao da etapa teorica autoriza planejar e implementar, mas nao autoriza pular teste real, revisao de Git ou commit de fechamento.

| Item | Status | Justificativa |
| --- | --- | --- |
| Metodo HTTP definido | [x] | `POST` aprovado como proposta da Spec |
| Rota definida | [x] | `/processed-transcriptions/v1.0.0` proposta |
| Padrao de versionamento decidido | [x] | Endpoint de negocio versionado com `v1.0.0` |
| Finalidade do endpoint explicada | [x] | Pos-processar audio ou transcricao bruta |
| Diferenca entre endpoint operacional e endpoint de negocio esclarecida | [x] | E03 e endpoint de negocio e IA textual |
| Parametros de path definidos | N/A | Nao ha parametros de path |
| Parametros de query definidos | N/A | Nao ha parametros de query no MVP |
| Body definido | [x] | `multipart/form-data` com `input_type`, audio ou texto e metadados |
| Headers exigidos definidos | [x] | `Authorization: Bearer <token>` |
| Tipos, obrigatoriedade e limites de entrada descritos | [x] | Campos e condicoes de entrada definidos |
| Resposta de sucesso definida | [x] | JSON estruturado com bruto, texto didatico, temas, tecnologias, termos e motores |
| Status code de sucesso definido | [x] | `200 OK` |
| Campos da resposta descritos | [x] | Campos descritos em tabela |
| Ausencia de dados sensiveis verificada | [x] | Regras de nao vazamento definidas |
| Schema de resposta definido | [x] | Schema conceitual definido com cinco entregas, `processing_notes`, `source` condicional e motor |
| Erros principais listados | [x] | `400`, `401`, `403`, `405`, `413`, `422`, `500`, `502`, `503`, `504` |
| Status codes de erro definidos | [x] | Cada erro principal possui status |
| Mensagens de erro sem vazamento sensivel | [x] | Regra definida |
| Metodo HTTP invalido considerado | [x] | `405 Method Not Allowed` definido; teste fica pendente na implementacao |
| Entrada invalida considerada | [x] | Entrada ausente, conflitante e invalida considerada |
| Necessidade de autenticacao decidida | [x] | Bearer token obrigatorio |
| Necessidade de autorizacao decidida | [x] | Autorizacao fina adiada; token unico do MVP |
| Dados sensiveis identificados | [x] | Audio, bruto, texto didatico, prompts, respostas e chaves |
| Regras de nao vazamento descritas | [x] | Logs e erros nao podem expor dados sensiveis |
| Uso de `.env`, tokens ou configuracao externa definido | [x] | Variaveis planejadas |
| Motor de pos-processamento substituivel definido | [x] | `llama-server`/API compativel por configuracao |
| Modelo local preferencial definido | [x] | `Qwen3.6-35B-A3B-MTP-Q8.gguf`, conforme benchmark real |
| Autostart do Llama local definido | [x] | Em modo `local`, `MINDVOX_LOCAL_LLM_AUTOSTART=true` tenta iniciar `llama-server`; em `contract`, nao inicia |
| Falha explicita de autostart definida | [x] | Falta de binario, modelo, porta/prontidao ou timeout falha a inicializacao com mensagem clara |
| Teste real comparativo de modelos executado | [x] | Gemma 4 12B Q8, Qwen 27B Q8 e Qwen 35B-A3B Q8 comparados |
| Cinco entregas publicas definidas | [x] | `raw_text`, `didactic_text`, `themes`, `technical_terms` e `technology_mentions` |
| `didactic_text` definido | [x] | Texto corrido, logico, didatico, sem titulos internos e com redundancias semanticas enxugadas |
| `themes` definido para futura E04 | [x] | Organiza nucleos semanticos para navegacao e futura ingestao em memoria |
| `technology_mentions` definido para futura E04 | [x] | Inventaria tecnologias e ferramentas citadas para deduplicacao e enriquecimento futuro |
| Regra de nao inventar tecnologia definida | [x] | Apenas tecnologias citadas ou fortemente indicadas no bruto devem ser listadas |
| `corrected_full_text` quase integral descartado como padrao | [x] | Teste demonstrou duplicacao do bruto com custo maior |
| Provider externo padrao sugerido definido | [x] | Groq com `llama-3.3-70b-versatile` |
| Chave real de provider proibida no repo | [x] | Deve vir de `.env` da instalacao |
| Chave vazia ou placeholder de provider tratada como ausente | [x] | `MINDVOX_LLM_API_KEY` vazia, `replace-with-provider-key` ou `<set-real-key-only-in-local-env>` deve gerar erro controlado em modo `provider` |
| Destino `provider` validado | [x] | Modo `provider` exige URL externa `https`, nao local, loopback ou privada, inclusive apos resolucao DNS |
| Allowlist de provider definida | [x] | `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` restringe hosts externos quando configurada e e obrigatoria em modo publico com provider |
| Destino `local` validado | [x] | Modo `local` exige endpoint local, loopback, privado ou equivalente operacional local |
| Persistencia de processamento E03 definida | [x] | Resposta processada salva JSON tecnico em `MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR` e Markdown humano em `MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR` |
| Fila automatica da E03 definida | [x] | Transcricao gerada por `input_type=audio` entra em fila local para retry automatico se o motor falhar |
| Pagina humana de entrada definida | [x] | Interface operacional distinta do Swagger, com textarea para bruto, metadados e curso ativo persistente |
| Curso ativo persistente definido | [x] | `course_id`/`course_name` entram no contrato humano e no `Study Package`, com seletor de cursos cadastrados |
| Study Package definido | [x] | Envelope canonico com metadados, bruto, texto didatico, temas, termos, tecnologias, ancoras, auditoria, `memory_manifest` e exportacoes |
| Pagina humana de saida definida | [x] | Resultado deve renderizar o `Study Package` em nichos humanos claros |
| Relacao E04 definida sem ingestao na E03 | [x] | E03 prepara `memory_manifest`; E04 ingere em SQLite e campo vetorial |
| Obsidian opcional definido | [x] | Obsidian e exportacao/redundancia, nao dependencia principal |
| Criacao deterministica de Student Vault definida | [x] | V1 cria Vault novo e nao importa/corrige Vault existente |
| Token local automatico definido | [x] | Em `MINDVOX_PUBLIC_DEPLOYMENT=false`, `MINDVOX_API_TOKEN` ausente ou vazio usa `dev-token` local |
| Token placeholder do app tratado como ausente | [x] | `MINDVOX_API_TOKEN` com placeholder nao autentica E02/E03 |
| Token didatico bloqueado em deploy publico | [x] | `dev-token` nao autentica quando `MINDVOX_PUBLIC_DEPLOYMENT=true` |
| Perfis CLI canonicos definidos | [x] | `main`, `contract` e `prod` documentam modos real local, contrato e producao publica |
| Endurecimento publico definido | [x] | `MINDVOX_PUBLIC_DEPLOYMENT`, `MINDVOX_ENABLE_DOCS` e `MINDVOX_TRUSTED_HOSTS` controlam docs e Host header |
| Transporte seguro exigido em deploy publico | [x] | `POST /processed-transcriptions/v1.0.0` retorna `403` quando a aplicacao nao recebe scheme `https` em modo publico |
| Trusted hosts sem wildcard em deploy publico | [x] | `MINDVOX_TRUSTED_HOSTS=*` impede inicializacao quando `MINDVOX_PUBLIC_DEPLOYMENT=true` |
| Limites de metadados opcionais definidos | [x] | `course` ate `160`, `discipline` ate `120`, `class_title` ate `200` caracteres |
| Provider publico sanitizado | [x] | `processing_engine.name` nao reflete provider configurado quando contiver marcador sensivel |
| Upload limitado por leitura incremental | [x] | Leitor compartilhado rejeita audio acima do limite sem leitura integral previa |
| Limite de saida LLM definido | [x] | `MINDVOX_LLM_MAX_OUTPUT_TOKENS` limita tokens solicitados ao motor textual |
| Limite de leitura da resposta LLM definido | [x] | Cliente deve rejeitar resposta excessiva antes de parsear JSON |
| Freio de cobertura semantica definido | [x] | Bruto longo nao pode gerar resumo curto tratado como sucesso; saida insuficiente aciona retry e depois erro controlado se persistir |
| Regua chunked diferenciada definida | [x] | Chunks individuais nao aplicam a regua monolitica completa; a validacao bloqueante de cobertura fica no merge final |
| Falsos positivos de ancoras mitigados | [x] | Palavras discursivas capitalizadas nao devem virar nomes proprios protegidos sem evidencia semantica real |
| Ruido STT repetitivo saneado internamente | [x] | Sequencias repetitivas longas podem ser removidas do texto enviado ao LLM, preservando `raw_text` publico intacto |
| Benchmark com leitura limitada | [x] | Script interno de benchmark rejeita resposta HTTP excessiva |
| Eventos permitidos em log descritos | [x] | Eventos operacionais descritos |
| Dados proibidos em log descritos | [x] | Texto integral, prompt, resposta, token, chave e paths |
| Logs existentes do servidor considerados | [x] | Insuficientes; logger proprio deve ser previsto |
| Necessidade de logger proprio decidida | [x] | Usar logger da aplicacao/servidor com mensagens sanitizadas |
| Persistencia de logs decidida | [x] | Sem persistencia propria de logs no MVP; persistencia operacional externa fica fora da E03 |
| Persistencia do bruto STT no fluxo de audio definida | [x] | `input_type=audio` salva artefatos locais da transcricao bruta antes do pos-processamento |
| Artefato humano da E03 definido | [x] | Toda resposta processada salva `.json` tecnico e `.md` legivel para humano, com nome e titulo humanos derivados de metadados seguros quando disponiveis |
| `summary` definido | [x] | `Post-process class transcription` |
| `description` definida | [x] | Texto sugerido definido com as cinco entregas da E03 |
| Cinco entregas explicadas na documentacao da API | [x] | `raw_text`, `didactic_text`, `themes`, `technical_terms` e `technology_mentions` descritos para o usuario |
| Respostas principais aparecem na documentacao | [x] | Validado por `test_openapi_documents_e03_contract` |
| Parametros/body aparecem corretamente | [x] | Validado por `test_openapi_documents_e03_contract` |
| Descricoes didaticas dos campos aparecem na documentacao | [x] | Validado por `test_openapi_documents_e03_contract` |
| `/openapi.json` reflete o contrato aprovado | [x] | Coberto por teste automatizado, incluindo `Active startup profile` |
| Router definido | [x] | `src/routers/processed_transcriptions.py` criado |
| Handler definido com nome explicavel | [x] | `post_process_class_transcription` criado |
| Router registrado no `app` | [x] | Router incluido em `src/main.py` |
| Endpoint temporario ou exemplo removido | N/A | Nao identificado |
| Dependencias fora do escopo nao sao importadas | [x] | Implementacao usa FastAPI/Pydantic e stdlib para cliente OpenAI-compatible |
| Codigo compila | [x] | `py_compile` passou para arquivos da E03 e testes relacionados |
| Matriz obrigatoria de testes definida | [x] | Secao 17.1 define testes de sucesso, erros, OpenAPI, seguranca, logs e prova humana |
| Pasta propria de testes criada | [x] | `tests/e03_processed_transcriptions/` criada |
| README da pasta de testes criado | [x] | `tests/e03_processed_transcriptions/README.md` criado |
| README da pasta de testes explica hipoteses verificadas | [x] | README cobre sucesso, erros, OpenAPI, seguranca, logs, modo `contract` e prova humana |
| README da pasta de testes explica como executar testes | [x] | README registra comandos da E03 e suite geral |
| Teste documental da matriz de E03 criado | [x] | `test_e03_test_plan_documents_required_contract` garante que README e Spec registram o contrato minimo de testes |
| Teste automatizado de sucesso criado | [x] | Cobre `raw_text` e `audio` em modo `contract` |
| Teste automatizado de erro principal criado | [x] | Cobre token, entrada invalida e motor indisponivel |
| Teste automatizado de metodo invalido criado | [x] | Cobre `405 Method Not Allowed` |
| Teste automatizado do OpenAPI criado | [x] | Valida rota, docs, Bearer, campos e respostas |
| Teste automatizado de limite de tamanho criado | [x] | Cobre `413` para `raw_text` acima do limite configurado |
| Teste automatizado de placeholder de provider criado | [x] | Cobre `503` para `MINDVOX_LLM_API_KEY` vazia ou placeholder em modo `provider` |
| Teste automatizado de timeout criado | [x] | Cobre `504 Gateway Timeout` |
| Teste automatizado de logs sanitizados criado | [x] | Cobre ausencia de bruto, prompt integral, resposta integral, token, chave e path |
| Teste automatizado de erro controlado logado criado | [x] | Cobre status, codigo de erro e duracao sem dados sensiveis |
| Teste automatizado de log de autenticacao criado | [x] | Cobre status, codigo, fase e duracao para falha de autenticacao |
| Teste automatizado de destino LLM criado | [x] | Cobre rejeicao de `provider` local, `provider` resolvido para IP privado e `local` publico |
| Teste automatizado de allowlist provider criado | [x] | Cobre host fora e dentro de `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` |
| Teste automatizado de token placeholder criado | [x] | Cobre `MINDVOX_API_TOKEN` placeholder em E03 |
| Teste automatizado de token didatico em deploy publico criado | [x] | Cobre `dev-token` recusado em `MINDVOX_PUBLIC_DEPLOYMENT=true` |
| Teste automatizado de transporte seguro publico criado | [x] | Cobre `403` para HTTP publico e aceite de scheme `https` |
| Teste automatizado de metadado opcional grande criado | [x] | Cobre `course`, `discipline` e `class_title` acima dos limites |
| Teste automatizado de deploy publico criado | [x] | Cobre exigencia de `MINDVOX_TRUSTED_HOSTS`, docs desabilitados, rejeicao de Host invalido e rejeicao de wildcard |
| Teste automatizado de leitura incremental de upload criado | [x] | Cobre interrupcao antes de ler todo upload acima do limite |
| Teste automatizado de provider sanitizado criado | [x] | Cobre redacao de provider com marcador sensivel em `processing_engine.name` |
| Teste automatizado de limite de saida LLM criado | [x] | Cobre envio de `max_tokens` e rejeicao de resposta excessiva |
| Teste automatizado de cobertura semantica criado | [x] | Cobre rejeicao de saida longa insuficiente e recuperacao por retry com cobertura adequada |
| Teste automatizado de limite no benchmark criado | [x] | Cobre rejeicao de resposta excessiva no script `benchmark_e03_models.py` |
| Teste automatizado de limite LLM invalido criado | [x] | Cobre fallback para padrao quando `MINDVOX_LLM_MAX_OUTPUT_TOKENS=0` |
| Teste automatizado de saida invalida do LLM criado | [x] | Cobre erro controlado sem vazamento da resposta integral |
| Teste automatizado de autostart Llama criado | [x] | Cobre contrato sem start, autostart desabilitado, servidor existente, start, binario ausente, modelo ausente e timeout |
| Teste automatizado de fila E03 criado | [x] | Cobre job concluido, job pendente apos falha e retry sem reupload |
| Comando de teste registrado | [x] | Comandos registrados na Secao 17.1 e no README da pasta de testes |
| Todos os testes passam antes do proximo endpoint | [x] | Suite E03 e suite geral passaram nesta etapa |
| Teste funcional manual real executado e registrado | [ ] | Obrigatorio antes do commit de fechamento da E03; deve ser repetido apos a correcao do freio de cobertura semantica |
| Teste real comparativo Qwen vs Gemma executado ou justificado | [x] | Executado e registrado em `RELATORIO_BENCHMARK_E03_MODELOS_LLM.md` |
| Comando de execucao local documentado | [x] | README e T03 registram modo `contract`, `local` e `provider` |
| Exemplo de chamada valida documentado | [x] | Exemplos definidos nesta Spec |
| Exemplo de falha relevante documentado | [x] | Exemplos definidos nesta Spec |
| Endpoint demonstrado com entrada real representativa | [ ] | Obrigatorio antes do commit |
| Endpoint explicavel por finalidade, entrada, processamento, saida, erro e teste | [x] | Spec fornece base de explicacao |
| Limites de escopo claros | [x] | E04/E05 explicitamente fora da E03 |
| `git status` revisado | [x] | Revisado nesta etapa; revisar novamente antes do commit final |
| `git diff` revisado | [x] | Revisado nesta etapa; revisar novamente antes do commit final |
| Arquivos alterados pertencem ao escopo da E03 ou justificados | [ ] | Executar antes do commit |
| Nenhum segredo, token, `.env`, path sensivel ou dado privado aparece no diff | [x] | Varredura encontrou apenas placeholders documentais esperados |
| Nenhum cache, `__pycache__`, temporario ou artefato gerado indevido aparece no diff | [x] | `git status` nao inclui caches, audios reais ou benchmarks gerados |
| Testes automatizados da E03 passaram | [x] | `uv run python -m unittest discover -s tests/e03_processed_transcriptions -v` passou |
| Testes gerais passaram | [x] | `uv run python -m unittest discover -s tests -v` passou |
| Checklist aplicavel da E03 esta todo marcado ou justificado como `N/A` | [ ] | Executar antes do commit |
| README da pasta de testes esta atualizado | [x] | README ja cobre contrato, erros, seguranca, logs, modo `contract`, provider e placeholder |
| Materiais didaticos externos ao repo foram atualizados | N/A | Nao aplicavel nesta etapa de implementacao de codigo |
| Mensagem de commit planejada identifica a E03 | [ ] | Definir antes do commit |
| Commit de fechamento realizado | [ ] | Ultima acao antes de iniciar E04 |

---

## 19. Decisoes Fechadas Para P03/T03

Decisoes fechadas por esta revisao:

1. `raw_text` deve ser retornado integralmente no MVP, salvo erro por limite configurado.
2. O limite inicial de `raw_text` e `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS=150000`.
3. O perfil `study_notes` deve gerar `didactic_text`, `themes`, `technology_mentions`, `technical_terms` e `processing_notes`.
4. Glossario, roteiro de revisao e revisao integral quase completa ficam fora do MVP da E03.
5. Groq `llama-3.3-70b-versatile` e provider sugerido de portabilidade, nao comparador obrigatorio para fechamento teorico.
6. P03/T03 devem documentar o autostart do `llama-server` por variaveis de ambiente, sem path local fixo na Spec.
7. A demonstracao real deve usar preferencialmente modo `local` com `Qwen3.6-35B-A3B-MTP-Q8.gguf`; se a maquina nao comportar o modelo local, modo `provider` com provider OpenAI-compatible configurado e aceitavel.
8. Entradas acima de `150000` caracteres devem ser rejeitadas com `413 Payload Too Large`; entradas longas abaixo desse limite podem usar chunking interno TF-IDF quando configurado.
9. No fluxo chunked, a preservacao semantica deve ser cobrada em duas camadas:
   prompt local por chunk para produzir JSON valido e material fiel daquele
   bloco; validacao bloqueante de cobertura somente depois do merge canonico.
10. A pre-auditoria pode sanear ruido repetitivo de STT e normalizar formas
   canonicas no texto interno do LLM, mas nao pode substituir o `raw_text`
   publico usado como evidencia auditavel.
11. A E03 deve possuir uma pagina humana de entrada como camada operacional melhor que Swagger, sem remover o contrato HTTP.
12. O curso deve ser contexto persistente do usuario, com `course_id`, `course_name` e seletor de cursos ja cadastrados.
13. A E03 deve produzir `Study Package` como envelope canonico para pagina humana, artefatos locais, futura E04 e exportacoes.
14. A pagina humana de saida deve renderizar o `Study Package` de modo legivel, em nichos como texto didatico, temas, conceitos, tecnologias, ancoras operacionais, bruto auditavel e auditoria.
15. A E04 deve consumir `memory_manifest`; a E03 nao deve gravar memoria relacional nem vetorial.
16. O SQLite e a memoria relacional escolhida para o Mindvox; Obsidian nao e banco relacional principal.
17. Obsidian deve ser opcao local de exportacao e redundancia positiva.
18. A primeira versao da opcao Obsidian deve criar Student Vault novo deterministicamente, sem importar, selecionar, corrigir ou validar Vault existente.

---

## 20. Registro de Estado

Status atual: `implementada_em_validacao_real`.

Motivo:

- a E02 foi fechada funcionalmente e com prova real humana;
- a apresentacao academica se beneficia de um segundo endpoint de IA textual;
- a arquitetura aprovada em conversa separa E03 de E04/E05 para controlar escopo ate sexta-feira;
- E03 deve ficar limitada a pos-processamento de alto nivel, sem banco, memoria ou busca;
- a implementacao HTTP, configuracao, pipeline longo opcional e testes automatizados foram integrados;
- resta prova real humana com motor textual real antes do fechamento canonico.

Esta Spec agora orienta a prova real final da E03 e o commit de fechamento.

Ela nao deve ser marcada como `fechada` enquanto a implementacao, os testes automatizados, a validacao real do OpenAPI, a prova funcional manual humana, a revisao de Git e o commit de fechamento nao estiverem concluidos.
