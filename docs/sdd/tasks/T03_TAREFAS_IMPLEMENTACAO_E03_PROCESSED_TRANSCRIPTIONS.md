# Tarefas T03: Implementacao do Endpoint E03 Processed Transcriptions

## 1. Identificacao

- `ID`: `T03`
- `Tipo`: `Tarefas de Implementacao`
- `Status`: `implementada_em_validacao_real`
- `Spec alvo`: `E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`
- `Plano alvo`: `P03_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`
- `Endpoint alvo`: `POST /processed-transcriptions/v1.0.0`
- `Data`: `2026-06-10`

---

## 2. Objetivo

Executar a implementacao do endpoint E03 Processed Transcriptions conforme a Spec E03 e o Plano P03.

O endpoint deve receber audio gravado ou transcricao bruta, autenticar a requisicao, validar entrada e metadados, obter ou preservar `raw_text`, executar pos-processamento por motor substituivel e devolver material de estudo estruturado.

Na emenda atual, a E03 passa tambem a planejar uma camada humana de entrada e saida: pagina de entrada melhor que Swagger, curso ativo persistente, `Study Package`, pagina humana de resultado, `memory_manifest` para E04 futura e exportacao opcional para Student Vault criado deterministicamente.

Entregas publicas obrigatorias:

- `raw_text`;
- `didactic_text`;
- `themes`;
- `technical_terms`;
- `technology_mentions`.

Campo auxiliar obrigatorio:

- `processing_notes`.

---

## 3. Regra de Execucao

Estas tarefas devem ser usadas como lista de conferencia durante a implementacao e antes do commit de fechamento da E03.

Interpretacao:

- enquanto a implementacao nao for feita, as tarefas permanecem `pendente`;
- apos comparar Spec, Plano, tarefas, implementacao e testes, cada item pode ser marcado como `concluida`, `ajustar` ou `N/A`;
- divergencias justificadas devem ser registradas nesta nota, no plano ou na Spec antes do commit;
- nenhuma tarefa de E04 deve iniciar antes do fechamento funcional e documental da E03;
- modo `contract` e necessario para testes automatizados, mas nao substitui prova real humana;
- a E03 so pode ser fechada depois de prova real humana, com entrada representativa, demonstrando que o endpoint faz corretamente aquilo que seu contrato declara.

### 3.1 Regra de Prova Real Para Specs Tipo E

Toda Spec tipo `E` do Mindvox deve exigir prova real humana antes de ser considerada fechada.

Para fins desta T03, `prova real humana` significa:

- execucao manual do endpoint por uma pessoa;
- uso de entrada real ou representativa do dominio do endpoint;
- verificacao de que a resposta corresponde ao comportamento prometido no contrato;
- verificacao de erros relevantes quando aplicavel;
- registro do modo usado (`local` ou `provider`), modelo/provider, status HTTP, tempo aproximado e avaliacao humana das cinco entregas;
- registro explicito de que o conteudo bruto foi enviado ao provider externo configurado, se modo `provider` for usado.

Consequencia obrigatoria:

- enquanto a E03 nao provar na vida real que faz sem erros aquilo que seu contrato diz que faz, ela nao esta concluida;
- enquanto a E03 nao estiver concluida, nao pode haver mudanca de desenvolvimento para E04;
- testes automatizados continuam obrigatorios, mas nao substituem a prova real humana.

---

## 4. Tarefas

| ID | Status | Tarefa | Criterio de conclusao |
| --- | --- | --- | --- |
| T03.01 | concluida | Conferir coerencia entre E03, P03, README e README de testes | Nenhuma divergencia remanescente bloqueia a implementacao |
| T03.02 | concluida | Confirmar arquivos planejados da E03 | Arquivos de codigo, teste, documentacao e configuracao pertencem ao escopo previsto em P03 |
| T03.03 | concluida | Corrigir regra documental de placeholder para chave LLM | `.env.example`, E03, P03, README e README de testes tratam chave vazia ou placeholder como ausente |
| T03.04 | concluida | Garantir `.gitignore` adequado | `.env`, `.benchmarks/`, caches, audios reais, transcricoes reais e saidas de benchmark ficam fora do Git |
| T03.05 | concluida | Confirmar `.env.example` sem segredo real | Variaveis da E03 estao documentadas com valores ficticios ou vazios |
| T03.06 | concluida | Definir `MINDVOX_POSTPROCESSING_MODE` em configuracao externa | Modos `auto`, `contract`, `local` e `provider` sao lidos de configuracao |
| T03.06.1 | concluida | Atrelar modo padrao da E03 ao modo de STT | `auto` deriva `contract` quando `MINDVOX_TRANSCRIPTION_MODE=contract` e deriva `local` quando `MINDVOX_TRANSCRIPTION_MODE=real` |
| T03.07 | concluida | Definir `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS` | Limite configuravel e recalibrado para `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS=150000`, cobrindo aula de ate aproximadamente duas horas com margem pragmatica |
| T03.08 | concluida | Definir variaveis LLM da E03 | `MINDVOX_LLM_PROVIDER`, `MINDVOX_LLM_BASE_URL`, `MINDVOX_LLM_MODEL`, `MINDVOX_LLM_API_KEY`, `MINDVOX_LLM_MAX_OUTPUT_TOKENS` e `MINDVOX_LLM_TIMEOUT_SECONDS` sao lidos de configuracao |
| T03.08.1 | concluida | Ajustar limites locais reais da E03 | Defaults locais usam `MINDVOX_LLM_MAX_OUTPUT_TOKENS=20000`, `MINDVOX_LLM_TIMEOUT_SECONDS=1200`, `MINDVOX_LLAMA_SERVER_CTX_SIZE=65536` e `MINDVOX_LLAMA_SERVER_PARALLEL=1` |
| T03.08.2 | concluida | Criar manual operacional do prompt E03 | Prompt LLM le `src/services/prompts/e03_postprocessing_manual.md` e exige preservacao semantica, sem orientar resumo barato |
| T03.09 | concluida | Tratar placeholder de `MINDVOX_LLM_API_KEY` como ausente | Valor vazio, `replace-with-provider-key` ou `<set-real-key-only-in-local-env>` gera erro controlado em modo `provider` |
| T03.09.1 | concluida | Tratar placeholder de `MINDVOX_API_TOKEN` como ausente | `replace-with-local-token` ou `<set-real-token-only-in-local-env>` nao autentica E02/E03 e gera erro controlado |
| T03.09.2 | concluida | Definir hardening de deploy publico | `MINDVOX_PUBLIC_DEPLOYMENT`, `MINDVOX_ENABLE_DOCS` e `MINDVOX_TRUSTED_HOSTS` controlam docs e Host header |
| T03.09.3 | concluida | Rejeitar `dev-token` em deploy publico | Quando `MINDVOX_PUBLIC_DEPLOYMENT=true`, token didatico e tratado como ausente e nao autentica E02/E03 |
| T03.09.4 | concluida | Rejeitar wildcard de trusted hosts em deploy publico | `MINDVOX_TRUSTED_HOSTS=*` impede inicializacao quando `MINDVOX_PUBLIC_DEPLOYMENT=true` |
| T03.09.5 | concluida | Exigir transporte seguro em deploy publico | `POST /transcriptions/v1.0.0` e `POST /processed-transcriptions/v1.0.0` retornam `403 Forbidden` quando a aplicacao nao recebe scheme `https` em modo publico |
| T03.09.6 | concluida | Definir token local automatico | Em `MINDVOX_PUBLIC_DEPLOYMENT=false`, `MINDVOX_API_TOKEN` ausente ou vazio usa `dev-token` para simplificar o uso local |
| T03.10 | concluida | Criar schemas Pydantic da E03 | Schemas existem em `src/schemas/processed_transcriptions.py` ou local equivalente |
| T03.11 | concluida | Criar `ProcessedTranscriptionResponse` | Resposta possui todos os campos obrigatorios da E03 |
| T03.12 | concluida | Criar schema de `Theme` | `themes` contem ordem, titulo, resumo, pontos-chave, papel semantico e evidencia curta |
| T03.13 | concluida | Criar schema de `TechnicalTerm` | `technical_terms` contem termo, normalizacao, explicacao curta, confianca e evidencia quando aplicavel |
| T03.14 | concluida | Criar schema de `TechnologyMention` | `technology_mentions` separa tecnologia/ferramenta de conceito tecnico abstrato |
| T03.15 | concluida | Criar schema de `ProcessingNote` | `processing_notes` registra correcoes, incertezas e cuidados sem prompt integral |
| T03.16 | concluida | Criar schema de `Source` | `source` representa origem `raw_text` ou `audio` sem vazamento sensivel |
| T03.17 | concluida | Criar schema de `ProcessingEngine` | `processing_engine` identifica modo/modelo sem token, chave ou path local |
| T03.18 | concluida | Criar camada `postprocessing_service` | Router nao contem logica completa de LLM ou pos-processamento |
| T03.19 | concluida | Criar cliente OpenAI-compatible isolado | Cliente conversa com `MINDVOX_LLM_BASE_URL` e `MINDVOX_LLM_MODEL` |
| T03.20 | concluida | Implementar modo `contract` | Modo retorna resposta controlada e se identifica em `processing_engine` |
| T03.21 | concluida | Implementar modo `provider` | Modo usa provider externo OpenAI-compatible quando configurado |
| T03.22 | concluida | Implementar modo `local` | Modo usa servidor local OpenAI-compatible, como `llama-server` |
| T03.23 | concluida | Manter modelo local preferencial configuravel | Preferencial e `qwen35a3b-q8`, sem path hard-coded no codigo ou contrato |
| T03.24 | concluida | Manter provider sugerido configuravel | Groq `llama-3.3-70b-versatile` e sugestao, nao dependencia obrigatoria |
| T03.25 | concluida | Implementar timeout controlado do motor textual | Timeout gera `504 Gateway Timeout` |
| T03.26 | concluida | Implementar validacao de saida estruturada do LLM | Saida sem campos obrigatorios gera erro controlado sem vazar resposta integral |
| T03.27 | concluida | Implementar erro para saida invalida do motor | Erro controlado nao expõe prompt, resposta integral, chave ou path |
| T03.27.1 | concluida | Enviar limite de tokens ao motor LLM | Cliente OpenAI-compatible envia `max_tokens` baseado em `MINDVOX_LLM_MAX_OUTPUT_TOKENS` |
| T03.27.2 | concluida | Limitar leitura da resposta LLM | Cliente rejeita resposta excessiva antes de parsear JSON |
| T03.27.3 | concluida | Validar destino do motor conforme modo | `provider` rejeita URL local/privada, inclusive hostname resolvido por DNS para IP privado, e `local` rejeita URL publica |
| T03.27.4 | concluida | Sanitizar nome publico do provider | `processing_engine.name` redige provider configurado com marcador sensivel |
| T03.27.5 | concluida | Limitar leitura de resposta no benchmark | `scripts/benchmark_e03_models.py` rejeita resposta HTTP excessiva |
| T03.27.6 | concluida | Implementar allowlist de host provider | `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` restringe hosts externos e e obrigatoria para provider em deploy publico |
| T03.27.13 | concluida | Normalizar saida quase correta do LLM | Aliases previsiveis, cerca Markdown, confianca em portugues e categorias equivalentes sao convertidos para o contrato sem aceitar saida inutil |
| T03.27.14 | concluida | Desativar thinking no `llama-server` local | Cliente envia `chat_template_kwargs.enable_thinking=false` em modo `local` para modelos Qwen entregarem JSON em `content` |
| T03.27.7 | concluida | Implementar autostart do `llama-server` em modo local | `MINDVOX_LOCAL_LLM_AUTOSTART=true` tenta iniciar o motor local no startup da aplicacao |
| T03.27.8 | concluida | Falhar claramente quando autostart local nao funcionar | Falta de binario, modelo ou prontidao gera erro explicito de inicializacao |
| T03.27.9 | concluida | Garantir que modo `contract` nao inicia Llama | Testes automatizados nao acionam `llama-server` |
| T03.27.10 | concluida | Criar perfis de inicializacao `contract` e `prod` | `fastapi dev contract` seleciona contrato sem Llama; `fastapi run prod` seleciona hardening publico |
| T03.27.11 | concluida | Exibir perfil ativo no Swagger | `MINDVOX_RUNTIME_PROFILE` e inferido ou definido pelos perfis e aparece como `Active startup profile` no OpenAPI/Swagger |
| T03.27.12 | concluida | Normalizar `main` para perfil `dev` | `fastapi dev` pela entrada principal nao reaproveita modo `contract` herdado; usa transcricao `real`, pos-processamento `auto -> local` e pipeline longo `tfidf` |
| T03.28 | concluida | Criar router `src/routers/processed_transcriptions.py` | Router declara `POST /processed-transcriptions/v1.0.0` |
| T03.29 | concluida | Registrar router em `src/main.py` | App inclui a rota da E03 sem quebrar E01/E02 |
| T03.30 | concluida | Implementar autenticacao Bearer | Endpoint exige `Authorization: Bearer <token>` |
| T03.31 | concluida | Rejeitar token ausente | Requisicao sem token retorna `401 Unauthorized` |
| T03.32 | concluida | Rejeitar token invalido | Bearer invalido retorna `401 Unauthorized` |
| T03.33 | concluida | Rejeitar header `Authorization` malformado | Header fora do formato `Bearer <token>` retorna `401 Unauthorized` |
| T03.34 | concluida | Implementar `multipart/form-data` | Endpoint recebe audio, texto bruto e metadados por formulario |
| T03.35 | concluida | Validar `input_type` por `Enum` | OpenAPI/Swagger apresenta lista de selecao com `audio`, `raw_text` e alias `raw_text_file`; internamente o alias normaliza para `raw_text` |
| T03.36 | concluida | Validar fluxo `input_type=raw_text` | Exatamente uma fonte textual e obrigatoria: `raw_text` ou `raw_text_file`; `audio_file` real e proibido |
| T03.36.1 | concluida | Aceitar `raw_text_file` para reprocessamento | `input_type=raw_text` aceita arquivo `.txt` como alternativa a colar `raw_text` |
| T03.36.2 | concluida | Tratar placeholder vazio de upload opcional | Arquivo opcional sem nome enviado pelo Swagger e tratado como ausente |
| T03.36.3 | concluida | Tratar placeholder legado `string` como ausente | Campos textuais opcionais iniciam vazios no OpenAPI/Swagger; se cliente antigo ou tela cacheada enviar `string`, o valor e tratado defensivamente como ausente |
| T03.36.4 | concluida | Aceitar alias `input_type=raw_text_file` | Valor e normalizado para `raw_text` quando o usuario anexar transcricao `.txt` pelo Swagger |
| T03.37 | concluida | Validar fluxo `input_type=audio` | `audio_file` e obrigatorio e `raw_text` proibido |
| T03.38 | concluida | Rejeitar entrada principal ausente | Entrada ausente retorna `422 Unprocessable Entity` |
| T03.39 | concluida | Rejeitar entradas principais conflitantes | `audio_file` com `raw_text`/`raw_text_file` ou `raw_text` com `raw_text_file` retorna `422 Unprocessable Entity` |
| T03.40 | concluida | Validar limite de `raw_text` | Texto acima de `MINDVOX_POSTPROCESSING_MAX_INPUT_CHARS` retorna `413 Payload Too Large` |
| T03.40.1 | concluida | Validar arquivo de texto bruto | `raw_text_file` exige `.txt`, UTF-8, conteudo nao vazio e limite de caracteres |
| T03.41 | concluida | Validar extensao de audio | Apenas `.wav` e `.m4a` sao aceitas no MVP |
| T03.42 | concluida | Validar content type de audio | Content type incompativel retorna `400 Bad Request` |
| T03.43 | concluida | Validar tamanho de audio | Upload acima de `MINDVOX_MAX_UPLOAD_MB` retorna `413 Payload Too Large` por leitura incremental |
| T03.44 | concluida | Validar metadados opcionais | `course`, `discipline`, `class_date`, `class_title`, `session_label` e `language` seguem regras da Spec |
| T03.44.1 | concluida | Limitar metadados opcionais textuais | `course` ate `160`, `discipline` ate `120` e `class_title` ate `200` caracteres; excesso retorna `422` |
| T03.44.2 | concluida | Aplicar defaults do nome de `raw_text_file` preparado | Arquivo `YYYY-MM-DD-...-aula-N-sessao-M.txt` preenche metadados ausentes; metadados explicitamente enviados pelo usuario prevalecem e diferencas sao registradas em log saneado, sem `422` |
| T03.44.3 | concluida | Registrar metadados saneados recebidos no E03 | Log registra filename e metadados saneados, sem bruto, prompt, token ou chave, para auditoria de divergencia |
| T03.45 | concluida | Validar `processing_profile` | Apenas `study_notes` e aceito no MVP |
| T03.46 | concluida | Implementar fluxo com `raw_text` | Texto bruto fornecido segue direto ao `postprocessing_service` |
| T03.47 | concluida | Implementar fluxo com `audio` | Audio chama internamente `transcription_service` antes do pos-processamento |
| T03.47.1 | concluida | Salvar bruto STT gerado por E03 audio | Quando `input_type=audio`, a transcricao interna gera JSON tecnico em `outputs/transcriptions/` e TXT humano em `outputs/human/transcriptions/` |
| T03.47.2 | concluida | Enfileirar bruto STT gerado por E03 audio | Transcricao gerada por E03 entra em fila local de pos-processamento antes da chamada LLM |
| T03.47.3 | concluida | Salvar resposta processada da E03 | Resposta processada gera artefato `.json` em `MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR` |
| T03.47.4 | concluida | Salvar artefato humano Markdown da E03 | Resposta processada gera `.md` legivel para humano em `outputs/human/processed_transcriptions/` |
| T03.47.5 | concluida | Criar cliente local de submit do `.metadata.json` | `scripts/submit_e03_raw_text.py` le o `.metadata.json`, anexa o `.txt` e chama o E03 com os metadados corretos |
| T03.47.6 | concluida | Permitir preparar e submeter em um comando | `prepare_e03_raw_text_from_vault.py --section N --submit` prepara o arquivo e aciona o E03 |
| T03.47.7 | concluida | Expor `artifact_locations` na resposta | Swagger informa caminhos relativos do artefato humano e do JSON tecnico, sem path absoluto local |
| T03.47.7.1 | concluida | Nomear artefatos processados com metadados seguros | Arquivos locais podem usar prefixo sanitizado de data/titulo/sessao e sempre terminam com `processed_transcription_id` opaco |
| T03.47.7.2 | concluida | Titular Markdown humano por metadados | Markdown processado usa titulo legivel e bloco curto de metadados quando enviados |
| T03.47.8 | concluida | Manter job pendente quando pos-processamento falhar | Falha de motor apos STT deixa job em `queue/pending` para retry automatico |
| T03.47.9 | concluida | Implementar retry automatico de fila | App processa jobs pendentes quando estiver rodando com motor real disponivel |
| T03.48 | concluida | Proibir chamada HTTP interna para E02 | E03 nao chama `POST /transcriptions/v1.0.0` por HTTP dentro do app |
| T03.49 | concluida | Montar `source` para `raw_text` | `source.input_origin=raw_text`, `source.raw_text_origin=provided_by_client` e `source.transcription=null` |
| T03.50 | concluida | Montar `source` para `audio` | `source` inclui dados controlados da STT, sem bruto indevido alem de `raw_text` |
| T03.51 | concluida | Gerar `processed_transcription_id` opaco | Identificador usa prefixo controlado e nao incorpora dado sensivel |
| T03.52 | concluida | Montar `raw_text` | Bruto e preservado integralmente, salvo erro por limite |
| T03.53 | concluida | Montar `didactic_text` | Texto corrido, logico, didatico, sem titulos internos e com redundancias reduzidas |
| T03.53.1 | concluida | Impedir resumo excessivo em bruto longo | Saida LLM semanticamente insuficiente aciona retry com instrucao mais rigorosa e, se persistir, retorna erro controlado |
| T03.53.2 | concluida | Reforcar manual operacional da E03 | Prompt exige preservacao de projetos, cases, contribuicoes de alunos, dores reais, exemplos, metaforas, arquiteturas, tecnologias e decisoes metodologicas |
| T03.53.3 | concluida | Proteger ancoras semanticas do bruto | Backend detecta projetos, empresas, tecnologias, arquiteturas, dores, cases e contribuicoes nominais relevantes, lista no prompt e rejeita saida longa que omita essas ancoras |
| T03.53.4 | concluida | Criar configuracao do pipeline longo da E03 | `MINDVOX_POSTPROCESSING_CHUNKING_MODE`, `MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS`, `MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS`, `MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED` e `MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED` sao lidas de configuracao |
| T03.53.5 | concluida | Implementar pre-auditoria sistemica antes do Qwen | Formas canonicas validadas (`CIGA`, `UFNDE`, `IAC`, `ICTI`, `EPT`, `GROC`) sao normalizadas em texto interno derivado, preservando `raw_text` original |
| T03.53.6 | concluida | Informar contexto de pre-auditoria ao prompt | Motor textual recebe bloco operacional delimitado com status da pre-auditoria, substituicoes e suspeitas remanescentes |
| T03.53.7 | concluida | Implementar chunking TF-IDF interno | Transcricoes longas sao divididas em chunks em memoria, sem banco vetorial e sem alterar o contrato HTTP |
| T03.53.8 | concluida | Processar chunks independentemente | Cada chunk passa pelo mesmo contrato E03 e por validacao estrutural da saida LLM |
| T03.53.9 | concluida | Implementar merge canonico deterministico | `didactic_text` e recomposto em ordem, listas sao deduplicadas e `processing_notes` preservam rastreabilidade por chunk |
| T03.53.10 | concluida | Implementar auditoria final dos artefatos semanticos | Auditoria final examina `didactic_text`, `themes`, `technical_terms` e `technology_mentions`, sem tratar `processing_notes` como conteudo semantico |
| T03.53.10.1 | concluida | Ajustar freio de cobertura para merge chunked | Fluxo chunked usa regua de tamanho propria para evitar falso 500 em merge canonico compacto; tamanho minimo e temas continuam bloqueantes, enquanto ancoras ausentes viram nota de auditoria |
| T03.53.10.2 | concluida | Criar quarentena de saidas LLM rejeitadas | Saidas estruturalmente validas, mas reprovadas por cobertura semantica, geram JSON tecnico em `outputs/processed_transcriptions/rejected/` e relatorio humano em `outputs/human/processed_transcriptions/rejected/` |
| T03.53.10.2.1 | concluida | Registrar `runtime_snapshot` na quarentena | JSON e relatorio humano de saida rejeitada informam modo de chunking, quantidade de chunks, limite de saida do LLM, modelo e regua semantica aplicada |
| T03.53.10.3 | concluida | Trocar rejeicao semantica final de `500` generico para `502` estruturado | Resposta usa `error_code=postprocessing_quality_rejected`, informa tentativa, limite, `retry_hint` e caminhos dos artefatos rejeitados |
| T03.53.10.4 | concluida | Limitar retries da fila E03 | `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS` controla tentativas e move jobs esgotados para `queue/failed/` |
| T03.53.10.5 | concluida | Remover regua monolitica de chunks individuais | Chunks longos recebem prompt local sem minimo monolitico de tamanho, temas e ancoras; a validacao bloqueante fica no merge final |
| T03.53.10.6 | concluida | Reduzir falsos positivos de ancoras e ruido STT | Palavras discursivas capitalizadas deixam de virar nomes proprios protegidos e sequencias repetitivas de STT sao limpas apenas no texto interno do LLM |
| T03.53.11 | concluida | Manter fluxo curto sem regressao | Com chunking `off` ou texto curto, E03 continua usando a chamada unica ja testada |
| T03.53.12 | concluida | Testar pipeline longo em modo `contract` | Testes automatizados provam pre-auditoria, chunking, merge, auditoria final e preservacao de `raw_text` original |
| T03.54 | concluida | Montar `themes` | Temas semanticos ficam estruturados para estudo e futura E04 |
| T03.55 | concluida | Montar `technical_terms` | Termos tecnicos sao normalizados ou marcados com confianca apropriada |
| T03.56 | concluida | Montar `technology_mentions` | Apenas tecnologias citadas ou fortemente indicadas no bruto sao listadas |
| T03.57 | concluida | Impedir invencao de tecnologias | Resultado nao sugere tecnologias relacionadas que nao apareceram na aula |
| T03.58 | concluida | Montar `processing_notes` | Notas registram correcoes/incertezas sem raciocinio interno ou prompt integral |
| T03.59 | concluida | Montar `metadata` | Metadados de curso/aula/sessao aparecem normalizados quando enviados |
| T03.60 | concluida | Montar `processing_engine` | Modo, provider/modelo e versao aparecem sem path local, segredo ou provider sensivel |
| T03.61 | concluida | Omitir `corrected_full_text` como saida padrao | Resposta nao duplica transcricao quase integral como requisito do MVP |
| T03.62 | concluida | Implementar erro `400` | Arquivo ou content type invalido retorna `400 Bad Request` |
| T03.63 | concluida | Implementar erro `401` | Token ausente, invalido ou malformado retorna `401 Unauthorized` |
| T03.63.1 | concluida | Implementar erro `403` para transporte inseguro publico | Endpoint protegido retorna `403 Forbidden` quando deploy publico exigir HTTPS e a requisicao nao atender a regra |
| T03.64 | concluida | Implementar erro `405` | Metodo errado retorna `405 Method Not Allowed` |
| T03.65 | concluida | Implementar erro `413` | Texto ou audio acima do limite retorna `413 Payload Too Large` |
| T03.66 | concluida | Implementar erro `422` | Entrada ausente, conflitante ou metadado invalido retorna `422 Unprocessable Entity` |
| T03.67 | concluida | Implementar erro `500` | Erro inesperado retorna `500` sem vazamento sensivel |
| T03.68 | concluida | Implementar erro `503` | Motor local/provider/STT indisponivel retorna `503 Service Unavailable` |
| T03.69 | concluida | Implementar erro `503` para placeholder de chave | Modo `provider` com chave vazia ou placeholder retorna `503 Service Unavailable` |
| T03.70 | concluida | Implementar erro `504` | Timeout de provider ou servidor local retorna `504 Gateway Timeout` |
| T03.71 | concluida | Sanitizar respostas e erros | Respostas e erros nao expõem token, `.env`, path local, prompt integral, bruto integral indevido ou resposta integral do provider |
| T03.72 | concluida | Registrar logs operacionais permitidos | Logs registram apenas eventos, modo, duracao, status, fase e codigos controlados |
| T03.73 | concluida | Proibir vazamento em logs | Logs nao registram audio bruto, transcricao integral, texto processado integral, prompt integral, resposta integral, token, chave ou path sensivel |
| T03.74 | concluida | Decidir persistencia de logs | E03 nao cria persistencia propria de logs no MVP |
| T03.75 | concluida | Configurar OpenAPI summary | Summary deve ser `Post-process class transcription` |
| T03.76 | concluida | Configurar OpenAPI description | Description explica as cinco entregas, ausencia de memoria/busca e privacidade do modo `provider` |
| T03.77 | concluida | Documentar didaticamente cada campo do formulario | Campos possuem descricao em ingles e exemplo curto conforme E03/P03 |
| T03.77.1 | concluida | Explicar valores exatos de `input_type` no Swagger | OpenAPI informa que `input_type` e `Enum` com lista de selecao para `audio`, `raw_text` e alias `raw_text_file`, em ingles, minusculo, sem traducao e sem acento |
| T03.77.2 | concluida | Explicar fluxo de texto ja transcrito no Swagger | OpenAPI informa que, para texto ja transcrito, deve-se usar `input_type=raw_text`, preencher `raw_text` ou `raw_text_file`, e deixar `audio_file` vazio |
| T03.77.3 | concluida | Explicar fluxo de audio no Swagger | OpenAPI informa que, para audio, deve-se usar `input_type=audio`, preencher `audio_file` e deixar `raw_text` e `raw_text_file` vazios |
| T03.77.4 | concluida | Explicar reprocessamento por arquivo `.txt` no Swagger | OpenAPI informa que `raw_text_file` permite reenviar transcricao longa ja existente sem repetir STT |
| T03.78 | concluida | Documentar Bearer token no OpenAPI | Swagger mostra esquema de autenticacao correto |
| T03.79 | concluida | Documentar respostas de erro no OpenAPI | `400`, `401`, `403`, `405`, `413`, `422`, `500`, `502`, `503` e `504` aparecem |
| T03.80 | concluida | Documentar schemas de resposta no OpenAPI | Campos e subcampos principais aparecem na documentacao |
| T03.81 | concluida | Garantir README da pasta de testes atualizado | README cobre contrato, erros, seguranca, logs, modo `contract`, provider e placeholder de chave |
| T03.82 | concluida | Criar `test_processed_transcriptions.py` | Testes executaveis da E03 existem na pasta propria |
| T03.83 | concluida | Manter teste documental da matriz | `test_e03_test_plan_documents_required_contract` continua passando |
| T03.84 | concluida | Criar teste de sucesso com `raw_text` em modo `contract` | `test_post_processed_transcriptions_raw_text_contract_success` passa |
| T03.84.1 | concluida | Criar teste de sucesso com `raw_text_file` em modo `contract` | `test_post_processed_transcriptions_raw_text_file_contract_success` passa |
| T03.84.2 | concluida | Criar teste de placeholder legado `string` em campo opcional | `test_raw_text_file_ignores_legacy_swagger_string_placeholder` passa |
| T03.84.3 | concluida | Criar teste de alias `input_type=raw_text_file` | `test_raw_text_file_input_type_alias_is_normalized_to_raw_text` passa |
| T03.85 | concluida | Criar teste de schema de sucesso | `test_success_response_contains_five_deliveries_and_auxiliary_fields` passa |
| T03.86 | concluida | Criar teste de `source` com `raw_text` | `test_raw_text_source_has_no_transcription_object` passa |
| T03.87 | concluida | Criar teste de sucesso com audio em modo `contract` | `test_post_processed_transcriptions_audio_contract_success` passa quando viavel |
| T03.87.1 | concluida | Criar teste de artefato bruto no fluxo de audio | `test_audio_flow_saves_internal_raw_transcription_artifacts` confirma JSON e TXT da transcricao interna |
| T03.88 | concluida | Criar teste de autenticacao ausente | `test_missing_token_returns_401` passa |
| T03.88.1 | concluida | Criar teste de token invalido | `test_invalid_token_returns_401` passa |
| T03.89 | concluida | Criar teste de header malformado | `test_malformed_authorization_header_returns_401` passa |
| T03.90 | concluida | Criar teste de entrada principal ausente | `test_missing_main_input_returns_422` passa |
| T03.91 | concluida | Criar teste de conflito audio/texto | `test_audio_and_raw_text_conflict_returns_422` passa |
| T03.91.1 | concluida | Criar teste de placeholder vazio de arquivo | `test_raw_text_flow_ignores_empty_audio_file_placeholder` passa |
| T03.91.2 | concluida | Criar teste de conflito texto/arquivo | `test_raw_text_and_raw_text_file_conflict_returns_422` passa |
| T03.91.3 | concluida | Criar teste de conflito audio/arquivo texto | `test_audio_and_raw_text_file_conflict_returns_422` passa |
| T03.92 | concluida | Criar teste de perfil invalido | `test_invalid_processing_profile_returns_422` passa |
| T03.93 | concluida | Criar teste de extensao invalida | `test_invalid_audio_extension_returns_400` passa |
| T03.93.1 | concluida | Criar teste de extensao invalida de `raw_text_file` | `test_invalid_raw_text_file_extension_returns_400` passa |
| T03.94 | concluida | Criar teste de limite de texto | `test_raw_text_over_limit_returns_413` passa |
| T03.95 | concluida | Criar teste de limite de audio | `test_audio_over_upload_limit_returns_413` passa |
| T03.96 | concluida | Criar teste de motor indisponivel | `test_unavailable_processing_engine_returns_503` passa |
| T03.97 | concluida | Criar teste de placeholder de provider | `test_placeholder_provider_key_returns_503` passa |
| T03.98 | concluida | Criar teste de timeout | `test_processing_engine_timeout_returns_504` passa |
| T03.99 | concluida | Criar teste de metodo invalido | `test_get_processed_transcriptions_returns_405` passa |
| T03.100 | concluida | Criar teste de OpenAPI | `test_openapi_documents_e03_contract` passa |
| T03.101 | concluida | Criar teste de nao vazamento em respostas e erros | `test_response_and_errors_do_not_expose_sensitive_values` passa |
| T03.102 | concluida | Criar teste de logs sanitizados | `test_e03_logs_are_sanitized` passa |
| T03.102.1 | concluida | Criar teste de logs de erros controlados | `test_controlled_validation_errors_are_logged_without_sensitive_values` passa |
| T03.102.2 | concluida | Criar teste de `input_type` invalido | `test_invalid_input_type_returns_422` passa |
| T03.102.3 | concluida | Criar testes de entrada audio incompleta/incompativel | `test_audio_input_without_audio_file_returns_422` e `test_incompatible_audio_content_type_returns_400` passam |
| T03.102.4 | concluida | Criar teste de metadado invalido | `test_invalid_metadata_returns_422` passa |
| T03.102.5 | concluida | Criar testes de destino LLM | `test_provider_mode_rejects_localhost_endpoint` e `test_local_mode_rejects_public_endpoint` passam |
| T03.102.6 | concluida | Criar teste de modo local indisponivel | `test_local_unavailable_processing_engine_returns_503` passa |
| T03.102.7 | concluida | Criar testes de limite de saida LLM | `test_llm_client_sends_max_tokens_and_limits_response_size` e `test_llm_client_rejects_excessive_response_body` passam |
| T03.102.7.0 | concluida | Criar teste do manual operacional E03 | `test_llm_prompt_uses_e03_manual_without_concise_instruction` passa |
| T03.102.7.0.1 | concluida | Criar teste de rejeicao de resumo excessivo | `test_long_llm_output_with_insufficient_semantic_coverage_returns_502_with_rejected_artifact` passa |
| T03.102.7.0.2 | concluida | Criar teste de retry por cobertura semantica | `test_long_llm_output_retry_can_recover_semantic_coverage` passa |
| T03.102.7.0.3 | concluida | Criar teste de rejeicao por omissao de ancoras semanticas | `test_long_llm_output_missing_semantic_anchors_returns_502` passa |
| T03.102.7.0.4 | concluida | Criar teste de prompt com ancoras protegidas | `test_llm_prompt_lists_protected_semantic_anchors_for_long_transcript` passa |
| T03.102.7.0.5 | concluida | Criar testes da politica chunked de cobertura | Compactacao valida passa com regua chunked; omissao de ancoras no fluxo chunked gera `semantic_anchor_audit` e `processing_notes` nao satisfaz cobertura |
| T03.102.7.0.6 | concluida | Criar testes contra falsos positivos de ancoras protegidas | `Positivo` exige contexto nominal minimo, `score` isolado nao vira score de viabilidade e `microsserviços` acentuado satisfaz `microservicos` |
| T03.102.7.0.7 | concluida | Criar teste de falha permanente da fila por qualidade | `test_audio_flow_moves_quality_failure_to_failed_after_max_attempts` passa |
| T03.102.7.0.8 | concluida | Criar teste de prompt local de chunk | `test_chunk_llm_prompt_does_not_apply_full_transcript_semantic_gate` passa |
| T03.102.7.0.9 | concluida | Criar teste de ruido STT repetitivo | `test_pre_audit_removes_repetitive_transcription_noise_only_from_llm_text` passa |
| T03.102.7.0.10 | concluida | Criar teste de palavras discursivas capitalizadas | `test_semantic_anchors_ignore_capitalized_discourse_words` passa |
| T03.102.7.1 | concluida | Criar testes de thinking local | `test_llm_client_disables_thinking_for_local_llama_server` e `test_llm_client_does_not_send_local_template_kwargs_to_provider` passam |
| T03.102.8 | concluida | Criar teste de saida invalida do LLM | `test_invalid_llm_output_returns_500` passa |
| T03.102.9 | concluida | Criar teste de limite LLM invalido | `test_zero_llm_max_output_tokens_falls_back_to_default` passa |
| T03.102.9.1 | concluida | Criar teste de slots invalidos do `llama-server` | `test_zero_llama_server_parallel_falls_back_to_default` passa |
| T03.102.10 | concluida | Criar teste de leitura incremental de upload | `test_limited_upload_reader_rejects_before_reading_full_oversized_upload` passa |
| T03.102.11 | concluida | Criar teste de hostname provider resolvido para IP privado | `test_provider_mode_rejects_hostname_resolving_to_private_address` passa |
| T03.102.12 | concluida | Criar teste de provider sensivel em `processing_engine` | `test_processing_engine_redacts_sensitive_provider_name` passa |
| T03.102.17 | concluida | Criar testes de normalizacao de saida LLM | `test_llm_output_with_common_aliases_is_normalized_to_e03_schema` e `test_payload_normalizer_accepts_markdown_json_fence` passam |
| T03.102.18 | concluida | Criar teste de artefato Markdown humano | `test_audio_flow_completes_generated_transcription_queue_job` confirma `.md` com texto didatico e secoes principais |
| T03.102.18.1 | concluida | Criar teste de titulo humano por metadados | `test_processed_markdown_artifact_uses_class_metadata_title` confirma nome seguro e titulo do Markdown com data/titulo/sessao |
| T03.102.18.2 | concluida | Criar teste de nomeacao segura compartilhada | `test_artifact_stem_uses_safe_class_metadata_prefix` confirma prefixo sanitizado e identificador opaco como sufixo |
| T03.102.13 | concluida | Criar teste de log de autenticacao da E03 | `test_processed_transcription_auth_failure_logs_status_error_and_duration` passa |
| T03.102.14 | concluida | Criar teste de limite do benchmark | `test_benchmark_script_rejects_excessive_response_body` passa |
| T03.102.15 | concluida | Criar teste de log de autenticacao da E02 afetada | `test_transcription_auth_failure_logs_status_error_and_duration` passa |
| T03.102.16 | concluida | Criar teste de metadado opcional grande | `test_oversized_optional_metadata_returns_422` passa |
| T03.102.18.3 | concluida | Criar teste de placeholder de token do app | `test_placeholder_api_token_configuration_returns_503` passa |
| T03.102.18.4 | concluida | Criar testes de allowlist provider | `test_provider_mode_rejects_hostname_outside_allowed_list` e `test_provider_mode_accepts_hostname_inside_allowed_list` passam |
| T03.102.19 | concluida | Criar testes de deploy publico | `test_public_deployment_requires_trusted_hosts`, `test_public_deployment_disables_docs_and_enforces_trusted_hosts` e `test_public_deployment_rejects_wildcard_trusted_hosts` passam |
| T03.102.20 | concluida | Criar teste de `dev-token` em deploy publico | `test_dev_token_configuration_returns_503_in_public_deployment` passa |
| T03.102.21 | concluida | Criar testes de transporte seguro em deploy publico | `test_public_deployment_requires_https_for_processed_transcriptions` e `test_public_deployment_accepts_https_for_processed_transcriptions` passam |
| T03.102.22 | concluida | Criar teste de clareza OpenAPI para `input_type` | `test_openapi_documents_e03_contract` valida valores exatos, ausencia de traducao e separacao entre `audio_file`, `raw_text` e `raw_text_file` |
| T03.102.23 | concluida | Criar testes de autostart do Llama | `test_contract_mode_does_not_start_llama_server`, autostart desabilitado, servidor existente, start, binario ausente, modelo ausente e timeout passam em `test_local_llm_runtime.py` |
| T03.102.24 | concluida | Criar testes de fila E03 | `test_audio_flow_completes_generated_transcription_queue_job`, `test_audio_flow_keeps_queue_job_pending_when_postprocessing_fails` e `test_pending_generated_transcription_job_can_be_retried_without_reupload` passam |
| T03.102.25 | concluida | Criar testes de token local automatico e perfis CLI | `test_local_development_without_api_token_uses_dev_token`, `test_public_deployment_without_api_token_has_no_default_token`, `test_contract_profile_forces_contract_modes_and_disables_llama_autostart` e `test_prod_profile_enables_public_hardening_without_dev_token_default` passam |
| T03.102.26 | concluida | Criar teste do perfil ativo no OpenAPI | `test_openapi_documents_e03_contract` valida `Active startup profile` no Swagger |
| T03.103 | concluida | Rodar verificacao de sintaxe | `py_compile` passa para arquivos da E03 e testes relacionados |
| T03.104 | concluida | Rodar testes da E03 | `uv run python -m unittest discover -s tests/e03_processed_transcriptions -v` passa |
| T03.105 | concluida | Rodar suite geral | `uv run python -m unittest discover -s tests -v` passa |
| T03.106 | concluida | Subir app em modo `contract` | Aplicacao sobe com `MINDVOX_TRANSCRIPTION_MODE=contract` e `MINDVOX_POSTPROCESSING_MODE=auto`, resultando em contrato nos dois motores |
| T03.107 | concluida | Conferir `/docs` | Swagger exibe rota, campos, descricoes, Bearer, cinco entregas, erros e regra de provider |
| T03.108 | concluida | Conferir `/openapi.json` | Contrato real reflete E03/P03 |
| T03.109 | concluida | Executar teste manual valido com `raw_text` em modo `contract` | Retorna `200 OK` e cinco entregas |
| T03.110 | concluida | Executar teste manual valido com `audio_file` em modo `contract` | Quando viavel, retorna `200 OK` e cinco entregas |
| T03.111 | concluida | Executar teste manual invalido sem token | Retorna `401 Unauthorized` |
| T03.112 | concluida | Executar teste manual invalido com entrada conflitante | Retorna `422 Unprocessable Entity` |
| T03.113 | pendente | Executar prova real humana em modo `local` ou `provider` | Entrada real representativa gera resultado coerente com contrato; deve ser repetida apos a correcao do freio de cobertura semantica |
| T03.114 | pendente | Registrar prova real humana | Registro inclui modo, modelo/provider, tempo, status HTTP, avaliacao das cinco entregas e privacidade do provider quando aplicavel |
| T03.115 | concluida | Atualizar checklist aplicavel da E03 | Checklist da Spec E03 reflete implementacao, testes, OpenAPI, logs, prova humana e Git |
| T03.116 | concluida | Atualizar T03 apos implementacao | Status de cada tarefa fica coerente com evidencias |
| T03.117 | concluida | Atualizar README do projeto se necessario | README reflete instrucao real de uso da E03 |
| T03.118 | N/A | Atualizar material didatico externo ao repo quando aplicavel | Nao aplicavel nesta etapa de implementacao de codigo; material de apresentacao pode ser atualizado em etapa propria |
| T03.119 | concluida | Revisar `git status` | Apenas arquivos da E03 ou justificaveis aparecem |
| T03.120 | concluida | Revisar `git diff` | Diff e coerente com E03, P03 e T03 |
| T03.121 | concluida | Verificar ausencia de segredos | Diff nao contem token real, chave real, `.env`, path sensivel ou dado privado indevido |
| T03.122 | concluida | Verificar ausencia de artefatos indevidos | Diff nao contem cache, `__pycache__`, temporario, audio real, transcricao real ou benchmark gerado indevido |
| T03.122.1 | concluida | Endurecer script de benchmark contra chave literal | `scripts/benchmark_e03_models.py` aceita nome de variavel de ambiente, nao chave literal em argumento CLI |
| T03.122.2 | concluida | Alinhar schema do benchmark ao contrato E03 | `processing_notes` do benchmark usa objetos, nao strings soltas |
| T03.122.3 | concluida | Registrar relatorio de correcao da auditoria | `RELATORIO_CORRECAO_AUDITORIA_IMPLEMENTACAO_E03.md` registra matriz de falhas, acoes e validacoes |
| T03.123 | pendente | Definir mensagem de commit | Mensagem identifica a E03 concluida |
| T03.124 | pendente | Realizar commit de fechamento | Commit de fechamento ocorre antes de iniciar E04 |
| T03.125 | concluida | Definir schema interno de `StudyPackage` | Schema cobre metadados, fonte, bruto, texto didatico, temas, termos, tecnologias, ancoras operacionais, conceitos candidatos, auditoria, `memory_manifest` e exportacoes |
| T03.126 | concluida | Montar `StudyPackage` a partir da resposta E03 | Toda resposta real consegue gerar envelope canonico sem remover as cinco entregas publicas de topo |
| T03.127 | concluida | Persistir `StudyPackage` em artefato local | Arquivo tecnico e gerado em `MINDVOX_E03_STUDY_PACKAGE_OUTPUT_DIR` ou default documentado |
| T03.128 | concluida | Criar `memory_manifest` para futura E04 | Manifest separa dados relacionais para SQLite e candidatos vetoriais sem executar ingestao |
| T03.129 | pendente | Extrair `operational_anchors` no `StudyPackage` | Links, prazos, entregas, eventos, contatos, canais e documentos aparecem separados quando detectados |
| T03.130 | concluida | Criar `concept_candidates` no `StudyPackage` | Temas e termos podem gerar candidatos sem promover automaticamente conceitos incertos |
| T03.131 | concluida | Criar armazenamento local de cursos cadastrados | Curso ativo e lista de cursos ficam persistidos em arquivo/config local sem exigir banco relacional |
| T03.132 | concluida | Persistir curso ativo | Novo processamento reaproveita ultimo curso ativo ate mudanca explicita do usuario |
| T03.133 | pendente | Criar seletor/lista flutuante de cursos cadastrados | Usuario pode escolher curso ja cadastrado sem redigitar nome |
| T03.134 | pendente | Criar pagina humana de entrada da E03 | Pagina aceita audio, texto colado e arquivo `.txt`, com metadados de curso/aula/sessao |
| T03.135 | pendente | Renderizar `raw_text` como textarea ampla | Usuario consegue colar e visualizar transcricoes longas sem campo de linha unica |
| T03.136 | pendente | Normalizar entrada da pagina humana para contrato interno E03 | Pagina, Swagger/API e scripts locais convergem para mesmo fluxo de processamento |
| T03.137 | pendente | Adaptar script do Vault para alimentar pagina humana | `prepare_e03_raw_text_from_vault.py` prepara `.txt` e metadados para preenchimento visivel ou entrada equivalente |
| T03.138 | concluida | Garantir comando com path absoluto para script local | Instrucao ao usuario evita erro de diretorio ao preparar transcritos do Vault |
| T03.139 | pendente | Criar pagina humana de resultado | Pagina renderiza `StudyPackage` em visao geral, texto didatico, temas, conceitos, termos, tecnologias, ancoras, bruto, auditoria e exportacoes |
| T03.140 | pendente | Exibir resultado automaticamente apos processamento pela pagina humana | Fluxo abre pagina/modal/drawer/janela de resultado sem depender do Swagger |
| T03.141 | concluida | Criar script/servico de criacao deterministica de Student Vault | Dado `course_id`, `course_name`, `institution` e path base, cria novo Vault padronizado |
| T03.142 | concluida | Bloquear importacao de Vault existente na v1 | Fluxo Obsidian v1 cria Vault novo e nao tenta selecionar, validar, corrigir ou importar Vault existente |
| T03.143 | concluida | Registrar `vault_path` por curso ativo | Curso criado com opcao Obsidian guarda destino local de exportacao |
| T03.144 | concluida | Criar exportador opcional de `StudyPackage` para Student Vault | Exportador escreve nos nichos padronizados do Vault criado sem inventar estrutura |
| T03.145 | concluida | Mapear bruto auditavel para Student Vault | `raw_transcription` vai para nicho de brutos da disciplina |
| T03.146 | concluida | Mapear texto didatico para Student Vault | `didactic_text` vai para nicho de aulas/textos didaticos da disciplina |
| T03.147 | concluida | Mapear ancoras operacionais para Student Vault | Links, prazos, contatos, canais e documentos vao para `03_Operacional` quando exportacao estiver ativa |
| T03.148 | concluida | Manter Obsidian opcional | E03 funciona sem Obsidian e com `MINDVOX_E03_OBSIDIAN_EXPORT_ENABLED=false` |
| T03.149 | concluida | Criar testes do `StudyPackage` | Testes validam schema, montagem, persistencia e compatibilidade com cinco entregas de topo |
| T03.150 | concluida | Criar testes de curso ativo | Testes validam persistencia de curso, selecao de curso cadastrado e mudanca explicita |
| T03.151 | pendente | Criar testes da pagina humana de entrada | Testes validam campos, textarea, metadados e normalizacao para contrato interno |
| T03.152 | pendente | Criar testes da pagina humana de resultado | Testes validam renderizacao dos nichos do `StudyPackage` |
| T03.153 | concluida | Criar testes de criacao de Student Vault | Testes validam estrutura deterministica minima e arquivos operacionais basicos |
| T03.154 | concluida | Criar testes de exportacao Obsidian opcional | Testes validam mapeamento para Vault criado e ausencia de dependencia quando desativado |
| T03.155 | pendente | Atualizar README do projeto para nova camada humana | README explica fluxo sem Obsidian, fluxo local com Vault, criacao opcional de Vault e papel do `StudyPackage` |
| T03.156 | concluida | Atualizar README/indice de relatórios quando necessario | Relatorios evolutivos continuam orientados para evitar leitura de estado legado como atual |
| T03.157 | pendente | Executar prova real com pagina humana | Entrada real processa pela pagina humana e exibe resultado legivel |
| T03.158 | pendente | Executar prova real do fluxo local a partir do Vault | Transcrito em `_captura-rapida.md` gera `.txt`, metadados e entrada visivel para E03 |
| T03.159 | concluida | Executar prova real de `StudyPackage` consumivel | Artefato gerado contem `memory_manifest` e secoes suficientes para futura E04 |
| T03.160 | pendente | Registrar prova real da camada humana | Registro inclui entrada, curso ativo, modo, resultado, artefatos, pagina e avaliacao humana |

---

## 5. Comandos de Verificacao

Verificacao de sintaxe:

```bash
uv run python -m py_compile src/main.py src/settings.py src/routers/endpoint_security.py src/routers/processed_transcriptions.py src/schemas/processed_transcriptions.py src/services/transcription_service.py src/services/postprocessing_service.py src/services/postprocessing_pipeline.py src/services/llm_client.py src/services/local_llm_runtime.py src/services/processed_transcription_artifacts.py src/services/processed_transcription_queue.py tests/e03_processed_transcriptions/test_e03_test_plan.py tests/e03_processed_transcriptions/test_processed_transcriptions.py tests/e03_processed_transcriptions/test_local_llm_runtime.py tests/e03_processed_transcriptions/test_postprocessing_pipeline.py scripts/benchmark_e03_models.py
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

Aplicacao em modo `provider`:

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

No Swagger local, o Bearer token didatico continua sendo `dev-token`.

Observacao:

- `MINDVOX_LLM_API_KEY` real deve estar apenas no `.env` local da instalacao;
- valor vazio ou placeholder deve ser tratado como ausencia de chave em modo `provider`;
- chave de provider nao deve ser enviada pelo Swagger, pelo corpo da requisicao ou pelo Git.
- `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` deve restringir o hostname externo aceito em modo `provider`, especialmente em deploy publico;
- em deploy publico, `MINDVOX_PUBLIC_DEPLOYMENT=true` exige `MINDVOX_TRUSTED_HOSTS`, rejeita `MINDVOX_TRUSTED_HOSTS=*`, desabilita docs por padrao, bloqueia `dev-token` e exige transporte seguro nos endpoints protegidos.

Documentacao:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

---

## 6. Demonstracao Manual Prevista

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

Chamada invalida em modo `provider` com placeholder de chave:

```bash
MINDVOX_PUBLIC_DEPLOYMENT=false \
MINDVOX_API_TOKEN=dev-token \
MINDVOX_POSTPROCESSING_MODE=provider \
MINDVOX_LLM_PROVIDER=groq \
MINDVOX_LLM_BASE_URL=https://api.groq.com/openai/v1 \
MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS=api.groq.com \
MINDVOX_LLM_MODEL=llama-3.3-70b-versatile \
MINDVOX_LLM_API_KEY=replace-with-provider-key \
uv run fastapi dev src/main.py
```

Resultado esperado em chamada ao endpoint:

```text
503 Service Unavailable
```

---

## 7. Fora do Escopo

Estas tarefas nao implementam:

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
- fila assincrona;
- deploy em cloud;
- ingestao real do E04;
- E05.
- selecao, importacao, validacao ou correcao de Vault Obsidian existente.

---

## 8. Criterio de Encerramento

Estas tarefas poderao ser encerradas quando:

- todas as tarefas aplicaveis estiverem marcadas como `concluida`;
- itens nao aplicaveis estiverem marcados como `N/A`, com justificativa;
- divergencias estiverem justificadas no documento correto;
- o endpoint `POST /processed-transcriptions/v1.0.0` existir;
- o endpoint exigir Bearer token;
- a resposta de sucesso contiver as cinco entregas publicas e campos auxiliares;
- erros principais estiverem implementados e testados;
- hardening publico estiver implementado e testado, incluindo bloqueio de `dev-token`, rejeicao de wildcard em `MINDVOX_TRUSTED_HOSTS` e `403` para transporte inseguro;
- OpenAPI real refletir E03/P03;
- logs e respostas estiverem sanitizados;
- chave vazia ou placeholder de provider for tratada como ausente;
- testes automatizados da E03 passarem;
- suite geral passar;
- prova real humana do endpoint tiver sido executada com sucesso;
- resultado da prova real humana estiver registrado;
- `StudyPackage` estiver implementado, persistido e renderizado;
- pagina humana de entrada estiver funcional;
- pagina humana de saida estiver funcional;
- curso ativo persistente estiver funcional;
- criacao deterministica de Student Vault novo estiver funcional quando opcao Obsidian estiver ativa;
- exportacao opcional para Student Vault criado estiver funcional sem tornar Obsidian dependencia;
- checklist da Spec E03 estiver coerente;
- auditoria final de Git estiver limpa;
- commit de fechamento da E03 tiver sido realizado antes de iniciar E04.

---

## 9. Registro de Estado

Status atual: `implementada_em_validacao_real`.

Motivo do estado:

- Spec E03 e Plano P03 foram criados;
- E02 ja fornece transcricao bruta que a E03 deve processar;
- benchmark real definiu `Qwen3.6-35B-A3B-MTP-Q8.gguf` como modelo local preferencial;
- provider OpenAI-compatible foi previsto para portabilidade;
- matriz de testes da E03 ja foi criada;
- pasta de testes da E03 existe com README e cobertura automatizada;
- endpoint E03 foi implementado com fluxo curto e pipeline longo opcional;
- pipeline longo integra pre-auditoria, chunking TF-IDF, processamento por chunk, merge canonico e auditoria final;
- suite automatizada E03 passou;
- suite geral passou.
- emenda de interface humana, `StudyPackage` e Vault opcional foi canonizada em Spec/P03/T03.

Pendencias restantes para fechamento canonico:

- executar prova real humana do endpoint em modo `local` com `Qwen3.6-35B-A3B-MTP-Q8.gguf`;
- implementar e provar a camada humana de entrada/saida;
- implementar e provar o `StudyPackage`;
- implementar e provar criacao/exportacao opcional de Student Vault novo;
- registrar status HTTP, tempo aproximado, modelo usado e avaliacao humana das cinco entregas;
- revisar `git status`/`git diff` imediatamente antes do commit de fechamento;
- realizar commit de fechamento da E03 antes de iniciar E04/E05.
