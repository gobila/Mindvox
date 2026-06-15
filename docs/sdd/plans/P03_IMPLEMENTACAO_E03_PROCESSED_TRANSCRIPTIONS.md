# Plano P03: Implementacao do Endpoint E03 Processed Transcriptions

## 1. Identificacao

- `ID`: `P03`
- `Tipo`: `Plano de Implementacao`
- `Status`: `implementado_em_validacao_real`
- `Spec alvo`: `E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`
- `Endpoint alvo`: `POST /processed-transcriptions/v1.0.0`
- `Data`: `2026-06-10`

---

## 2. Objetivo

Implementar o endpoint de pos-processamento de transcricoes do Mindvox:

```text
POST /processed-transcriptions/v1.0.0
```

O endpoint deve receber audio gravado ou transcricao bruta, autenticar a requisicao, validar entrada e metadados, obter ou preservar `raw_text`, processar o texto por motor substituivel e devolver material de estudo estruturado.

A E03 e o segundo endpoint de IA do MVP academico. Diferente da E02, que executa STT e preserva a transcricao bruta, a E03 transforma esse bruto em material didatico, organizado e semanticamente util.

Nesta emenda de plano, a E03 tambem passa a planejar uma camada humana de uso: pagina de entrada melhor que Swagger, `Study Package` como artefato canonico estruturado, pagina humana de saida, `memory_manifest` para futura E04 e exportacao opcional para Student Vault criado deterministicamente.

Entregas publicas obrigatorias:

- `raw_text`;
- `didactic_text`;
- `themes`;
- `technical_terms`;
- `technology_mentions`.

Campo auxiliar obrigatorio:

- `processing_notes`.

---

## 3. Observacao de Governanca

Este plano deve implementar a E03 sem ampliar o escopo para E04 ou E05.

Regra de conferencia:

- se a implementacao cumprir este plano e a Spec E03, marcar as tarefas correspondentes como concluidas em T03;
- se faltar algo previsto aqui, implementar antes do commit de fechamento da E03;
- se houver excesso fora do escopo, remover ou justificar antes do commit;
- se o plano estiver incompleto em relacao a Spec E03, emendar este plano antes de fechar;
- se a implementacao divergir corretamente da previsao, registrar a justificativa no plano, nas tarefas ou na Spec;
- a E03 nao deve ser marcada como `fechada` antes de implementacao real, testes automatizados, OpenAPI real, prova humana e revisao de Git.

---

## 4. Estado Atual Esperado Antes da E03

Arquivos e capacidades ja existentes:

- `src/main.py`;
- `src/settings.py`;
- `src/routers/health.py`;
- `src/routers/transcriptions.py`;
- `src/schemas/transcriptions.py`;
- `src/services/transcription_service.py`;
- `src/contract/__init__.py`;
- `src/prod/__init__.py`;
- `tests/e01_health/`;
- `tests/e02_transcriptions/`;
- `tests/e03_processed_transcriptions/README.md`;
- `tests/e03_processed_transcriptions/test_e03_test_plan.py`;
- `docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`;
- `docs/sdd/reports/RELATORIO_ARQUITETURA_E_ESCOPO_E03_E05.md`;
- `docs/sdd/reports/RELATORIO_BENCHMARK_E03_MODELOS_LLM.md`;
- `docs/sdd/reports/RELATORIO_DIRETRIZES_E03_SERVICO_IA_LLM.md`;
- `docs/sdd/reports/RELATORIO_SINTESE_E03_CHUNKING_PIPELINE_VAULT.md`;
- `docs/sdd/reports/RELATORIO_E03_INTERFACE_STUDY_PACKAGE_E_VAULT_OPCIONAL.md`;
- `scripts/benchmark_e03_models.py`.

Situacao esperada:

- `GET /health` deve continuar funcionando;
- `POST /transcriptions/v1.0.0` deve continuar funcionando;
- a E02 deve continuar sendo a fonte de STT bruta;
- a E03 deve reaproveitar internamente o servico de transcricao da E02 quando receber audio;
- a E03 nao deve chamar a E02 por HTTP dentro do mesmo app;
- `.env` deve continuar fora do Git;
- `.benchmarks/`, caches, audios reais e transcricoes reais de teste devem continuar fora do Git;
- a pasta de testes da E03 ja existe e deve ser expandida com os testes executaveis do endpoint.

---

## 5. Decisoes de Implementacao

Implementacao proposta:

- criar router proprio para a E03;
- registrar esse router em `src/main.py`;
- exigir autenticacao por `Authorization: Bearer <token>`;
- reutilizar o token do MVP lido por `MINDVOX_API_TOKEN`;
- em desenvolvimento local, usar `dev-token` automaticamente quando `MINDVOX_API_TOKEN` estiver ausente ou vazio;
- manter `dev-token` bloqueado em `MINDVOX_PUBLIC_DEPLOYMENT=true`;
- manter autenticacao Bearer tambem no modo `contract`, para testar o contrato de seguranca dos endpoints protegidos;
- receber `multipart/form-data`;
- tipar `input_type` como `Enum` no OpenAPI, para que o Swagger apresente lista de selecao/dropdown em vez de campo textual livre;
- aceitar `input_type=audio` ou `input_type=raw_text`;
- aceitar `input_type=raw_text_file` como alias ergonomico de Swagger para `raw_text` quando o usuario anexar arquivo `.txt`;
- aceitar `audio_file` apenas quando `input_type=audio`;
- aceitar `raw_text` colado apenas quando `input_type=raw_text`;
- aceitar `raw_text_file` em `.txt` apenas quando `input_type=raw_text`, para reprocessar transcricao ja existente sem reenviar audio;
- rejeitar `audio_file` enviado junto com `raw_text` ou `raw_text_file`;
- rejeitar `raw_text` e `raw_text_file` enviados juntos;
- garantir que campos textuais opcionais iniciem vazios no OpenAPI/Swagger;
- tratar defensivamente valor literal `string` em campo textual opcional como ausente quando vier de cliente antigo ou Swagger cacheado;
- validar `course`, `discipline`, `class_date`, `class_title`, `session_label`, `language` e `processing_profile`;
- usar `study_notes` como unico `processing_profile` do MVP;
- rejeitar `processing_profile` fora dos valores aceitos;
- rejeitar `raw_text` acima de `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS=150000` com `413 Payload Too Large`;
- aceitar audio nas mesmas extensoes basicas da E02: `.wav` e `.m4a`;
- se receber audio, chamar internamente a camada de transcricao ja usada pela E02;
- se receber texto bruto colado ou em `.txt`, enviar o conteudo diretamente ao servico de pos-processamento;
- manter a logica de transcricao e de LLM fora do router;
- criar camada de servico de pos-processamento;
- criar cliente OpenAI-compatible para modo `local` e modo `provider`;
- criar runtime local para iniciar `llama-server` automaticamente quando o modo real/local exigir;
- falhar a inicializacao de forma explicita se o `llama-server` automatico nao puder ser encontrado, iniciado ou verificado;
- criar perfis de inicializacao simples: `main` para desenvolvimento real local, `contract` para teste de contrato sem Llama e `prod` para endurecimento de producao publica;
- validar destino do cliente LLM conforme modo: `provider` externo `https`; `local` local/privado/loopback;
- enviar limite de tokens ao motor LLM por `MINDVOX_LLM_MAX_OUTPUT_TOKENS`;
- limitar bytes lidos da resposta LLM antes de parsear JSON;
- salvar artefato local de toda resposta processada da E03;
- quando `input_type=audio`, enfileirar a transcricao bruta gerada antes do pos-processamento;
- manter job pendente para retry automatico se o pos-processamento falhar apos STT;
- reprocessar jobs pendentes automaticamente quando o app estiver rodando com motor real disponivel;
- manter modo `contract` para testes automatizados e demonstracao controlada;
- nao apresentar modo `contract` como pos-processamento real;
- implementar pipeline interno opcional para transcricoes longas, com
  pre-auditoria, chunking TF-IDF, contexto de pre-auditoria no prompt, merge
  canonico e auditoria final;
- criar camada humana de entrada da E03, distinta do Swagger, com textarea real para `raw_text`;
- manter Swagger como documentacao tecnica e console de teste, nao como UI principal de usuario;
- introduzir `course_id`, `course_name`, `institution`, `class_number` e `session_number` como metadados planejados da interface humana e do `Study Package`;
- persistir curso ativo na camada de interface/configuracao do usuario, com seletor/lista de cursos ja cadastrados;
- normalizar fluxos de entrada vindos de pagina humana, Swagger/API e script local do Obsidian para um contrato interno unico;
- criar `Study Package` como artefato estruturado canonico envolvendo as cinco entregas, metadados, fonte, ancoras operacionais, conceitos candidatos, auditoria, `memory_manifest` e exportacoes;
- criar pagina humana de resultado para renderizar o `Study Package` em nichos claros;
- exibir automaticamente a pagina/modal/drawer de resultado ao fim de processamento iniciado pela pagina humana;
- criar `memory_manifest` para futura E04, sem executar ingestao de memoria dentro da E03;
- tratar SQLite como memoria relacional escolhida para o Mindvox no desenho de E04;
- tratar Obsidian como exportacao opcional e redundancia positiva, nao como banco relacional principal;
- criar script/servico opcional para criar Student Vault novo deterministicamente a partir dos metadados de curso;
- nao importar, selecionar, validar ou corrigir Vault existente na primeira versao da opcao Obsidian;
- criar exportador opcional que projete o `Study Package` nos nichos padronizados do Student Vault criado;
- manter fluxo curto atual para entradas abaixo do limite configurado;
- preservar `raw_text` original na resposta publica, mesmo quando o motor textual
  receber internamente texto saneado pela pre-auditoria;
- garantir que suspeitas remanescentes da pre-auditoria nao sejam promovidas a
  `didactic_text`, `themes`, `technical_terms` ou `technology_mentions` sem
  evidencia independente;
- retornar erro controlado quando motor de pos-processamento estiver indisponivel;
- retornar erro controlado quando motor de pos-processamento exceder timeout;
- registrar logs operacionais sem bruto integral, texto processado integral, prompt integral, resposta integral, token, chave, `.env` ou path sensivel;
- nao persistir memoria, embeddings, banco relacional, banco vetorial ou busca.

### 5.1 Arquitetura Interna Obrigatoria

Fluxo correto:

```text
E03 router
  -> validacao/autenticacao
  -> transcription_service, somente quando input_type=audio
  -> artefato bruto e fila E03, somente quando input_type=audio
  -> postprocessing_service
  -> artefato processado e conclusao da fila, quando houver sucesso
  -> resposta E03
```

Fluxo proibido:

```text
E03 router -> HTTP -> POST /transcriptions/v1.0.0
```

Motivo:

- evitar acoplamento HTTP interno;
- reduzir latencia;
- facilitar testes;
- preservar responsabilidade dos endpoints;
- manter composicao na camada de servicos.

### 5.2 Motor de Pos-processamento

A E03 deve ter motor substituivel por configuracao.

Modos:

| Modo | Uso |
| --- | --- |
| `contract` | Testes automatizados e demonstracao controlada do contrato |
| `local` | Pos-processamento real via servidor local OpenAI-compatible, preferencialmente `llama-server` |
| `provider` | Pos-processamento real via provider externo OpenAI-compatible |

Modelo local preferencial:

```text
Qwen3.6-35B-A3B-MTP-Q8.gguf
```

Nome operacional recomendado:

```text
qwen35a3b-q8
```

Provider externo sugerido:

```text
groq / llama-3.3-70b-versatile
```

Regras:

- o path local do modelo nao deve ser hard-coded;
- o contrato HTTP nao deve depender do nome fisico do arquivo GGUF;
- `Gemma 4 12B Q8` permanece candidato alternativo, nao padrao;
- `Qwen3.6-27B-MTP-Q8_0.gguf` permanece baseline historico, nao padrao;
- qualquer substituicao do modelo preferencial exige nova prova real demonstravel ou justificativa expressa.
- em modo `local`, o app deve tentar iniciar o `llama-server` automaticamente quando `MINDVOX_LOCAL_LLM_AUTOSTART=true`;
- em modo `contract`, o app nao deve iniciar `llama-server`;
- falha de binario, modelo, porta/prontidao ou timeout do `llama-server` deve aparecer no terminal como erro claro de inicializacao.

### 5.3 Produto Textual Obrigatorio

A E03 nao deve gerar, por padrao, `corrected_full_text` quase integral.

A resposta deve priorizar:

- enxugamento de redundancias semanticas;
- preservacao dos nucleos relevantes da aula;
- texto didatico continuo, sem titulos internos;
- temas semanticos estruturados;
- termos tecnicos normalizados;
- tecnologias citadas;
- lastro bruto preservado em `raw_text`.

Se houver duvida sobre perda ou distorcao, o usuario deve conferir o resultado processado contra `raw_text`.

### 5.4 Pipeline Longo de Alta Fidelidade

Para transcricoes longas, a implementacao deve permitir o seguinte fluxo interno:

```text
raw_text original
  -> pre-auditoria E02/E03
  -> texto saneado para o Qwen
  -> chunking TF-IDF
  -> processamento de cada chunk pelo postprocessing_service
  -> merge canonico deterministico
  -> auditoria final dos campos semanticos
  -> resposta publica E03
```

Configuracoes planejadas:

| Variavel | Default | Finalidade |
| --- | --- | --- |
| `MINDVOX_POSTPROCESSING_CHUNKING_MODE` | `tfidf` no perfil `dev`; `off` como fallback/override | `tfidf` ativa pipeline longo; `off` preserva chamada unica para diagnostico |
| `MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS` | `20000` | Tamanho minimo para ativar chunking |
| `MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS` | `5000` | Tamanho alvo aproximado de chunks |
| `MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED` | `true` | Liga pre-auditoria lexical antes do LLM |
| `MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED` | `true` | Liga auditoria final dos artefatos semanticos |

Escopo inicial da integracao:

- usar TF-IDF em memoria, sem banco vetorial;
- normalizar formas canonicas ja validadas em bancada;
- adicionar contexto de pre-auditoria ao prompt;
- deduplicar listas e recompor texto em merge deterministico;
- processar cada chunk com prompt local de preservacao, mas sem aplicar a
  regua monolitica completa de cobertura semantica antes do merge;
- aplicar a regua semantica dura ao artefato mesclado final, com razao propria
  para fluxo chunked e notas de auditoria para ancoras heuristicas ausentes;
- nao exigir clipe/re-STT no runtime quando a requisicao nao fornecer audio
  acessivel por path local persistente;
- manter a auditoria com audio/clipes como ferramenta de bancada ate nova
  decisao de integracao.

Justificativa:

- benchmarks A1S1 e A1S2 mostraram que o Qwen 35B-A3B Q8 funciona melhor quando
  recebe blocos menores e semanticamente saneados;
- a pre-auditoria v3 reduziu residuos finais para `0` issues na auditoria
  final corrigida;
- o smoke test com contexto de pre-auditoria impediu que `PNI`, uma suspeita
  remanescente, fosse promovida para os campos principais.

### 5.5 Interface Humana, Study Package e Vault Opcional

Esta fase deve ser implementada como camada complementar da E03, sem quebrar o endpoint versionado.

Fluxo humano alvo:

```text
pagina humana de entrada
  -> entrada por audio, texto colado ou arquivo `.txt`
  -> metadados de curso/aula/sessao
  -> normalizacao para o contrato interno E03
  -> pipeline E03
  -> Study Package
  -> pagina humana de resultado
```

Fluxo local/dev com Obsidian:

```text
Student Vault/00_Inbox/_captura-rapida.md
  -> script extrai propriedades e sessao ativa
  -> gera `.txt` em `inputs/e03_raw_texts/`
  -> gera metadados auxiliares
  -> preenche de modo visivel a pagina humana da E03 ou produz entrada equivalente
```

Fluxo opcional de criacao de Vault:

```text
usuario informa course_id/course_name/institution e path base
  -> Mindvox cria Student Vault novo deterministicamente
  -> curso ativo recebe vault_path
  -> Study Package futuro pode ser exportado para esse Vault
```

Regras:

- a pagina humana deve aceitar usuario sem Obsidian;
- a pagina humana deve ter `raw_text` como textarea ou componente equivalente amplo;
- o curso ativo deve persistir ate mudanca explicita;
- cursos ja cadastrados devem aparecer em seletor/lista flutuante;
- o `Study Package` deve ser salvo como artefato tecnico e renderizavel em pagina humana;
- o `memory_manifest` deve preparar a E04, sem persistir memoria na E03;
- o exportador Obsidian deve operar apenas sobre `Study Package` ja produzido;
- a primeira versao da opcao Obsidian deve criar Vault novo e nao importar Vault existente.

---

## 6. Arquivos Planejados

Arquivos de codigo:

- `src/main.py`;
- `src/settings.py`;
- `src/routers/processed_transcriptions.py`;
- `src/schemas/__init__.py`;
- `src/schemas/processed_transcriptions.py`;
- `src/services/__init__.py`;
- `src/services/transcription_service.py`;
- `src/services/postprocessing_service.py`;
- `src/services/postprocessing_pipeline.py`;
- `src/services/llm_client.py`;
- `src/services/local_llm_runtime.py`;
- `src/services/processed_transcription_artifacts.py`;
- `src/services/processed_transcription_queue.py`;
- `src/services/e03_study_package.py`;
- `src/services/e03_course_context.py`;
- `src/services/e03_vault_scaffold.py`;
- `src/services/e03_vault_exporter.py`.

Arquivos de teste:

- `tests/e03_processed_transcriptions/__init__.py`;
- `tests/e03_processed_transcriptions/README.md`;
- `tests/e03_processed_transcriptions/test_e03_test_plan.py`;
- `tests/e03_processed_transcriptions/test_processed_transcriptions.py`;
- `tests/e03_processed_transcriptions/test_local_llm_runtime.py`;
- `tests/e03_processed_transcriptions/test_e03_study_package.py`;
- `tests/e03_processed_transcriptions/test_e03_course_context.py`;
- `tests/e03_processed_transcriptions/test_e03_vault_export.py`.

Arquivos de documentacao e configuracao:

- `.env.example`;
- `.gitignore`;
- `README.md`;
- `docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`;
- `docs/sdd/plans/P03_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`;
- `docs/sdd/tasks/T03_TAREFAS_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`;
- `docs/sdd/reports/RELATORIO_CORRECAO_AUDITORIA_IMPLEMENTACAO_E03.md`.
- `docs/sdd/reports/RELATORIO_SINTESE_E03_CHUNKING_PIPELINE_VAULT.md`;
- `docs/sdd/reports/RELATORIO_E03_INTERFACE_STUDY_PACKAGE_E_VAULT_OPCIONAL.md`;
- `docs/sdd/reports/README.md`.

Script auxiliar:

- `scripts/benchmark_e03_models.py`.
- `scripts/prepare_e03_raw_text_from_vault.py`;
- `scripts/create_student_vault.py`.

Regra:

- qualquer arquivo adicional deve ser justificado antes do commit;
- arquivos gerados, caches, `.env`, audios reais, transcricoes reais, saidas de benchmark, chaves e tokens reais nao devem entrar no Git.

---

## 7. Configuracao Planejada

Variaveis esperadas:

| Variavel | Finalidade | Regra |
| --- | --- | --- |
| `MINDVOX_API_TOKEN` | Token local do MVP para autenticar o endpoint | Ausente ou vazio usa `dev-token` em desenvolvimento local; em producao publica exige token forte externo |
| `MINDVOX_PUBLIC_DEPLOYMENT` | Ativa endurecimento para exposicao publica | Padrao `false`; quando `true`, exige hosts confiaveis |
| `MINDVOX_ENABLE_DOCS` | Controla `/docs`, `/redoc` e `/openapi.json` | Padrao `true` localmente e `false` em deploy publico |
| `MINDVOX_TRUSTED_HOSTS` | Hosts aceitos pelo app | Obrigatorio quando `MINDVOX_PUBLIC_DEPLOYMENT=true` |
| `MINDVOX_RUNTIME_PROFILE` | Perfil operacional exibido no Swagger | Normalmente inferido ou definido pelos perfis `main`, `contract` e `prod`; valores: `dev`, `contract`, `prod` |
| `MINDVOX_POSTPROCESSING_MODE` | Define `auto`, `contract`, `local` ou `provider` | Padrao recomendado `auto`: acompanha `MINDVOX_TRANSCRIPTION_MODE`; `contract` para testes automatizados; `local` ou `provider` para teste real |
| `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS` | Limite maximo de `raw_text` | Padrao local: `150000`, definido para aula de ate aproximadamente duas horas com margem pragmatica |
| `MINDVOX_POSTPROCESSING_CHUNKING_MODE` | Estrategia interna para entrada longa | Perfil `dev` define `tfidf` por padrao; `off` pode ser usado como override diagnostico |
| `MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS` | Tamanho minimo para acionar o pipeline longo | Padrao `20000`; so vale quando `CHUNKING_MODE=tfidf` |
| `MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS` | Tamanho alvo aproximado por chunk interno | Padrao `5000`; controla a carga enviada ao motor textual por chamada |
| `MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED` | Liga pre-auditoria lexical sistemica | Padrao `true`; normaliza formas canonicas validadas antes do LLM sem alterar `raw_text` publico |
| `MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED` | Liga auditoria final deterministica | Padrao `true`; filtra suspeitas remanescentes dos artefatos semanticos e registra notas |
| `MINDVOX_LLM_PROVIDER` | Nome do provider externo, quando aplicavel | Sugerido: `groq` |
| `MINDVOX_LLM_BASE_URL` | URL base OpenAI-compatible | Local: servidor `llama-server`; provider Groq sugerido: `https://api.groq.com/openai/v1` |
| `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` | Allowlist de hostnames externos aceitos em modo `provider` | Sugerido: `api.groq.com`; obrigatorio para provider em deploy publico |
| `MINDVOX_LLM_MODEL` | Modelo textual usado no pos-processamento | Local preferencial: `qwen35a3b-q8`; provider sugerido: `llama-3.3-70b-versatile` |
| `MINDVOX_LLM_API_KEY` | Chave externa, quando aplicavel | Obrigatoria em modo `provider`; nao deve entrar no Git |
| `MINDVOX_LLM_MAX_OUTPUT_TOKENS` | Limite de tokens de saida solicitado ao motor textual | Padrao local da E03: `20000`, definido para aula de ate aproximadamente duas horas com preservacao semantica alta |
| `MINDVOX_LLM_TIMEOUT_SECONDS` | Timeout maximo do motor textual | Padrao local da E03: `1200` segundos |
| `MINDVOX_LOCAL_LLM_AUTOSTART` | Liga autostart do `llama-server` em modo `local` | Padrao recomendado: `true` |
| `MINDVOX_LLAMA_SERVER_PATH` | Caminho opcional do binario `llama-server` | Vazio permite autodeteccao |
| `MINDVOX_LOCAL_LLM_MODEL_PATH` | Caminho opcional do GGUF local | Vazio permite autodeteccao local documentada |
| `MINDVOX_LLAMA_SERVER_CTX_SIZE` | Contexto usado no `llama-server` automatico | Padrao local da E03: `65536` |
| `MINDVOX_LLAMA_SERVER_GPU_LAYERS` | Camadas GPU usadas no `llama-server` automatico | Padrao inicial: `99` |
| `MINDVOX_LLAMA_SERVER_PARALLEL` | Quantidade de slots do `llama-server` automatico | Padrao local da E03: `1`, pois a prioridade e uma chamada longa de qualidade por vez |
| `MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS` | Timeout para o motor local ficar pronto | Padrao inicial: `240` |
| `MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR` | Diretorio local dos artefatos processados da E03 | Padrao: `outputs/processed_transcriptions` |
| `MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR` | Diretorio local do Markdown humano da E03 | Padrao: `outputs/human/processed_transcriptions`; proprio do modo `dev`/instalacao local |
| `MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR` | Diretorio local de quarentena tecnica para saidas LLM reprovadas pela auditoria semantica | Padrao: `outputs/processed_transcriptions/rejected` |
| `MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR` | Diretorio local de relatorios humanos para saidas LLM reprovadas | Padrao: `outputs/human/processed_transcriptions/rejected` |
| `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_ENABLED` | Liga fila local de retry da E03 | Padrao recomendado: `true` |
| `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS` | Intervalo de retry da fila E03 | Padrao inicial: `60` |
| `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS` | Limite de tentativas antes de mover job para `queue/failed/` | Padrao inicial: `3` |
| `MINDVOX_MAX_UPLOAD_MB` | Limite de upload de audio herdado da E02 | Usado quando E03 receber audio |
| `MINDVOX_TRANSCRIPTION_MODE` | Modo do servico de transcricao herdado da E02 | Usado quando E03 receber audio |
| `MINDVOX_TRANSCRIPTION_MODEL` | Modelo STT herdado da E02 | Padrao final de qualidade: `mlx-community/whisper-large-v3-turbo-fp16` |
| `MINDVOX_TRANSCRIPTION_OUTPUT_DIR` | Pasta local do JSON tecnico da STT herdada da E02 | Usada quando E03 receber audio e gerar transcricao interna |
| `MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR` | Pasta local do TXT humano da STT herdada da E02 | Usada quando E03 receber audio e gerar transcricao interna |
| `MINDVOX_E03_HUMAN_UI_ENABLED` | Liga pagina humana local da E03 | Padrao `true` em `dev`; em producao depende do empacotamento da aplicacao |
| `MINDVOX_E03_ACTIVE_COURSE_STORE` | Arquivo/local de configuracao para curso ativo e cursos cadastrados | Padrao local sugerido: `outputs/config/e03_courses.json` |
| `MINDVOX_E03_STUDY_PACKAGE_OUTPUT_DIR` | Diretorio local dos Study Packages | Padrao: `outputs/study_packages` |
| `MINDVOX_E03_OBSIDIAN_EXPORT_ENABLED` | Liga exportacao opcional para Student Vault | Padrao `false` |
| `MINDVOX_E03_OBSIDIAN_VAULTS_BASE_DIR` | Path base onde novos Vaults podem ser criados | Obrigatorio somente quando exportacao/criacao de Vault estiver ativa |
| `MINDVOX_E03_OBSIDIAN_VAULT_CREATE_ONLY` | Garante que a v1 cria Vault novo e nao importa Vault existente | Padrao `true` |

Regras:

- valores reais de token e chave devem ficar fora do codigo e fora do Git;
- `.env.example` deve documentar nomes e exemplos ficticios;
- `MINDVOX_POSTPROCESSING_MODE=auto` deve atrelar os modos: transcricao `contract` deriva pos-processamento `contract`; transcricao `real` deriva pos-processamento `local`;
- a entrada principal `main` deve normalizar `fastapi dev` para perfil `dev`, com transcricao `real`, pos-processamento `auto` e `MINDVOX_POSTPROCESSING_CHUNKING_MODE=tfidf`, impedindo reaproveitamento acidental de modo `contract` herdado no ambiente;
- `MINDVOX_API_TOKEN` ausente ou vazio deve usar `dev-token` somente em desenvolvimento local com `MINDVOX_PUBLIC_DEPLOYMENT=false`;
- placeholder de exemplo, como `replace-with-local-token` ou `<set-real-token-only-in-local-env>`, deve ser tratado como token ausente;
- `dev-token` deve ser tratado como token ausente quando `MINDVOX_PUBLIC_DEPLOYMENT=true`;
- modo `contract` deve continuar exigindo Bearer token para testar o contrato de seguranca dos endpoints protegidos;
- Swagger/OpenAPI deve exibir `Active startup profile` no cabecalho da API, indicando `dev`, `contract` ou `prod`;
- `MINDVOX_LLM_API_KEY` vazio ou com placeholder de exemplo, como `replace-with-provider-key` ou `<set-real-key-only-in-local-env>`, deve ser tratado como ausente;
- `.env` real deve permanecer ignorado;
- mensagens de erro e logs nao devem revelar valores dessas variaveis;
- chave de provider nao deve ser enviada pelo Swagger ou corpo da requisicao;
- modo `provider` deve rejeitar URL local, loopback ou privada;
- modo `provider` deve rejeitar hostname que resolva por DNS para IP local, privado, loopback, link-local, reservado, multicast ou indefinido;
- modo `provider` deve rejeitar host fora de `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` quando allowlist estiver configurada;
- modo `local` com `MINDVOX_LOCAL_LLM_AUTOSTART=true` deve iniciar ou reaproveitar `llama-server` automaticamente;
- modo `contract` nao deve iniciar `llama-server`;
- falha de autostart local deve falhar a inicializacao com erro claro;
- transcricao gerada por `input_type=audio` deve entrar em fila local de pos-processamento;
- falha de pos-processamento apos STT deve manter job pendente para retry automatico;
- resposta processada da E03 deve ser salva em artefato local;
- resposta processada da E03 deve gerar `.json` tecnico em `outputs/processed_transcriptions/` para integracoes/E04 e `.md` humano em `outputs/human/processed_transcriptions/` para leitura direta no modo `dev`;
- a E03 deve gerar `Study Package` em `MINDVOX_E03_STUDY_PACKAGE_OUTPUT_DIR`, mantendo compatibilidade com os artefatos `.json` e `.md` atuais;
- curso ativo e lista de cursos cadastrados devem ser armazenados localmente em instalacao dev, sem exigir preenchimento repetido do curso em cada processamento;
- se `MINDVOX_E03_OBSIDIAN_EXPORT_ENABLED=false`, nenhum fluxo deve exigir Obsidian;
- se a opcao Obsidian estiver ativa, `MINDVOX_E03_OBSIDIAN_VAULTS_BASE_DIR` deve existir ou gerar erro controlado;
- a criacao de Vault deve ser deterministica e limitada a Vault novo, sem importar ou corrigir Vault existente;
- se `MINDVOX_PUBLIC_DEPLOYMENT=true`, o app deve exigir `MINDVOX_TRUSTED_HOSTS`, rejeitar `MINDVOX_TRUSTED_HOSTS=*` e desabilitar docs por padrao;
- se `MINDVOX_PUBLIC_DEPLOYMENT=true`, os endpoints de negocio protegidos devem exigir que a aplicacao receba scheme `https`;
- se TLS terminar em proxy, o proxy e o servidor ASGI devem ser configurados de modo confiavel para repassar o scheme `https`; a aplicacao nao deve confiar em header `X-Forwarded-Proto` enviado livremente pelo cliente;
- a exigencia de transporte seguro na aplicacao deve ser tratada como defesa em profundidade, sem substituir TLS, rate limiting, limite de corpo e bloqueio de acesso direto ao processo ASGI na camada de deploy;
- modo `local` deve rejeitar URL publica;
- resposta excessiva do LLM deve ser rejeitada antes do parse;
- saida quase correta do LLM deve ser normalizada defensivamente para o contrato E03 quando houver produto humano principal, aceitando aliases previsiveis, cerca Markdown, valores de confianca em portugues e categorias equivalentes;
- saida sem `didactic_text` ou alias equivalente deve continuar sendo invalida, pois nao ha produto humano principal a preservar;
- saida estruturalmente valida, mas semanticamente insuficiente para bruto longo, deve ser rejeitada: a primeira ocorrencia aciona retry com instrucao mais rigorosa de preservacao; a segunda falha retorna `502` estruturado com `error_code=postprocessing_quality_rejected`, salva a saida recusada em `rejected/` com `runtime_snapshot` da execucao e nao e tratada como sucesso;
- jobs de audio com falhas repetidas devem respeitar `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS`; ao atingir o limite, devem sair de `pending` e ir para `queue/failed/`, encerrando retry automatico;
- a checagem de cobertura deve detectar ancoras semanticas protegidas no bruto, como projetos, empresas, tecnologias, arquiteturas, dores de implementacao, cases e contribuicoes nominais de alunos, listar essas ancoras no prompt e rejeitar saida longa que as omita mesmo quando tamanho e quantidade de temas parecerem suficientes;
- palavras capitalizadas de discurso comum, como "Então", "Acho", "Alguém" e
  "Temos", nao devem virar ancoras semanticas protegidas apenas por aparecerem
  em frases com pistas de participacao estudantil;
- a pre-auditoria pode remover sequencias repetitivas longas de ruido STT no
  texto interno enviado ao LLM, desde que preserve `raw_text` publico intacto;
- no fluxo longo com chunking TF-IDF, a checagem final deve diferenciar compactacao legitima de resumo editorial: a razao minima de tamanho do `didactic_text` pode ser reduzida no merge canonico, temas estruturados permanecem obrigatorios e ancoras protegidas ausentes devem ser registradas como nota `semantic_anchor_audit`, sem derrubar a resposta inteira, porque essa lista de ancoras e heuristica no fluxo fragmentado;
- no fluxo longo com chunking TF-IDF, chunks individuais nao devem receber a
  regua monolitica completa de tamanho, temas e ancoras; a validacao bloqueante
  de cobertura pertence ao merge final;
- `processing_notes` nao deve satisfazer cobertura de ancoras semanticas, pois e rastreabilidade operacional e nao artefato estudantil principal;
- o prompt operacional deve explicitar que E03 nao faz resumo editorial, deve preservar projetos, cases, contribuicoes de alunos, dores reais, exemplos, metaforas, arquiteturas, tecnologias e decisoes metodologicas que acrescentem conteudo novo;
- script interno de benchmark deve aplicar limite equivalente de leitura de resposta HTTP;
- `processing_engine.name` deve sanitizar o nome do provider antes de expor a resposta publica;
- uploads de audio devem ser lidos em blocos com rejeicao imediata quando `MINDVOX_MAX_UPLOAD_MB` for excedido;
- logs de falha de autenticacao devem registrar `status_code`, `error_code`, `phase=auth` e duracao, sem token ou header;
- em modo `provider`, o conteudo de `raw_text` ou a transcricao gerada a partir do audio sera enviado ao provider externo configurado;
- modo `local` deve ser preferido quando o conteudo nao puder sair da maquina;
- a documentacao da API, o README e a prova humana devem deixar essa diferenca de privacidade explicita.

Configuracao operacional sugerida para provider externo:

```env
MINDVOX_POSTPROCESSING_MODE=provider
MINDVOX_LLM_PROVIDER=groq
MINDVOX_LLM_BASE_URL=https://api.groq.com/openai/v1
MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS=api.groq.com
MINDVOX_LLM_MODEL=llama-3.3-70b-versatile
MINDVOX_LLM_API_KEY=<set-real-key-only-in-local-env>
MINDVOX_LLM_MAX_OUTPUT_TOKENS=20000
MINDVOX_LLM_TIMEOUT_SECONDS=1200
```

Configuracao operacional sugerida para modelo local:

```env
MINDVOX_POSTPROCESSING_MODE=local
MINDVOX_LLM_BASE_URL=http://127.0.0.1:8080/v1
MINDVOX_LLM_MODEL=qwen35a3b-q8
MINDVOX_LLM_MAX_OUTPUT_TOKENS=20000
MINDVOX_LLM_TIMEOUT_SECONDS=1200
MINDVOX_LOCAL_LLM_AUTOSTART=true
MINDVOX_LLAMA_SERVER_PATH=
MINDVOX_LOCAL_LLM_MODEL_PATH=
MINDVOX_LLAMA_SERVER_CTX_SIZE=65536
MINDVOX_LLAMA_SERVER_GPU_LAYERS=99
MINDVOX_LLAMA_SERVER_PARALLEL=1
MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS=240
```

Comportamento de autostart do `llama-server`:

- a aplicacao tenta reaproveitar servidor local ja ativo se `/v1/models` responder corretamente;
- se nao houver servidor ativo, tenta iniciar `llama-server` automaticamente;
- `MINDVOX_LOCAL_LLM_MODEL_PATH` e configuracao operacional local e nao faz parte do contrato HTTP da E03;
- o path real do GGUF nao deve ser gravado na Spec, no Plano, no codigo, nos testes ou em logs;
- a aplicacao deve conversar com o servidor por `MINDVOX_LLM_BASE_URL` e `MINDVOX_LLM_MODEL`;
- o app deve iniciar o `llama-server` local com `--ctx-size 65536` e `--parallel 1` por padrao, preservando contexto para uma aula de ate aproximadamente duas horas e evitando slots concorrentes desnecessarios;
- em modo `local`, o cliente deve enviar `chat_template_kwargs.enable_thinking=false` ao `llama-server`, para impedir que modelos Qwen retornem apenas `reasoning_content` e deixem o JSON final vazio;
- se o servidor local nao puder ficar pronto em modo `local`, a aplicacao deve falhar a inicializacao de forma clara;
- se o servidor local nao responder dentro de `MINDVOX_LLM_TIMEOUT_SECONDS`, a E03 deve retornar `504 Gateway Timeout`.

---

## 8. Contrato HTTP Planejado

Metodo:

```text
POST
```

Rota:

```text
/processed-transcriptions/v1.0.0
```

Entrada:

```text
multipart/form-data
```

Campos:

| Campo | Obrigatoriedade | Regra |
| --- | --- | --- |
| `input_type` | obrigatorio | `Enum` no OpenAPI/Swagger com `audio`, `raw_text` e alias `raw_text_file` |
| `audio_file` | condicional | Obrigatorio quando `input_type=audio`; proibido quando `input_type=raw_text` |
| `raw_text` | condicional | Texto colado quando `input_type=raw_text`; alternativa a `raw_text_file`; proibido quando `input_type=audio` |
| `raw_text_file` | condicional | Arquivo `.txt` com transcricao bruta quando `input_type=raw_text`; alternativa a `raw_text`; proibido quando `input_type=audio` |
| `course` | opcional | Curso ou contexto geral |
| `discipline` | opcional | Disciplina associada |
| `class_date` | opcional | `YYYY-MM-DD` |
| `class_title` | opcional | Titulo ou tema da aula |
| `session_label` | opcional | Identificador curto |
| `language` | opcional | Padrao `pt-BR` |
| `processing_profile` | opcional | Padrao e unico perfil do MVP: `study_notes` |

Regra de consistencia para arquivos preparados localmente:

- quando `raw_text_file` tiver nome no padrao gerado pelo Mindvox, como `2026-05-09-api-rogerio-aula-1-sessao-4.txt`, o backend deve usar esse nome como fonte de defaults para metadados ausentes;
- se `class_date`, `discipline`, `class_title` ou `session_label` forem enviados no formulario, o endpoint deve preservar esses valores explicitos, pois eles continuam sendo metadados opcionais e publicos do contrato da API;
- diferencas entre metadados recebidos e defaults inferidos do nome preparado devem ser registradas em log saneado, mas nao devem retornar `422`;
- o endpoint deve registrar em log apenas filename e metadados saneados recebidos, sem bruto, prompt, token ou chave, para permitir auditoria de divergencia;
- usuarios externos continuam podendo usar Swagger normalmente; a inferencia pelo nome preparado nao deve restringir a liberdade dos metadados opcionais.

Header obrigatorio:

```text
Authorization: Bearer <token>
```

Descricoes didaticas no OpenAPI:

- todos os campos devem ter descricao didatica em ingles;
- todos os campos devem ter exemplo curto;
- `input_type` deve ser documentado como `Enum` com opcoes visiveis no Swagger;
- as descricoes abaixo devem ser usadas como base textual canonica para evitar perda didatica:
  - `input_type`: `Required strict technical selector. Type exactly one lowercase English value: audio or raw_text. In Swagger, raw_text_file is also accepted as a user-friendly alias when uploading a .txt transcript; the backend normalizes it to raw_text. Do not translate these values and do not use accents. Use audio when uploading audio_file. Use raw_text when pasting an existing transcription. Use raw_text_file when uploading the .txt field named raw_text_file. Example: audio for audio upload. Example for pasted text: raw_text. Example for .txt upload in Swagger: raw_text_file.`
  - `audio_file`: `Recorded audio file to transcribe before post-processing. Fill this only when input_type is exactly audio. Leave this empty when input_type is raw_text or when uploading raw_text_file. Supported formats are .wav and .m4a. Example: class-2026-06-09.wav.`
  - `raw_text`: `Raw transcription text to be post-processed. Fill this only when input_type is exactly raw_text and you want to paste the text directly. For long transcriptions, use raw_text_file instead. This field starts empty by default; leave it empty when uploading raw_text_file. Leave audio_file empty. Example: a rough transcript copied from a previous STT run.`
  - `raw_text_file`: `Optional .txt file containing a raw transcription to be post-processed. Use this only when input_type is exactly raw_text, or when the Swagger input_type alias is raw_text_file, and the transcript is too long to paste comfortably in raw_text. Send either raw_text or raw_text_file, not both. Leave raw_text and audio_file empty. Example: e02-transcription.txt.`
  - `course`: `Optional name of the course or broader learning context. Example: Postgraduate course at Federal University of Goias.`
  - `discipline`: `Optional name of the discipline, subject, or class area. Example: API Engineering for AI.`
  - `class_date`: `Optional date of the class. Leave this empty if there is no date. If filled, use the YYYY-MM-DD format. Example: 2026-06-09.`
  - `class_title`: `Optional title or topic of the class. Example: API First and FastAPI.`
  - `session_label`: `Optional short identifier for the recording or class session. Example: S02.`
  - `language`: `Expected language of the source content. For Brazilian Portuguese, use pt-BR. Example: pt-BR.`
  - `processing_profile`: `Post-processing profile to apply. Example: study_notes.`
- a descricao do endpoint deve explicar as cinco entregas;
- a documentacao deve explicar que `raw_text_file` permite reiniciar o pos-processamento de uma transcricao ja existente sem reprocessar o audio;
- a documentacao deve indicar que a E03 nao grava memoria, nao cria embeddings e nao executa busca.

---

## 9. Processamento Planejado

### 9.1 Fluxo com `input_type=raw_text`

1. autenticar requisicao;
2. validar `input_type`;
3. validar presenca de exatamente uma fonte textual: `raw_text` ou `raw_text_file`;
4. tratar placeholder vazio de upload como nao enviado;
5. validar ausencia de `audio_file` real;
6. validar metadados;
7. decodificar `raw_text_file` como UTF-8 quando usado;
8. validar limite `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS`;
9. enviar o texto bruto ao servico de pos-processamento;
10. montar `source.input_origin=raw_text`;
11. montar `source.raw_text_origin=provided_by_client`;
12. montar `source.transcription=null`;
13. devolver resposta E03 estruturada.

### 9.2 Fluxo com `input_type=audio`

1. autenticar requisicao;
2. validar `input_type`;
3. validar presenca de `audio_file`;
4. validar ausencia de `raw_text` e `raw_text_file`;
5. validar arquivo conforme regras basicas da E02;
6. validar metadados;
7. validar limite de upload herdado de `MINDVOX_MAX_UPLOAD_MB`;
8. chamar internamente `transcription_service`;
9. salvar automaticamente a transcricao bruta interna como artefatos locais `.json` e `.txt`;
10. obter `raw_text`, `segments`, `duration_seconds` e `transcription_engine`;
11. enviar `raw_text` ao servico de pos-processamento;
12. montar `source.input_origin=audio`;
13. montar `source.raw_text_origin=generated_by_transcription_service`;
14. montar `source.transcription` com dados controlados da STT;
15. devolver resposta E03 estruturada.

### 9.3 Regras do Servico de Pos-processamento

O servico de pos-processamento deve:

- receber `raw_text`, metadados, idioma e perfil;
- aplicar modo `contract`, `local` ou `provider`;
- produzir JSON controlado;
- validar que o resultado contem os campos obrigatorios;
- rejeitar ou tratar saida invalida de LLM sem vazar resposta integral;
- registrar `processing_engine`;
- nao registrar prompt integral ou resposta integral em logs.

---

## 10. Resposta Planejada

Resposta de sucesso:

```text
200 OK
```

Campos obrigatorios:

- `processed_transcription_id`;
- `input_type`;
- `language`;
- `raw_text`;
- `didactic_text`;
- `themes`;
- `technical_terms`;
- `technology_mentions`;
- `processing_notes`;
- `metadata`;
- `source`;
- `processing_engine`;
- `artifact_locations`.

Campo planejado para a nova camada:

- `study_package`.

O `study_package` deve existir no artefato tecnico e na pagina humana de saida. Ele pode ser incluido tambem na resposta HTTP como campo adicional nao destrutivo, desde que as cinco entregas de topo continuem presentes para compatibilidade.

Estrutura conceitual do `study_package`:

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

- `processed_transcription_id` deve ser opaco e usar prefixo controlado, como `ptr_`;
- `raw_text` deve permanecer integral, salvo erro por limite de tamanho;
- `didactic_text` deve ser texto corrido, didatico, logico, sem titulos internos e com redundancias semanticas reduzidas;
- `themes` deve conter ordem, titulo, resumo, pontos-chave, papel semantico e evidencia curta;
- `themes[].order` deve ser numero inteiro positivo;
- `themes[].title` deve ser titulo curto do nucleo tematico;
- `themes[].summary` deve ser resumo semantico do tema;
- `themes[].key_points` deve ser lista de pontos principais;
- `themes[].semantic_role` deve usar papel explicavel, como `fundamento`, `exemplo`, `risco`, `comparacao`, `pratica` ou `conclusao`;
- `themes[].evidence` deve ser trecho curto ou pista textual, nunca trecho longo do bruto;
- `technical_terms` deve conter termos normalizados ou provaveis;
- `technical_terms[].term` deve conter termo tecnico normalizado;
- `technical_terms[].normalized_from` deve listar formas brutas ou artefatos de STT quando houver;
- `technical_terms[].confidence` deve usar `low`, `medium` ou `high`;
- `technology_mentions` deve listar apenas tecnologias, ferramentas, frameworks, plataformas, bibliotecas, servicos, APIs ou providers citados ou fortemente indicados no bruto;
- `technology_mentions` nao deve inventar tecnologias relacionadas;
- `technology_mentions[].name` deve conter nome normalizado da tecnologia ou ferramenta;
- `technology_mentions[].category` deve usar categoria explicavel, como `framework`, `library`, `platform`, `service`, `provider`, `protocol`, `language`, `database`, `infrastructure`, `tool` ou `api`;
- `technology_mentions[].context` deve explicar brevemente a mencao na aula;
- `technology_mentions[].importance` deve usar `low`, `medium` ou `high`;
- `technology_mentions[].normalized_from` deve listar formas brutas ou artefatos de STT quando houver;
- `technology_mentions[].confidence` deve usar `low`, `medium` ou `high`;
- `technology_mentions[].evidence` deve ser trecho curto ou pista textual, nunca trecho longo do bruto;
- `processing_notes` deve registrar correcoes, incertezas e cuidados sem expor raciocinio interno;
- `processing_notes[].type` deve classificar a nota, como `normalization`, `uncertainty`, `safety` ou `processing`;
- `processing_notes[].message` deve ser mensagem curta, sem prompt integral ou raciocinio interno;
- `metadata` deve refletir os metadados opcionais recebidos, sem inventar campos do usuario;
- `source.input_origin` deve ser `audio` ou `raw_text`;
- `source.raw_text_origin` deve ser `generated_by_transcription_service` ou `provided_by_client`;
- `source.transcription` deve ser `null` quando `input_type=raw_text`;
- `source.transcription` deve conter `transcription_id`, `duration_seconds`, `segments_count` e `transcription_engine` quando `input_type=audio`;
- `source.transcription.transcription_engine` deve conter `name`, `model` e `version`, sem path local;
- `processing_engine.mode` deve ser `contract`, `local` ou `provider`;
- `processing_engine.name` deve identificar o processador sem segredo;
- `processing_engine.model` deve identificar o modelo/configuracao sem path local;
- `processing_engine.version` deve existir, ainda que como `unknown` ou `contract-mode`;
- `processing_engine` nao deve expor token, chave, path local, prompt ou resposta integral;
- `study_package.metadata` deve incluir metadados de curso, aula e sessao quando disponiveis;
- `study_package.operational_anchors` deve separar URLs, prazos, entregas, eventos, contatos, canais e documentos institucionais;
- `study_package.concept_candidates` deve listar conceitos candidatos sem promover automaticamente notas canonicas;
- `study_package.audit_report` deve consolidar cobertura, suspeitas, retries, chunks e quarentena;
- `study_package.memory_manifest` deve preparar ingestao futura pelo E04 em SQLite e campo vetorial;
- `study_package.export_targets` deve listar artefatos locais e Obsidian quando ativado.

---

## 11. Erros Planejados

| Situacao | Status esperado |
| --- | --- |
| Token ausente | `401 Unauthorized` |
| Token invalido | `401 Unauthorized` |
| Header `Authorization` malformado | `401 Unauthorized` |
| `input_type` ausente ou invalido | `422 Unprocessable Entity` |
| `input_type=raw_text` sem `raw_text` ou `raw_text_file` | `422 Unprocessable Entity` |
| `input_type=audio` sem `audio_file` | `422 Unprocessable Entity` |
| `audio_file` enviado junto com `raw_text` ou `raw_text_file` | `422 Unprocessable Entity` |
| `raw_text` e `raw_text_file` enviados juntos | `422 Unprocessable Entity` |
| `raw_text_file` fora de `.txt` | `400 Bad Request` |
| `raw_text_file` sem UTF-8 valido | `422 Unprocessable Entity` |
| `processing_profile` invalido | `422 Unprocessable Entity` |
| Metadados invalidos | `422 Unprocessable Entity` |
| Extensao de audio invalida | `400 Bad Request` |
| `content_type` de audio incompativel | `400 Bad Request` |
| Audio ou texto acima do limite configurado | `413 Payload Too Large` |
| Modo `provider` sem chave | `503 Service Unavailable` |
| Modo `provider` com chave vazia ou placeholder de exemplo | `503 Service Unavailable` |
| Provider externo indisponivel | `503 Service Unavailable` |
| Modo `local` sem servidor/modelo disponivel | `503 Service Unavailable` |
| STT indisponivel quando entrada for audio | `503 Service Unavailable` |
| Timeout do provider externo ou servidor local | `504 Gateway Timeout` |
| Metodo HTTP errado | `405 Method Not Allowed` |
| Erro interno inesperado | `500 Internal Server Error` |

Todos os erros devem retornar mensagem curta, sem stack trace, path local, token, chave, prompt integral, transcricao integral, texto processado integral ou resposta integral do provider.

---

## 12. Logs Planejados

Eventos permitidos:

- inicio da requisicao;
- `input_type`;
- tamanho aproximado da entrada;
- modo de processamento;
- provider/motor sem chave, sem registrar chave;
- sucesso ou falha;
- status code;
- duracao do processamento;
- contagem de caracteres;
- contagem de temas e mencoes, sem texto integral.

Dados proibidos:

- audio bruto;
- transcricao integral;
- texto processado integral;
- prompt integral;
- resposta integral de provider;
- header `Authorization`;
- token;
- chave;
- `.env`;
- paths locais sensiveis.

Decisao de persistencia:

- a E03 nao cria armazenamento proprio de logs no MVP;
- usar logger da aplicacao/servidor com mensagens sanitizadas;
- persistencia externa de logs fica fora do escopo da E03.
- quando `input_type=audio`, a transcricao bruta gerada internamente pelo STT deve salvar JSON tecnico em `outputs/transcriptions/` ou `MINDVOX_TRANSCRIPTION_OUTPUT_DIR`, e TXT humano em `outputs/human/transcriptions/` ou `MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR`;
- quando `input_type=raw_text`, a E03 nao cria artefato de STT, pois o bruto foi fornecido pelo cliente.
- artefatos brutos e processados podem usar prefixo humano sanitizado derivado de `class_date`, `class_title`, `session_label` ou metadado equivalente, e devem sempre terminar com o identificador opaco correspondente;
- toda resposta processada deve salvar `[metadados-seguros_]<processed_transcription_id>.json` no diretorio `MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR` e `[metadados-seguros_]<processed_transcription_id>.md` no diretorio `MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR`;
- o Markdown humano deve conter titulo legivel e bloco curto de metadados quando esses dados forem enviados;
- as respostas devem incluir `artifact_locations` com caminhos relativos, sem expor path absoluto local;
- em producao publica, esses artefatos locais devem ser substituidos ou complementados por endpoint/interface de download em Markdown, TXT, PDF ou outro formato de exportacao.

Verificacao obrigatoria:

- teste automatizado deve confirmar que logs da E03 nao registram bruto integral, prompt integral, resposta integral, token, chave ou path sensivel.

---

## 13. Documentacao FastAPI Planejada

A documentacao automatica deve permitir conferir:

- `summary` definido como `Post-process class transcription`;
- `description` definida com explicacao das cinco entregas;
- texto sugerido de `description`: `Receives a recorded audio file or an existing raw transcription and turns it into study-ready material. It returns five deliveries: raw_text, the auditable raw transcription; didactic_text, a logical continuous didactic text with semantic redundancies reduced; themes, the main semantic topics prepared for future memory ingestion; technical_terms, relevant technical concepts and corrections; and technology_mentions, technologies, frameworks, platforms, tools, services, libraries, APIs, or providers mentioned in class. This endpoint does not store memory, create embeddings, or perform search. When provider mode is configured, raw transcription content is sent to the configured external LLM provider; use local mode when content must remain on this machine.`;
- rota `POST /processed-transcriptions/v1.0.0`;
- entrada `multipart/form-data`;
- `input_type`;
- `audio_file`;
- `raw_text`;
- metadados opcionais;
- `processing_profile`;
- descricoes didaticas com exemplos curtos para cada campo;
- esquema de autenticacao por Bearer token;
- resposta de sucesso;
- schema de sucesso com subcampos de `themes`, `technical_terms`, `technology_mentions`, `processing_notes`, `source` e `processing_engine`;
- respostas principais de erro: `400`, `401`, `403`, `405`, `413`, `422`, `500`, `502`, `503` e `504`;
- indicacao de que a E03 recebe audio ou transcricao bruta;
- indicacao de que a E03 nao grava memoria, nao cria embeddings e nao executa busca.

---

## 14. Matriz de Testes Planejada

Os testes devem ficar em:

```text
tests/e03_processed_transcriptions/
```

Testes obrigatorios:

| Teste | Objetivo |
| --- | --- |
| `test_e03_test_plan_documents_required_contract` | Garantir que README e Spec registram matriz obrigatoria da E03 |
| `test_post_processed_transcriptions_raw_text_contract_success` | Validar sucesso com `raw_text` em modo `contract` |
| `test_post_processed_transcriptions_raw_text_file_contract_success` | Validar sucesso com `raw_text_file` `.txt` em modo `contract` |
| `test_raw_text_file_input_type_alias_is_normalized_to_raw_text` | Validar alias `input_type=raw_text_file` normalizado para `raw_text` |
| `test_raw_text_file_ignores_legacy_swagger_string_placeholder` | Validar que valor literal `string` vindo de cliente antigo/cacheado e tratado como ausente em campo opcional |
| `test_success_response_contains_five_deliveries_and_auxiliary_fields` | Validar cinco entregas e campos auxiliares |
| `test_raw_text_source_has_no_transcription_object` | Validar `source.transcription=null` com `raw_text` |
| `test_post_processed_transcriptions_audio_contract_success` | Validar sucesso com audio em modo `contract`, quando viavel |
| `test_audio_flow_saves_internal_raw_transcription_artifacts` | Validar que audio processado pela E03 salva JSON tecnico e TXT humano do bruto STT |
| `test_audio_flow_completes_generated_transcription_queue_job` | Validar que audio processado pela E03 cria job, conclui a fila, salva `.json` tecnico, `.md` humano e expõe `artifact_locations` |
| `test_processed_markdown_artifact_uses_class_metadata_title` | Validar que metadados de aula aparecem no nome seguro do arquivo e no titulo do Markdown humano |
| `test_artifact_stem_uses_safe_class_metadata_prefix` | Validar servico compartilhado de nomeacao segura de artefatos com metadados e identificador opaco |
| `test_audio_flow_keeps_queue_job_pending_when_postprocessing_fails` | Validar que falha do motor depois da STT deixa job pendente para retry |
| `test_pending_generated_transcription_job_can_be_retried_without_reupload` | Validar que job pendente e reprocessado sem reenviar audio |
| `test_contract_mode_does_not_invent_technology_mentions` | Validar que modo `contract` nao inventa tecnologia ausente do bruto |
| `test_missing_token_returns_401` | Validar token ausente |
| `test_invalid_token_returns_401` | Validar token invalido |
| `test_malformed_authorization_header_returns_401` | Validar header `Authorization` fora do formato `Bearer <token>` |
| `test_local_development_without_api_token_uses_dev_token` | Validar token local automatico em desenvolvimento |
| `test_dev_token_configuration_returns_503_in_public_deployment` | Validar que `dev-token` e recusado em deploy publico |
| `test_public_deployment_without_api_token_has_no_default_token` | Validar que producao publica nao cria token padrao |
| `test_contract_profile_forces_contract_modes_and_disables_llama_autostart` | Validar perfil CLI `contract` |
| `test_prod_profile_enables_public_hardening_without_dev_token_default` | Validar perfil CLI `prod` |
| `test_public_deployment_requires_https_for_processed_transcriptions` | Validar `403` para E03 quando a aplicacao nao recebe scheme `https` em deploy publico |
| `test_public_deployment_accepts_https_for_processed_transcriptions` | Validar aceite de scheme `https` em deploy publico |
| `test_missing_main_input_returns_422` | Validar entrada principal ausente |
| `test_invalid_input_type_returns_422` | Validar `input_type` invalido |
| `test_audio_input_without_audio_file_returns_422` | Validar fluxo de audio sem arquivo |
| `test_audio_and_raw_text_conflict_returns_422` | Validar conflito entre audio e texto |
| `test_raw_text_flow_ignores_empty_audio_file_placeholder` | Validar que placeholder vazio de upload nao bloqueia fluxo por texto |
| `test_raw_text_and_raw_text_file_conflict_returns_422` | Validar conflito entre texto colado e arquivo `.txt` |
| `test_audio_and_raw_text_file_conflict_returns_422` | Validar conflito entre audio e arquivo `.txt` |
| `test_invalid_raw_text_file_extension_returns_400` | Validar extensao invalida de arquivo de texto |
| `test_invalid_processing_profile_returns_422` | Validar perfil invalido |
| `test_invalid_audio_extension_returns_400` | Validar extensao invalida |
| `test_incompatible_audio_content_type_returns_400` | Validar content type de audio incompativel |
| `test_invalid_metadata_returns_422` | Validar metadados invalidos |
| `test_oversized_optional_metadata_returns_422` | Validar limites de `course`, `discipline` e `class_title` |
| `test_raw_text_over_limit_returns_413` | Validar limite de `150000` caracteres |
| `test_audio_over_upload_limit_returns_413` | Validar limite de upload de audio herdado de `MINDVOX_MAX_UPLOAD_MB` |
| `test_limited_upload_reader_rejects_before_reading_full_oversized_upload` | Validar leitura incremental e interrupcao antes de consumir upload inteiro acima do limite |
| `test_unavailable_processing_engine_returns_503` | Validar motor indisponivel |
| `test_placeholder_provider_key_returns_503` | Validar que chave vazia ou placeholder de provider retorna `503` e nao e tratada como chave real |
| `test_empty_provider_key_returns_503` | Validar chave vazia de provider |
| `test_placeholder_api_token_configuration_returns_503` | Validar que placeholder de `MINDVOX_API_TOKEN` e tratado como token ausente |
| `test_provider_mode_rejects_localhost_endpoint` | Validar rejeicao de endpoint local em modo `provider` |
| `test_provider_mode_rejects_hostname_resolving_to_private_address` | Validar rejeicao de hostname provider que resolve para IP local/privado |
| `test_provider_mode_rejects_hostname_outside_allowed_list` | Validar rejeicao de host fora da allowlist de provider |
| `test_provider_mode_accepts_hostname_inside_allowed_list` | Validar aceitacao de host dentro da allowlist de provider |
| `test_local_mode_rejects_public_endpoint` | Validar rejeicao de endpoint publico em modo `local` |
| `test_local_unavailable_processing_engine_returns_503` | Validar indisponibilidade do servidor local |
| `test_contract_mode_does_not_start_llama_server` | Validar que modo `contract` nao aciona autostart do Llama |
| `test_local_autostart_disabled_does_not_start_llama_server` | Validar que autostart desligado nao inicia `llama-server` |
| `test_existing_openai_compatible_server_is_reused` | Validar que servidor local ja ativo e reaproveitado |
| `test_local_autostart_starts_llama_server_until_ready` | Validar que autostart inicia `llama-server` e aguarda prontidao |
| `test_missing_llama_server_path_fails_with_clear_message` | Validar que falta de binario gera erro claro |
| `test_missing_model_path_fails_with_clear_message` | Validar que falta de modelo GGUF gera erro claro |
| `test_startup_timeout_terminates_started_process` | Validar que timeout de startup encerra processo iniciado |
| `test_invalid_llm_output_returns_500` | Validar saida invalida de LLM sem vazamento de resposta integral |
| `test_long_llm_output_with_insufficient_semantic_coverage_returns_502_with_rejected_artifact` | Validar que bruto longo nao aceita resumo excessivo como sucesso, retorna `502` e salva artefato rejeitado |
| `test_long_llm_output_retry_can_recover_semantic_coverage` | Validar retry automatico quando a primeira saida tem cobertura semantica insuficiente |
| `test_long_llm_output_missing_semantic_anchors_returns_502` | Validar que saida editorial longa, mas sem projetos/cases/dor/autoria, e rejeitada com diagnostico estruturado |
| `test_audio_flow_moves_quality_failure_to_failed_after_max_attempts` | Validar que falha de qualidade em job de audio vai para `queue/failed/` apos limite de tentativas |
| `test_llm_prompt_lists_protected_semantic_anchors_for_long_transcript` | Validar que o prompt lista ancoras semanticas protegidas extraidas do bruto |
| `test_chunk_llm_prompt_does_not_apply_full_transcript_semantic_gate` | Validar que prompt de chunk nao aplica a regua monolitica completa antes do merge |
| `test_semantic_anchors_do_not_treat_generic_positive_as_company` | Validar que uso comum de "positivo" nao aciona a ancora da empresa Positivo |
| `test_semantic_anchors_detect_possibly_named_positivo_company` | Validar que contexto nominal minimo continua acionando a ancora da empresa Positivo |
| `test_semantic_anchors_do_not_treat_generic_score_as_viability_case` | Validar que "score" isolado nao aciona o case de score de viabilidade |
| `test_semantic_anchors_ignore_capitalized_discourse_words` | Validar que palavras comuns capitalizadas nao viram nomes proprios protegidos |
| `test_pre_audit_removes_repetitive_transcription_noise_only_from_llm_text` | Validar saneamento interno de ruido repetitivo de STT sem alterar o bruto publico |
| `test_semantic_coverage_matches_microsservicos_accented_spelling` | Validar que `microsserviços` acentuado satisfaz a ancora `microservicos` |
| `test_processing_engine_timeout_returns_504` | Validar timeout |
| `test_get_processed_transcriptions_returns_405` | Validar metodo HTTP invalido |
| `test_public_deployment_requires_trusted_hosts` | Validar que deploy publico exige `MINDVOX_TRUSTED_HOSTS` |
| `test_public_deployment_disables_docs_and_enforces_trusted_hosts` | Validar docs desabilitados por padrao e Host header protegido |
| `test_public_deployment_rejects_wildcard_trusted_hosts` | Validar rejeicao de `MINDVOX_TRUSTED_HOSTS=*` em deploy publico |
| `test_openapi_documents_e03_contract` | Validar OpenAPI, incluindo `Active startup profile` |
| `test_response_and_errors_do_not_expose_sensitive_values` | Validar nao vazamento em respostas e erros |
| `test_e03_logs_are_sanitized` | Validar logs sanitizados |
| `test_processed_transcription_auth_failure_logs_status_error_and_duration` | Validar log de autenticacao com status, codigo, fase e duracao sem credenciais |
| `test_controlled_validation_errors_are_logged_without_sensitive_values` | Validar logs de erro controlado sem dados sensiveis |
| `test_processing_engine_redacts_sensitive_provider_name` | Validar redacao de provider com marcador sensivel |
| `test_llm_client_sends_max_tokens_and_limits_response_size` | Validar envio de `max_tokens` e limite de leitura do cliente LLM |
| `test_llm_prompt_uses_e03_manual_without_concise_instruction` | Validar que o prompt usa manual operacional da E03, exige preservacao semantica e nao reintroduz concisao/resumo |
| `test_llm_client_disables_thinking_for_local_llama_server` | Validar que modo `local` desliga thinking no `llama-server` |
| `test_llm_client_does_not_send_local_template_kwargs_to_provider` | Validar que provider externo nao recebe parametro especifico local |
| `test_llm_client_rejects_excessive_response_body` | Validar rejeicao de resposta LLM excessiva |
| `test_benchmark_script_rejects_excessive_response_body` | Validar limite de leitura no script interno de benchmark |
| `test_zero_llm_max_output_tokens_falls_back_to_default` | Validar fallback seguro para limite invalido de tokens |
| `test_zero_llama_server_parallel_falls_back_to_default` | Validar fallback seguro para slots invalidos do `llama-server` |

Regra:

- testes automatizados devem manter STT e E03 em contrato, preferencialmente com `MINDVOX_TRANSCRIPTION_MODE=contract` e `MINDVOX_POSTPROCESSING_MODE=auto`;
- testes reais com `local` ou `provider` nao substituem testes automatizados;
- prova humana real e obrigatoria antes do commit de fechamento.

---

## 15. Passos de Implementacao

1. Corrigir qualquer incoerencia remanescente entre Spec E03, P03 e README da pasta de testes.
2. Atualizar `.env.example` com variaveis da E03 e valores ficticios.
3. Garantir que `.env`, `.benchmarks/`, caches e artefatos locais continuam ignorados.
4. Criar schemas Pydantic da E03.
5. Criar `ProcessedTranscriptionResponse`.
6. Criar modelos internos para `Theme`, `TechnicalTerm`, `TechnologyMention`, `ProcessingNote`, `Source` e `ProcessingEngine`.
7. Criar camada `postprocessing_service`.
8. Criar cliente OpenAI-compatible isolado.
9. Criar modo `contract`.
10. Criar modo `provider`.
11. Criar modo `local`.
12. Implementar validacao de modo e variaveis obrigatorias.
12.1. Tratar `MINDVOX_LLM_API_KEY` vazia ou com placeholder de exemplo como chave ausente em modo `provider`.
12.2. Usar `dev-token` quando `MINDVOX_API_TOKEN` estiver ausente ou vazio em desenvolvimento local.
12.2.1. Tratar placeholder de exemplo de `MINDVOX_API_TOKEN` como token ausente.
12.3. Implementar hardening configuravel por `MINDVOX_PUBLIC_DEPLOYMENT`, `MINDVOX_ENABLE_DOCS` e `MINDVOX_TRUSTED_HOSTS`.
12.4. Implementar allowlist de provider por `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS`.
12.5. Bloquear `dev-token`, `MINDVOX_TRUSTED_HOSTS=*` e transporte inseguro quando `MINDVOX_PUBLIC_DEPLOYMENT=true`.
13. Implementar timeout controlado do motor textual.
14. Implementar parsing/validacao da saida estruturada do motor textual.
15. Implementar erro controlado para saida invalida do motor textual.
16. Criar router `src/routers/processed_transcriptions.py`.
17. Registrar router em `src/main.py`.
18. Implementar autenticacao por Bearer token.
19. Implementar validacao de `input_type` por `Enum` no OpenAPI/Swagger.
20. Implementar validacao de `raw_text`.
20.1. Implementar upload opcional de `raw_text_file` em `.txt` para reprocessar transcricao ja existente.
20.2. Tratar placeholder vazio de upload opcional como nao enviado.
21. Implementar limite `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS=150000`.
22. Implementar validacao de `audio_file`.
23. Implementar proibicao de `audio_file` com `raw_text` ou `raw_text_file`, e de `raw_text` com `raw_text_file`.
24. Implementar validacao de metadados.
24.1. Implementar limite de `course` ate `160`, `discipline` ate `120` e `class_title` ate `200` caracteres.
25. Implementar validacao de `processing_profile`.
26. Implementar fluxo `input_type=raw_text`.
27. Implementar fluxo `input_type=audio` reutilizando `transcription_service`.
28. Garantir que E03 nao chama E02 por HTTP.
29. Montar `source` corretamente para `raw_text`.
30. Montar `source` corretamente para `audio`.
31. Montar `processing_engine` sem path local ou segredo.
32. Montar resposta com cinco entregas publicas.
32.1. Implementar nome humano seguro para artefatos locais da E03 com sufixo `processed_transcription_id` opaco.
32.2. Implementar titulo e bloco curto de metadados no Markdown humano da E03.
32.3. Criar schema interno de `StudyPackage`.
32.4. Montar `StudyPackage` a partir das cinco entregas, metadados, fonte, auditoria e destinos.
32.5. Persistir `StudyPackage` em `MINDVOX_E03_STUDY_PACKAGE_OUTPUT_DIR`.
32.6. Criar `memory_manifest` apontando dados relacionais para SQLite e textos candidatos para campo vetorial futuro.
32.7. Criar extracao inicial de `operational_anchors` a partir dos artefatos ja produzidos pela E03, sem inventar factualidade.
32.8. Criar `concept_candidates` a partir de temas e termos tecnicos, sem promover conceitos incertos.
33. Implementar tratamento de `400`, `401`, `403`, `405`, `413`, `422`, `500`, `502`, `503` e `504`.
34. Implementar logs sanitizados.
35. Garantir que router nao contem logica completa de STT ou LLM.
35.1. Criar armazenamento local de curso ativo e cursos cadastrados.
35.2. Criar pagina humana de entrada da E03 com textarea para `raw_text`.
35.3. Criar seletor/lista flutuante de cursos cadastrados.
35.4. Adaptar script de preparo a partir do Vault para preencher a pagina humana de modo visivel ou gerar entrada equivalente.
35.5. Criar pagina humana de saida para renderizar `StudyPackage`.
35.6. Abrir ou exibir automaticamente o resultado ao fim do processamento iniciado pela pagina humana.
35.7. Criar script/servico de criacao deterministica de Student Vault novo.
35.8. Criar exportador opcional de `StudyPackage` para Student Vault criado.
36. Criar testes de sucesso com `raw_text`.
37. Criar testes de schema de sucesso.
38. Criar testes de `source` para `raw_text`.
39. Criar testes de sucesso com audio em modo `contract`, se viavel.
40. Criar testes de autenticacao.
41. Criar teste de header `Authorization` malformado.
42. Criar testes de entrada invalida.
43. Criar testes de conflito entre audio e texto.
44. Criar testes de perfil invalido.
45. Criar testes de extensao invalida.
46. Criar teste de limite `413`.
47. Criar teste de upload de audio acima de `MINDVOX_MAX_UPLOAD_MB` retornando `413`.
48. Criar teste de motor indisponivel `503`.
49. Criar teste de chave vazia ou placeholder de provider retornando `503`.
49.1. Criar teste de placeholder de `MINDVOX_API_TOKEN` retornando `503`.
49.2. Criar testes de allowlist de provider.
49.3. Criar testes de endurecimento de deploy publico.
50. Criar teste de timeout `504`.
51. Criar teste de metodo invalido `405`.
52. Criar teste de OpenAPI.
53. Criar teste de nao vazamento em respostas e erros.
54. Criar teste de logs sanitizados.
55. Atualizar README da pasta de testes, se necessario.
56. Rodar verificacao de sintaxe.
57. Rodar testes da E03.
58. Rodar suite geral.
59. Rodar aplicacao local em modo `contract`.
60. Conferir `/docs`.
61. Conferir `/openapi.json`.
62. Executar teste manual valido com `raw_text` em modo `contract`.
63. Executar teste manual valido com `audio_file` em modo `contract`, quando viavel.
64. Executar teste manual invalido sem token.
65. Executar teste manual invalido com entrada conflitante.
66. Executar teste manual real com modo `local` preferencial ou `provider` quando local nao for viavel.
67. Registrar prova humana real.
68. Atualizar checklist da E03.
69. Atualizar T03.
70. Atualizar README do projeto, se a implementacao alterar instrucao de uso.
71. Atualizar material didatico externo ao repo, quando aplicavel.
72. Revisar `git status`.
73. Revisar `git diff`.
74. Confirmar que arquivos alterados pertencem ao escopo da E03 ou estao justificados.
75. Confirmar ausencia de segredo, token real, `.env`, path sensivel ou dado privado no diff.
76. Confirmar ausencia de cache, `__pycache__`, temporario ou artefato gerado indevido no diff.
77. Confirmar que a mensagem de commit identifica a E03.
78. Preparar commit de fechamento.
79. Realizar commit de fechamento antes de iniciar E04.
80. Atualizar README do projeto com fluxo sem Obsidian, fluxo com Obsidian opcional e papel do `StudyPackage`.

---

## 16. Verificacoes

Verificacao de sintaxe:

```bash
uv run python -m py_compile src/main.py src/settings.py src/routers/processed_transcriptions.py src/schemas/processed_transcriptions.py src/services/transcription_service.py src/services/postprocessing_service.py src/services/llm_client.py src/services/local_llm_runtime.py src/services/processed_transcription_artifacts.py src/services/processed_transcription_queue.py tests/e03_processed_transcriptions/test_e03_test_plan.py tests/e03_processed_transcriptions/test_processed_transcriptions.py tests/e03_processed_transcriptions/test_local_llm_runtime.py
```

Testes automatizados da E03:

```bash
uv run python -m unittest discover -s tests/e03_processed_transcriptions -v
```

Testes automatizados gerais:

```bash
uv run python -m unittest discover -s tests -v
```

Servidor local em modo de contrato:

```bash
uv run fastapi dev src/contract
```

Aplicacao em modo `local` com autostart do `llama-server`:

```bash
uv run fastapi dev src/main.py
```

Aplicacao em modo `provider`, com Groq configurado por `.env` local:

```bash
MINDVOX_POSTPROCESSING_MODE=provider \
MINDVOX_LLM_PROVIDER=groq \
MINDVOX_LLM_BASE_URL=https://api.groq.com/openai/v1 \
MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS=api.groq.com \
MINDVOX_LLM_MODEL=llama-3.3-70b-versatile \
uv run fastapi dev src/main.py
```

Atalhos dentro da pasta `src`:

```bash
fastapi dev
fastapi dev contract
fastapi run prod
```

No Swagger local, o Bearer token didatico permanece sendo `dev-token`.

Documentacao:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

---

## 17. Demonstracao Manual Prevista

Chamada valida com texto bruto em modo de contrato:

```bash
curl -X POST "http://127.0.0.1:8000/processed-transcriptions/v1.0.0" \
  -H "Authorization: Bearer dev-token" \
  -F "input_type=raw_text" \
  -F "raw_text=Texto bruto de aula para pos-processamento." \
  -F "discipline=API" \
  -F "session_label=S03" \
  -F "language=pt-BR" \
  -F "processing_profile=study_notes"
```

Resultado esperado:

```text
200 OK
```

Chamada valida com audio em modo de contrato:

```bash
curl -X POST "http://127.0.0.1:8000/processed-transcriptions/v1.0.0" \
  -H "Authorization: Bearer dev-token" \
  -F "input_type=audio" \
  -F "audio_file=@/caminho/para/audio.wav;type=audio/wav" \
  -F "discipline=API" \
  -F "session_label=S03" \
  -F "language=pt-BR" \
  -F "processing_profile=study_notes"
```

Resultado esperado:

```text
200 OK
```

Chamada invalida sem token:

```bash
curl -X POST "http://127.0.0.1:8000/processed-transcriptions/v1.0.0" \
  -F "input_type=raw_text" \
  -F "raw_text=Texto bruto"
```

Resultado esperado:

```text
401 Unauthorized
```

Chamada invalida com entrada conflitante:

```bash
curl -X POST "http://127.0.0.1:8000/processed-transcriptions/v1.0.0" \
  -H "Authorization: Bearer dev-token" \
  -F "input_type=audio" \
  -F "audio_file=@/caminho/para/audio.wav;type=audio/wav" \
  -F "raw_text=texto bruto indevido"
```

Resultado esperado:

```text
422 Unprocessable Entity
```

Prova real humana antes do commit:

- executar a E03 com entrada real representativa;
- usar preferencialmente modo `local` com `Qwen3.6-35B-A3B-MTP-Q8.gguf`;
- se o modo local nao for viavel, usar modo `provider` com provider OpenAI-compatible configurado;
- registrar modo, modelo/provider, status HTTP, tempo aproximado e avaliacao humana da coerencia de `raw_text`, `didactic_text`, `themes`, `technical_terms` e `technology_mentions`;
- se o modo usado for `provider`, registrar explicitamente que o conteudo bruto foi enviado ao provider externo configurado.

---

## 18. Fora do Escopo Deste Plano

Este plano nao implementa:

- memoria persistida;
- banco relacional definitivo;
- banco vetorial;
- embeddings;
- busca semantica;
- busca relacional;
- recuperacao de informacao;
- chunks vetoriais;
- ingestao em memoria;
- frontend completo multiusuario, area administrativa geral ou sistema de contas;
- TTS;
- streaming;
- diarizacao final;
- revisao humana definitiva;
- `corrected_full_text` quase integral como saida padrao;
- glossario adicional;
- roteiro de revisao;
- processamento de textos acima do limite duro `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS`;
- fila distribuida externa, com broker, workers separados ou garantias avancadas de entrega;
- deploy em cloud.
- selecao, importacao, validacao ou correcao de Vault Obsidian existente.
- ingestao real do `memory_manifest` no E04.

Esses itens pertencem a Specs futuras, especialmente E04 e E05, ou a emenda propria.

---

## 19. Riscos e Cuidados

Riscos principais:

- ampliar E03 para memoria, banco ou busca;
- chamar E02 por HTTP dentro do app;
- confundir modo `contract` com pos-processamento real;
- vazar transcricao bruta, texto processado, prompt, resposta do provider, token, chave ou path local;
- deixar path local de modelo hard-coded;
- aceitar tecnologias inventadas em `technology_mentions`;
- duplicar a transcricao bruta em um `corrected_full_text` quase integral;
- implementar logica de LLM diretamente no router;
- criar dependencia obrigatoria de provider externo;
- usar provider externo sem deixar claro que o conteudo bruto e enviado a terceiro configurado;
- commitar `.env`, `.benchmarks/`, cache, audio real ou transcricao real.

Cuidados obrigatorios:

- manter `raw_text` como lastro de auditoria;
- manter `didactic_text` como texto didatico pos-processado, com redundancia semantica reduzida e sem perda deliberada de conteudo;
- manter `themes` pronto para futura E04 sem gravar memoria agora;
- produzir `memory_manifest` para futura E04 sem executar ingestao na E03;
- manter SQLite como destino relacional futuro escolhido, sem tratar Obsidian como banco relacional principal;
- manter Obsidian como exportacao opcional e redundancia positiva;
- manter `technical_terms` separado de `technology_mentions`;
- usar exemplos ficticios;
- usar variaveis de ambiente para configuracao;
- preferir modo `local` quando o conteudo nao puder sair da maquina;
- sanitizar logs e erros;
- garantir testes perenes antes de iniciar E04.

---

## 20. Criterios de Pronto

Este plano podera ser fechado quando:

- o endpoint `POST /processed-transcriptions/v1.0.0` existir;
- o endpoint exigir Bearer token;
- o endpoint rejeitar token ausente, invalido e header malformado;
- o endpoint aceitar `input_type=raw_text` em modo `contract`;
- o endpoint aceitar `raw_text_file` `.txt` como alternativa a `raw_text` para reprocessar transcricao existente;
- o endpoint aceitar `input_type=audio` em modo `contract`, quando viavel;
- o endpoint rejeitar entrada principal ausente;
- o endpoint rejeitar `audio_file` com `raw_text` ou `raw_text_file`;
- o endpoint rejeitar `raw_text` e `raw_text_file` juntos;
- o endpoint rejeitar `processing_profile` invalido;
- o endpoint rejeitar `course`, `discipline` ou `class_title` acima dos limites definidos;
- o endpoint rejeitar extensao de audio invalida;
- o endpoint rejeitar `raw_text` acima de `150000` caracteres com `413 Payload Too Large`;
- o endpoint rejeitar upload de audio acima de `MINDVOX_MAX_UPLOAD_MB` com `413 Payload Too Large`;
- o endpoint retornar `503 Service Unavailable` quando motor necessario estiver indisponivel;
- o endpoint retornar `503 Service Unavailable` quando `MINDVOX_LLM_API_KEY` estiver vazia ou contiver placeholder de exemplo em modo `provider`;
- o endpoint usar `dev-token` quando `MINDVOX_API_TOKEN` estiver ausente ou vazio em desenvolvimento local;
- o endpoint retornar `503 Service Unavailable` quando `MINDVOX_API_TOKEN` estiver com placeholder de exemplo;
- o modo `provider` respeitar allowlist de host quando configurada;
- `dev-token` ser recusado em deploy publico;
- o modo publico exigir `MINDVOX_TRUSTED_HOSTS`, rejeitar `MINDVOX_TRUSTED_HOSTS=*`, desabilitar docs por padrao e rejeitar Host header fora da lista;
- `POST /processed-transcriptions/v1.0.0` exigir transporte seguro em deploy publico, retornando `403` quando a aplicacao nao receber scheme `https`;
- o endpoint retornar `504 Gateway Timeout` quando motor textual exceder timeout;
- o endpoint retornar `405 Method Not Allowed` para metodo errado;
- o endpoint tratar erro interno inesperado como `500`, sem vazamento sensivel;
- a resposta de sucesso contiver `raw_text`, `didactic_text`, `themes`, `technical_terms`, `technology_mentions`, `processing_notes`, `metadata`, `source` e `processing_engine`;
- o artefato tecnico ou a resposta conter `study_package` com metadados, fonte, bruto, texto didatico, temas, termos, tecnologias, ancoras operacionais, conceitos candidatos, auditoria, `memory_manifest` e destinos;
- a pagina humana de entrada existir e aceitar texto colado em textarea ampla;
- a pagina humana de entrada permitir curso ativo persistente e escolha de cursos cadastrados;
- a pagina humana de saida renderizar o `StudyPackage` em secoes claras;
- o script local de Vault conseguir preparar transcrito e metadados para a pagina humana sem exigir preenchimento manual repetitivo;
- o script de criacao de Student Vault novo criar estrutura deterministica quando Obsidian opcional estiver ativado;
- o exportador Obsidian projetar `StudyPackage` para Vault criado, sem importar Vault existente;
- `source.transcription` for `null` quando `input_type=raw_text`;
- `source.transcription` contiver dados controlados de STT quando `input_type=audio`;
- `processing_engine` identificar modo/modelo sem path local ou segredo;
- OpenAPI documentar rota, formulario, Bearer token, descricoes didaticas, cinco entregas e respostas `400`, `401`, `403`, `405`, `413`, `422`, `500`, `502`, `503` e `504`;
- OpenAPI explicar que modo `provider` envia o conteudo bruto ao provider externo configurado;
- logs tiverem sido verificados contra vazamento de audio bruto, transcricao integral, texto processado integral, prompt integral, resposta integral, token, chave, `.env` e path sensivel;
- houver testes automatizados da E03;
- houver README atualizado na pasta de testes da E03;
- a suite da E03 passar;
- a suite geral passar;
- a prova real humana da E03 passar e ficar registrada;
- checklist da Spec E03 estiver coerente;
- T03 estiver atualizada;
- material didatico externo ao repo estiver atualizado, quando aplicavel;
- `git status` e `git diff` tiverem sido revisados;
- os arquivos alterados pertencerem ao escopo da E03 ou estiverem justificados;
- nenhum segredo, token real, `.env`, path sensivel, cache, `__pycache__`, temporario ou artefato gerado indevido aparecer no diff;
- a mensagem de commit identificar a E03;
- o commit de fechamento tiver sido realizado antes de iniciar E04;
- Adalberto conseguir explicar finalidade, entrada, autenticacao, validacao, processamento, saida, erros, logs, testes, motor e limites da E03.

---

## 21. Registro de Estado

Status atual: `implementado_em_validacao_real`.

Motivo do estado:

- Spec E03 esta suficientemente detalhada para orientar plano e tarefas;
- E02 ja fornece a transcricao bruta que a E03 deve processar;
- benchmark real definiu `Qwen3.6-35B-A3B-MTP-Q8.gguf` como modelo local preferencial;
- provider OpenAI-compatible foi previsto para portabilidade;
- a matriz de testes da E03 foi criada;
- a pasta de testes da E03 existe com README atualizado;
- o endpoint E03 foi implementado;
- o pipeline longo opcional foi integrado ao runtime;
- os testes automatizados da E03 passaram;
- a suite geral passou.

Pendencia para fechamento canonico:

- executar e registrar prova real humana do endpoint em modo `local` ou `provider`;
- revisar Git imediatamente antes do commit;
- realizar commit de fechamento da E03.
