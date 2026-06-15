# Mindvox

Mindvox e uma API em FastAPI para transformar aulas gravadas em memoria consultavel.

O projeto recebe arquivos de audio, transcreve o conteudo, processa a transcricao e organiza os dados para consulta posterior por tema, aula, disciplina, sessao ou busca semantica.

## Problema

Aulas longas podem ter varias horas de duracao e normalmente sao divididas em sessoes. Depois da aula, encontrar uma informacao especifica no video ou no audio bruto e lento e pouco pratico.

O Mindvox resolve esse problema criando um fluxo de memoria consultavel a partir do audio ja gravado:

```text
arquivo de audio
  -> envio para a API
  -> transcricao
  -> processamento da transcricao
  -> armazenamento estruturado
  -> busca semantica ou relacional
```

A captura do audio nao faz parte da API. O Mindvox comeca seu trabalho a partir de um arquivo de audio ja existente.

## Escopo do MVP

O MVP esta organizado em tres servicos principais:

1. Transcricao de audio para texto.
2. Processamento de transcricoes para producao de material didatico organizado.
3. Ingestao e consulta futura da memoria por busca semantica e por filtros relacionais.

STT significa Speech-to-Text: transformacao de fala em texto.

## Memoria

A memoria do Mindvox sera isolada em um espaco proprio chamado nano-space. O nano-space canonico do projeto e:

```text
projeto_mindvox
```

Esse isolamento evita misturar conteudos de origens ou projetos diferentes.

## Endpoints Planejados

Os endpoints abaixo representam o alvo do MVP e podem ser ajustados durante a implementacao.

```text
GET /health
```

Verifica se a API esta rodando.

```text
POST /transcriptions/v1.0.0
```

Recebe um arquivo de audio e devolve uma transcricao.

```text
POST /processed-transcriptions/v1.0.0
```

Recebe audio ou transcricao bruta e devolve material de estudo com cinco entregas: bruto auditavel, texto didatico, temas, termos tecnicos e tecnologias citadas.

```text
GET /search/semantic/v1?q=consulta
```

Busca informacoes por sentido aproximado.

```text
GET /search/relational/v1
```

Busca informacoes por campos estruturados, como curso, disciplina, aula, sessao, data ou tema.

## Fora do MVP

Os itens abaixo nao fazem parte da primeira versao:

- TTS;
- resposta falada em streaming;
- speech-to-speech;
- interface grafica;
- captura de audio ao vivo dentro da API;
- dependencia obrigatoria de servicos internos de outros projetos.

## API First

O Mindvox segue uma abordagem API First. Isso significa que os endpoints, os dados de entrada, as respostas, os erros e a documentacao automatica sao parte central do projeto.

A API deve demonstrar:

- validacao de dados;
- tratamento de erros;
- logs;
- seguranca basica;
- versionamento de endpoints;
- documentacao automatica do FastAPI;
- execucao em outro computador.

## Estado Atual

O projeto esta em desenvolvimento inicial, com os primeiros endpoints implementados:

```text
GET /health
POST /transcriptions/v1.0.0
```

O endpoint de transcricao ja possui contrato HTTP, autenticacao por token, validacoes, schema de resposta, documentacao FastAPI, testes automatizados e prova real humana com STT.

A E03 esta especificada para pos-processamento de alto nivel em `POST /processed-transcriptions/v1.0.0`. O motor local preferencial selecionado por benchmark real e `Qwen3.6-35B-A3B-MTP-Q8.gguf`, executado via `llama.cpp`/`llama-server` em modo compativel com OpenAI.

Para transcricoes longas, a E03 usa no perfil local de desenvolvimento um
pipeline interno de alta fidelidade:

```text
transcricao bruta
  -> pre-auditoria lexical
  -> chunking TF-IDF em memoria
  -> processamento chunk por chunk
  -> merge canonico deterministico
  -> auditoria final dos campos semanticos
```

Esse pipeline preserva `raw_text` original na resposta publica. O texto saneado
pela pre-auditoria e usado apenas internamente para reduzir ruido lexical antes
do Qwen. No perfil `dev`, iniciado por `fastapi dev`, esse pipeline ja fica
ativo por padrao. A configuracao equivalente e:

No fluxo chunked, cada chunk recebe prompt e validacao estrutural proprios, mas
nao recebe a regua monolitica completa de cobertura semantica. Essa regua dura
fica reservada ao resultado mesclado final. A pre-auditoria tambem remove, no
texto interno enviado ao LLM, ruido repetitivo de STT como sequencias longas de
tokens sem conteudo, mantendo o `raw_text` original intacto para auditoria.

```env
MINDVOX_POSTPROCESSING_CHUNKING_MODE=tfidf
MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS=20000
MINDVOX_POSTPROCESSING_CHUNK_TARGET_TOKENS=5000
MINDVOX_POSTPROCESSING_PRE_AUDIT_ENABLED=true
MINDVOX_POSTPROCESSING_FINAL_AUDIT_ENABLED=true
```

Com `MINDVOX_POSTPROCESSING_CHUNKING_MODE=off`, a E03 volta ao fluxo anterior
de chamada unica ao motor textual, util apenas para diagnostico comparativo.

Quando uma transcricao for copiada diretamente do site da UFG para o Vault
`UFG_Pos_2`, prepare o `.txt` para a E03 com:

```bash
cd /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox && uv run python /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/scripts/prepare_e03_raw_text_from_vault.py --section 3
```

O script le os metadados do frontmatter da inbox (`disciplina`, `professor`,
`aula`, `data` e `sessao-ativa`) e usa esses dados no nome do arquivo preparado.
O `.txt` sera salvo em `inputs/e03_raw_texts/`. Essa pasta fica fora do Git e
serve como bandeja local de transcricoes prontas para anexar em `raw_text_file`
no Swagger da E03.

Ao lado do `.txt`, o script tambem gera um `.metadata.json` com os campos do
formulario E03 ja normalizados: `course`, `discipline`, `class_date`,
`class_title`, `session_label`, `language`, `processing_profile` e `input_type`.
Esse JSON funciona como fonte de preenchimento do formulario.

Para o modo aprendiz/desenvolvedor local, preencha visualmente a tela do Swagger
sem clicar em `Execute`:

```bash
cd /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox && uv run python /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/scripts/fill_e03_swagger_from_vault.py --section 3
```

Esse comando abre uma janela Chromium controlada pelo Playwright, autoriza com
`dev-token` em modo dev, clica em `Try it out`, seleciona `raw_text_file`, anexa
o `.txt` preparado e preenche os metadados na tela HTTP. Ele para antes do
`Execute`, para que o aprendiz veja e confira tudo antes do processamento.

Como alternativa auxiliar, para apenas copiar os campos preparados para a area de
transferencia:

```bash
cd /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox && uv run python /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/scripts/prepare_e03_raw_text_from_vault.py --section 3 --copy-swagger-fields
```

Para evitar a tela do Swagger e chamar o mesmo endpoint diretamente, submeta o
`.metadata.json`:

```bash
cd /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox && uv run python /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/scripts/submit_e03_raw_text.py /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/inputs/e03_raw_texts/2026-05-09-api-rogerio-aula-1-sessao-4.metadata.json
```

Ou prepare e submeta diretamente em um unico comando:

```bash
cd /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox && uv run python /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox/scripts/prepare_e03_raw_text_from_vault.py --section 4 --submit
```

O Swagger e o endpoint continuam sendo o contrato publico para usuarios externos.
O script local e apenas um cliente da API que usa os campos do formulario a
partir do `.metadata.json`. Quando um arquivo `.txt` preparado pelo Mindvox tem
nome como `2026-05-09-api-rogerio-aula-1-sessao-4.txt`, o backend usa esse nome
apenas para preencher metadados ausentes. Se o usuario informar `class_date`,
`discipline`, `class_title` ou `session_label` no formulario, esses valores
explicitos prevalecem; diferencas em relacao ao nome preparado sao registradas em
log para auditoria, mas nao bloqueiam a requisicao.

## Como Executar

Entre na pasta do projeto:

```bash
cd /caminho/para/Mindvox
```

Instale as dependencias:

```bash
uv sync
```

Rode a API em modo de desenvolvimento:

```bash
uv run fastapi dev src/main.py
```

Esse comando usa os defaults locais do MVP: `MINDVOX_PUBLIC_DEPLOYMENT=false`,
`MINDVOX_TRANSCRIPTION_MODE=real`, `MINDVOX_POSTPROCESSING_MODE=auto` e token
didatico local `dev-token` quando `MINDVOX_API_TOKEN` nao estiver definido.
Como entrada principal `main`, esse perfil normaliza o modo local para `dev` e
nao reaproveita acidentalmente modo `contract` herdado de teste anterior.

Se o terminal ja estiver dentro da pasta `src` e o ambiente virtual estiver ativo,
o comando curto tambem e valido:

```bash
fastapi dev
```

Depois acesse a documentacao automatica:

```text
http://127.0.0.1:8000/docs
```

No topo do Swagger, o campo de descricao da API informa o perfil ativo:
`Active startup profile: dev`, `contract` ou `prod`.

## Requisitos Para Transcricao Real

O endpoint `POST /transcriptions/v1.0.0` pode rodar em dois modos:

- `contract`: modo rapido de contrato, usado para testes da API sem STT real;
- `real`: modo real de transcricao, usando `mlx-whisper`.

Para o modo real da E02, o motor definido e:

```text
mlx-whisper + mlx-community/whisper-large-v3-turbo-fp16
```

Esse motor foi escolhido para privilegiar qualidade de transcricao em aulas longas. Ele usa MLX, tecnologia otimizada para Apple Silicon. Portanto, para executar a transcricao real do endpoint `POST /transcriptions/v1.0.0` de forma adequada, a maquina deve ter:

- macOS em Apple Silicon, como M1, M2, M3 ou superior;
- espaco em disco para o modelo local;
- internet no primeiro uso, caso o modelo ainda nao esteja baixado;
- dependencias de STT instaladas com o extra `stt`.

Capacidade minima esperada:

| Uso | Hardware esperado |
| --- | --- |
| Rodar API, `/health`, Swagger e modo `contract` | Computador capaz de rodar Python/FastAPI e `uv`; nao exige MLX nem modelo local |
| Rodar transcricao real em `POST /transcriptions/v1.0.0` | Mac com Apple Silicon, 16 GB de memoria unificada recomendados para aulas longas, e pelo menos 10 GB livres em disco para dependencias, cache do modelo e arquivos temporarios |

Observacoes:

- maquinas com 8 GB de memoria podem ate executar testes curtos, mas nao sao a referencia adequada para aulas longas;
- o modelo `mlx-community/whisper-large-v3-turbo-fp16` ocupou cerca de `1.5 GB` no cache local observado, mas o espaco livre recomendado deve ser maior por causa de dependencias, cache do Hugging Face, adaptacoes locais e arquivos temporarios;
- Windows, Linux, Mac Intel ou maquinas sem MLX compativel podem rodar o contrato da API, mas nao sao o alvo do modo real de STT do endpoint `POST /transcriptions/v1.0.0`;
- se a maquina nao atender aos requisitos do modo real, o endpoint deve falhar de forma controlada, sem trocar automaticamente para outro modelo.
- esta capacidade minima cobre apenas o endpoint `POST /transcriptions/v1.0.0`; os requisitos do app completo podem aumentar quando os endpoints futuros de processamento, memoria e busca forem implementados.

Instale as dependencias do modo real com:

```bash
uv sync --extra stt
```

Depois rode a API em modo real:

```bash
uv run fastapi dev src/main.py
```

Esse e o modo real local padrao. Ele executa STT real, resolve
`MINDVOX_POSTPROCESSING_MODE=auto` como `local` e tenta iniciar automaticamente o
`llama-server` para a E03 quando o pos-processamento real for acionado.

Observacao sobre cache:

- aqui, `cache` nao significa memoria RAM;
- significa uma pasta local em disco onde arquivos baixados ficam guardados;
- se o modelo ja estiver no cache local, o Mindvox usa esses arquivos sem baixar tudo novamente;
- se o modelo ainda nao existir na maquina, o app busca o modelo no Hugging Face no primeiro uso;
- depois do primeiro download, chamadas futuras tendem a carregar o modelo localmente.

Em outra maquina, o mesmo fluxo se aplica: instalar dependencias, iniciar o app em modo real e permitir que o modelo seja baixado do Hugging Face no primeiro uso. Se a maquina nao tiver hardware compativel ou o motor real nao estiver instalado, o endpoint deve retornar erro controlado de indisponibilidade do servico.

Se o terminal ja estiver dentro da pasta `src`, use `fastapi dev` ou
`fastapi dev main.py`. Se estiver na raiz do projeto, use
`uv run fastapi dev src/main.py`.

## Artefatos Locais de Transcricao

Sempre que o STT produzir uma transcricao bruta, o Mindvox salva automaticamente dois arquivos locais em pastas separadas:

```text
outputs/transcriptions/[class-date-title-session_]<transcription_id>.json
outputs/human/transcriptions/[class-date-title-session_]<transcription_id>.txt
```

O `.txt` em `outputs/human/transcriptions/` e o arquivo humano principal da E02: e ali que o usuario tecnico local encontra o texto bruto transcrito para ler, copiar ou reenviar ao E03.

Quando `class_date`, `class_title`, `session_label` ou metadado equivalente forem enviados, o Mindvox usa esses dados como prefixo seguro do nome do arquivo. Isso facilita localizar a aula no filesystem local. O sufixo tecnico continua sendo o `transcription_id`, que permanece opaco e obrigatorio para rastreabilidade. O conteudo do `.txt` continua sendo somente a transcricao bruta, sem titulo artificial, mas e paragrafado quando houver segmentos do STT para evitar uma linha unica ilegivel.

Isso ocorre quando:

- `POST /transcriptions/v1.0.0` transcreve um audio diretamente;
- `POST /processed-transcriptions/v1.0.0` recebe `input_type=audio` e chama internamente o servico de STT antes do pos-processamento.

O arquivo `.json` em `outputs/transcriptions/` contem a resposta estruturada da transcricao bruta para uso tecnico, auditoria e integracoes, incluindo segmentos e timestamps quando o STT os fornecer. O arquivo `.txt` em `outputs/human/transcriptions/` contem somente o texto bruto paragrafado para leitura humana e reprocessamento posterior em `input_type=raw_text` com `raw_text_file`.

Os metadados de curso, disciplina, data, titulo da aula e sessao aparecem no JSON tecnico, ajudam o E03 a entender o contexto da aula e serao importantes para o E04 organizar memoria, filtros e buscas. No modo `dev`, eles tambem tornam o nome do arquivo humano mais legivel.

Na resposta do Swagger, o campo `artifact_locations` indica onde procurar:

- `human_text_path`: caminho relativo do arquivo humano `.txt`;
- `technical_json_path`: caminho relativo do JSON tecnico.

Para reprocessar esse `.txt` no Swagger da E03, use `input_type=raw_text` ou,
por tolerancia ergonomica da tela, `input_type=raw_text_file`; anexe o arquivo
em `raw_text_file`, deixe `audio_file` vazio e deixe `raw_text` vazio. Os
campos textuais opcionais da documentacao interativa devem nascer vazios; se
um cliente antigo ou tela cacheada ainda enviar o literal `string` em campo
opcional, o backend trata esse valor como ausente para evitar erro artificial.
No Swagger, `input_type` e publicado como `Enum`, entao a interface deve mostrar
uma lista de selecao/dropdown com as opcoes permitidas.

A pasta padrao e configuravel por:

```text
MINDVOX_TRANSCRIPTION_OUTPUT_DIR=outputs/transcriptions
MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR=outputs/human/transcriptions
```

Quando o valor for relativo, ele e resolvido a partir da raiz do projeto, mesmo que o servidor tenha sido iniciado de dentro de `src`. A pasta `outputs/` fica fora do Git, porque pode conter transcricoes reais e dados sensiveis de aula.

## Artefatos Locais e Fila da E03

Sempre que o E03 gerar uma resposta processada, o Mindvox salva automaticamente dois artefatos:

```text
outputs/processed_transcriptions/[class-date-title-session_]<processed_transcription_id>.json
outputs/human/processed_transcriptions/[class-date-title-session_]<processed_transcription_id>.md
```

O `.md` em `outputs/human/processed_transcriptions/` e o arquivo humano principal da E03: e ali que o usuario tecnico local encontra o texto processado para ler, copiar ou estudar. O `.json` em `outputs/processed_transcriptions/` e o contrato tecnico da API, proprio para o E04 e para integracoes.

Quando metadados de aula forem enviados, o Markdown humano tambem recebe titulo legivel com data, aula e sessao, alem de uma pequena secao de metadados. Isso nao substitui o JSON tecnico: apenas torna o arquivo de estudo mais facil de reconhecer e usar.

Na resposta do Swagger, o campo `artifact_locations` indica:

- `human_text_path`: caminho relativo do Markdown humano `.md`;
- `technical_json_path`: caminho relativo do JSON tecnico.

Quando o LLM devolve JSON estruturalmente valido, mas a auditoria de cobertura
semantica reprova a saida por parecer resumo excessivo ou por omitir conteudo
protegido, a E03 nao descarta silenciosamente esse material. A saida rejeitada
entra em quarentena para auditoria humana:

```text
outputs/processed_transcriptions/rejected/[class-date-title-session_]<job-or-manual-id>_rejected_attempt-N.json
outputs/human/processed_transcriptions/rejected/[class-date-title-session_]<job-or-manual-id>_rejected_attempt-N.md
```

O JSON rejeitado contem status, erro, tentativa, metricas, excerto do bruto,
`runtime_snapshot` e a saida do LLM que foi recusada. Esse snapshot registra
modo de chunking, quantidade de chunks, limite de tokens de saida, modelo e
regua semantica aplicada naquela execucao. O Markdown humano explica a rejeicao
e mostra o texto didatico rejeitado para conferencia. Nesse caso, o endpoint
retorna `502` com `error_code=postprocessing_quality_rejected` e caminhos dos
artefatos rejeitados, em vez de um `500` generico.

Essa estrategia de pastas e propria do modo `dev` e da instalacao local, em que o usuario tecnico tem acesso ao projeto e ao disco da maquina. Em producao publica, o usuario final normalmente nao tem acesso ao filesystem do servidor. Nesse caso, a evolucao correta e oferecer download direto pela API ou pela interface, permitindo formatos como Markdown, TXT, PDF ou outros formatos de exportacao. PDF fica tratado como formato futuro de entrega publica, nao como requisito obrigatorio do MVP local.

Quando `POST /processed-transcriptions/v1.0.0` recebe `input_type=audio`, ele primeiro gera uma transcricao bruta por STT. Essa transcricao entra em uma fila local antes do pos-processamento:

```text
outputs/processed_transcriptions/queue/pending/<transcription_id>.json
outputs/processed_transcriptions/queue/completed/<transcription_id>.json
outputs/processed_transcriptions/queue/failed/<transcription_id>.<error_type>.json
```

Se o pos-processamento der certo, o item sai de `pending` e vai para `completed`. Se o motor LLM estiver temporariamente indisponivel, o item permanece em `pending` e o app tenta reprocessar automaticamente quando estiver rodando em modo real com motor disponivel. Se a falha atingir `MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS`, o item sai de `pending` e vai para `failed`, encerrando o custo oculto de retry. Assim, o usuario nao precisa selecionar de novo o audio nem procurar manualmente onde ficou o bruto, e tambem consegue ver quando uma falha foi encerrada.

Configuracoes:

```text
MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR=outputs/processed_transcriptions
MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR=outputs/human/processed_transcriptions
MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_OUTPUT_DIR=outputs/processed_transcriptions/rejected
MINDVOX_PROCESSED_TRANSCRIPTION_REJECTED_MARKDOWN_OUTPUT_DIR=outputs/human/processed_transcriptions/rejected
MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_ENABLED=true
MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS=60
MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_MAX_ATTEMPTS=3
```

Esses arquivos podem conter conteudo real de aula e permanecem fora do Git.

## Modelo Local Preferencial da E03

A E03 tem como objetivo transformar a transcricao bruta de uma aula em material semanticamente organizado.

No teste real feito com a transcricao bruta da E02 (`42.998` caracteres), o melhor candidato local foi:

```text
Qwen3.6-35B-A3B-MTP-Q8.gguf
```

Resumo do benchmark:

| Modelo | Tempo total | Temas | Termos tecnicos | Resultado |
| --- | ---: | ---: | ---: | --- |
| Gemma 4 12B Q8 | `77,26s` | `4` | `8` | passou, mas perdeu para o Qwen 35B-A3B |
| Qwen 3.6 27B Q8 | `188,46s` | `5` | `8` | passou, mas foi lento na geracao |
| Qwen 3.6 35B-A3B Q8 | `55,83s` | `6` | `10` | melhor resultado local |

Decisao atual:

- `Qwen3.6-35B-A3B-MTP-Q8.gguf` e o modelo local preferencial da E03;
- o modelo deve continuar configuravel por variaveis de ambiente;
- o contrato HTTP da E03 nao deve depender de um path local fixo;
- providers externos OpenAI-compatible continuam previstos para portabilidade.

Requisitos operacionais observados para esse modelo:

- arquivo GGUF local com cerca de `37 GB`;
- uso observado pelo `llama.cpp` em torno de `38 GB` de memoria no teste local com o modelo carregado;
- janela maxima declarada pelo GGUF local: `262144` tokens;
- configuracao padrao local da E03: entrada textual ate `150000` caracteres, contexto `65536`, saida maxima `20000` tokens, timeout `1200s` e `1` slot de servidor;
- essa configuracao foi definida a partir de transcricao real de `78,88` minutos, projetada para aula de `120` minutos com margem de densidade semantica;
- recomendacao prudente: Mac Apple Silicon com memoria unificada alta, preferencialmente `96 GB` ou mais para demonstracao confortavel;
- o Mac M4 Max com `128 GB` de memoria unificada e largura de banda informada de `546 GB/s` atende com folga ao uso local demonstrado;
- pelo menos `50 GB` livres em disco para o modelo, caches e arquivos auxiliares.

Em maquinas sem capacidade para o modelo local, a E03 deve poder usar modo `provider` com API OpenAI-compatible ou modo `contract` para testes automatizados do contrato.

Privacidade dos modos da E03:

- em modo `auto`, que e o padrao, o Mindvox atrela os modos: `MINDVOX_TRANSCRIPTION_MODE=contract` faz a E03 usar `contract`; `MINDVOX_TRANSCRIPTION_MODE=real` faz a E03 usar `local`;
- em modo `local`, o app tenta iniciar automaticamente um servidor local compativel com OpenAI, como `llama-server`;
- em modo `local`, o cliente envia `chat_template_kwargs.enable_thinking=false` ao `llama-server`, para que modelos Qwen entreguem o JSON final em vez de consumir a saida apenas com `reasoning_content`;
- em modo `provider`, o `raw_text` enviado pelo usuario ou a transcricao gerada a partir do audio sera enviado ao provedor externo configurado;
- em modo `contract`, o endpoint valida o contrato HTTP sem fazer pos-processamento real por LLM;
- use modo `local` quando o conteudo da aula nao puder sair da maquina;
- nunca coloque chave real de provider no Git, no README, em testes, em logs ou no corpo da requisicao Swagger.

## Saidas Processadas da E03

A E03 nao deve produzir, por padrao, uma segunda transcricao quase integral.
Ela tambem nao deve produzir resumo curto. A finalidade correta e retirar
somente redundancia semantica e ruido de fala, preservando projetos, cases,
contribuicoes relevantes dos alunos, exemplos, metaforas, tecnologias e dores
reais de implementacao que acrescentem conteudo novo.

Motivo:

- aulas longas possuem muita redundancia semantica;
- a E02 ja preserva a transcricao bruta como lastro fiel do que foi ouvido;
- uma versao quase integral processada teve tamanho praticamente igual ao bruto (`42.892` caracteres contra `42.998`) e custou mais tempo;
- a versao pos-processada deve preservar os nucleos semanticos da aula e remover apenas redundancia semantica, ruido de fala e repeticoes sem informacao nova.

Assim, a E03 deve priorizar:

- `raw_text`, para rastreabilidade e conferencia;
- `didactic_text`, como texto discursivo, sequencial, logico e didatico, com redundancia semantica reduzida sem perda deliberada de conteudo;
- `themes`, como mapa tematico estruturado para estudo e futura ingestao pela E04;
- `technical_terms`, para normalizacao de termos tecnicos;
- `technology_mentions`, para listar tecnologias, ferramentas, frameworks, plataformas, bibliotecas, servicos, APIs e providers citados em aula.

Campo auxiliar:

- `processing_notes`, para registrar correcoes, incertezas e cuidados do processamento.

Se houver duvida sobre perda ou distorcao, o usuario deve conferir a saida processada contra a transcricao bruta preservada pela E02.

Nota sobre consumo humano:

- o contrato principal da API continua sendo JSON, porque ele sera consumido pela E04;
- o texto de leitura humana ja aparece em `didactic_text`;
- para ergonomia de uso direto no modo `dev`, a E03 salva automaticamente um artefato humano em Markdown (`.md`) em `outputs/human/processed_transcriptions/`, pois preserva titulos, listas e secoes, abre no Obsidian e pode ser convertido para PDF depois;
- em producao publica, esse arquivo local deve ser substituido ou complementado por um endpoint/interface de download, pois o usuario final nao acessa a pasta do servidor;
- PDF nao e o formato padrao do MVP porque aumenta dependencias e escopo operacional.

Nota sobre saida do LLM:

- o Mindvox exige JSON estruturado para que o E04 consiga ler a resposta;
- se o LLM devolver uma resposta quase correta, com aliases previsiveis ou valores em portugues como `alta`, `media`, `baixa` ou `ferramenta`, o backend normaliza para o contrato publico;
- se faltar o texto didatico principal ou o JSON for irrecuperavel, o endpoint rejeita a saida com erro controlado, sem expor a resposta integral do LLM;
- para transcricoes longas, se a resposta estiver tecnicamente em JSON correto, mas parecer resumo excessivamente curto ou pobre em temas, o backend rejeita a primeira saida, tenta uma segunda geracao com instrucao mais rigorosa de preservacao semantica e, se ainda assim houver falha, retorna erro controlado em vez de entregar produto ruim.

## Verificacoes Uteis

Verificar a sintaxe de um arquivo Python especifico:

```bash
uv run python -m py_compile src/main.py
```

Verificar a sintaxe dos arquivos Python do projeto:

```bash
uv run python -m compileall .
```

O ponto final no comando acima significa: verificar a pasta atual e suas subpastas.

## Variaveis de Ambiente

O arquivo `.env.example` documenta as variaveis esperadas pelo projeto.

O arquivo `.env` e local e nao deve ser enviado ao GitHub, pois pode conter chaves, tokens ou configuracoes privadas.

Variaveis usadas pela E02:

```text
MINDVOX_API_TOKEN
MINDVOX_MAX_UPLOAD_MB
MINDVOX_TRANSCRIPTION_MODE
MINDVOX_TRANSCRIPTION_MODEL
MINDVOX_TRANSCRIPTION_OUTPUT_DIR
MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR
```

Variaveis gerais de endurecimento operacional:

```text
MINDVOX_PUBLIC_DEPLOYMENT
MINDVOX_ENABLE_DOCS
MINDVOX_TRUSTED_HOSTS
MINDVOX_RUNTIME_PROFILE
```

Variaveis usadas pela E03:

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
MINDVOX_LLAMA_SERVER_STARTUP_TIMEOUT_SECONDS
MINDVOX_PROCESSED_TRANSCRIPTION_OUTPUT_DIR
MINDVOX_PROCESSED_TRANSCRIPTION_MARKDOWN_OUTPUT_DIR
MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_ENABLED
MINDVOX_PROCESSED_TRANSCRIPTION_QUEUE_RETRY_SECONDS
```

`MINDVOX_API_TOKEN` deve ser definido no `.env` local ou no ambiente da instalacao
quando se quiser substituir o token didatico. Em desenvolvimento local
(`MINDVOX_PUBLIC_DEPLOYMENT=false`), valor ausente ou vazio usa automaticamente o
token didatico `dev-token`. Placeholder de exemplo, como
`replace-with-local-token` ou `<set-real-token-only-in-local-env>`, continua sendo
tratado como token ausente. O token `dev-token` nao deve ser usado em exposicao
publica.

Quando `MINDVOX_PUBLIC_DEPLOYMENT=true`, a aplicacao trata `dev-token` como token ausente. Isso evita que o token didatico usado em aula ou testes locais autentique `POST /transcriptions/v1.0.0` ou `POST /processed-transcriptions/v1.0.0` em instalacao exposta.

Nota didatica sobre geracao e guarda do token:

- o Mindvox nao gera tokens de usuarios nesta versao do MVP;
- o token Bearer e uma senha tecnica da instalacao, criada fora do codigo por quem instala e administra o sistema;
- essa pessoa ou equipe administradora e chamada aqui de operador da instalacao;
- a AWS, quando usada, nao e o operador: ela e a infraestrutura onde o app roda e oferece servicos seguros para guardar segredos;
- em nuvem, o token deve ser guardado em mecanismo seguro do ambiente, como AWS Secrets Manager, AWS Systems Manager Parameter Store, secret do servico de deploy ou solucao equivalente;
- o app apenas le esse valor pelo ambiente em `MINDVOX_API_TOKEN` e compara com o valor enviado no header `Authorization: Bearer <token>`;
- para um produto futuro multiusuario, com clientes diferentes, emissao e revogacao de chaves, login, permissoes e auditoria por usuario, a arquitetura deve evoluir para Cognito, Keycloak, OAuth2/JWT, API Gateway com API keys/usage plans ou mecanismo equivalente.

Exemplo local para gerar um token forte de instalacao:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Os metadados opcionais de aula tambem possuem limite para evitar abuso de memoria, prompt e custo: `course` ate `160` caracteres, `discipline` ate `120` caracteres e `class_title` ate `200` caracteres.

Modo padrao coerente:

- `MINDVOX_POSTPROCESSING_MODE=auto` e o padrao recomendado;
- no perfil `contract` explicito, a E03 tambem usa `contract`;
- com `MINDVOX_TRANSCRIPTION_MODE=real`, a E03 usa `local`, portanto tenta iniciar automaticamente o `llama-server` local antes de aceitar processamento real;
- para uso local padrao, nao e preciso declarar `MINDVOX_TRANSCRIPTION_MODE`,
  `MINDVOX_POSTPROCESSING_MODE` nem `MINDVOX_API_TOKEN` no comando;
- `MINDVOX_RUNTIME_PROFILE` normalmente e inferido ou definido pelos perfis
  `main`, `contract` e `prod`; o valor aparece no Swagger como
  `Active startup profile`;
- para usar provider externo, defina explicitamente `MINDVOX_POSTPROCESSING_MODE=provider` e configure a chave em ambiente seguro.

Exemplo de configuracao local da E03 com autostart do `llama-server`:

```bash
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

Com `MINDVOX_LOCAL_LLM_AUTOSTART=true`, o app tenta localizar `llama-server` no `PATH` ou no caminho local padrao `~/Desenvolvedor/llama.cpp/build/bin/llama-server`. Tambem tenta localizar o modelo local preferencial em `~/Models/Qwen3.6-35B-A3B-MTP-Q8.gguf`, salvo quando `MINDVOX_LOCAL_LLM_MODEL_PATH` aponta para outro arquivo GGUF.

`MINDVOX_LLAMA_SERVER_PARALLEL=1` e intencional no modo local padrao: a E03 foi desenhada para uma chamada longa de pos-processamento por vez, preservando memoria e contexto para qualidade de saida em vez de abrir multiplos slots concorrentes.

No modo `local`, o cliente OpenAI-compatible do Mindvox desliga o modo thinking do `llama-server` com `chat_template_kwargs.enable_thinking=false`. Isso e necessario para modelos Qwen que podem devolver raciocinio em `reasoning_content` e deixar `content` vazio; a E03 precisa de JSON final limpo em `content`.

Se o app estiver em modo real/local e nao conseguir encontrar o binario, encontrar o modelo, iniciar o processo ou verificar que o servidor ficou pronto em `/v1/models`, a inicializacao falha com mensagem clara no terminal. Isso e intencional: o Mindvox nao deve seguir funcionando com erro silencioso de LLM.

Exemplo de configuracao da E03 com provider externo OpenAI-compatible:

```bash
MINDVOX_POSTPROCESSING_MODE=provider
MINDVOX_LLM_PROVIDER=groq
MINDVOX_LLM_BASE_URL=https://api.groq.com/openai/v1
MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS=api.groq.com
MINDVOX_LLM_MODEL=llama-3.3-70b-versatile
MINDVOX_LLM_API_KEY=<set-real-key-only-in-local-env>
MINDVOX_LLM_MAX_OUTPUT_TOKENS=20000
```

No modo `provider`, o conteudo bruto enviado para pos-processamento deixa a maquina local e e transmitido ao provider configurado. Essa opcao deve ser usada somente quando isso for aceitavel para o contexto do audio ou da transcricao.

`MINDVOX_LLM_API_KEY` deve ser definido somente no `.env` local da instalacao. Valor vazio ou placeholder de exemplo, como `replace-with-provider-key` ou `<set-real-key-only-in-local-env>`, deve ser tratado pela aplicacao como chave ausente.

`MINDVOX_LLM_MAX_OUTPUT_TOKENS` limita a quantidade maxima de tokens que a E03 solicita ao motor LLM. A aplicacao tambem limita o tamanho da resposta lida do provider ou servidor local, evitando respostas excessivas, custo inesperado e consumo indevido de memoria.

Por seguranca operacional, modo `provider` deve usar URL externa `https` e nao deve apontar para `localhost` ou rede privada. A aplicacao tambem rejeita hostname de provider que resolva para IP local/privado, evitando falsa aparencia de endpoint externo. Em exposicao publica, configure `MINDVOX_LLM_ALLOWED_PROVIDER_HOSTS` para allowlist do provider esperado, por exemplo `api.groq.com`; assim, host fora da allowlist e rejeitado antes da chamada LLM. Modo `local` deve apontar para `localhost`, IP local/privado ou host local equivalente, como `host.docker.internal`.

Uploads de audio sao lidos com limite incremental. Isso evita que um arquivo acima de `MINDVOX_MAX_UPLOAD_MB` precise ser carregado inteiro em memoria antes de ser rejeitado.

O nome de provider exposto em `processing_engine.name` e sanitizado quando a configuracao contem marcador sensivel, como `secret` ou `token`.

Para execucao publica, configure tambem:

```bash
MINDVOX_PUBLIC_DEPLOYMENT=true
MINDVOX_ENABLE_DOCS=false
MINDVOX_TRUSTED_HOSTS=api.seu-dominio.example
```

Quando `MINDVOX_PUBLIC_DEPLOYMENT=true`, a aplicacao nao sobe sem `MINDVOX_TRUSTED_HOSTS`. A documentacao interativa (`/docs`, `/redoc`, `/openapi.json`) fica desabilitada por padrao, salvo configuracao expressa em contrario. Rate limiting, TLS e limite maximo de corpo no proxy continuam sendo responsabilidades do deploy de producao.

Ainda em `MINDVOX_PUBLIC_DEPLOYMENT=true`, `MINDVOX_TRUSTED_HOSTS=*` e recusado, porque wildcard remove a protecao contra Host header indevido. Configure hostnames reais, por exemplo `api.seu-dominio.example`.

Os endpoints de negocio protegidos, `POST /transcriptions/v1.0.0` e `POST /processed-transcriptions/v1.0.0`, exigem transporte seguro em modo publico. A requisicao deve chegar a aplicacao com `request.url.scheme == "https"`. Se TLS terminar em proxy, o proxy e o servidor ASGI devem ser configurados de modo confiavel para repassar esse scheme; nao basta aceitar um header `X-Forwarded-Proto` enviado livremente pelo cliente. Essa checagem e defesa em profundidade: em producao real, TLS, limite de corpo, rate limiting e bloqueio de acesso direto ao processo Uvicorn devem ser aplicados no ALB, API Gateway, Nginx ou camada equivalente.

Em producao publica, a documentacao interativa (`/docs`, `/redoc`, `/openapi.json`) deve permanecer desabilitada ou ser protegida por uma camada externa. Swagger/OpenAPI revela o mapa tecnico da API: rotas, metodos, schemas, campos, erros e forma de autenticacao. Isso e desejavel em desenvolvimento e demonstracao local, mas aumenta a superficie de reconhecimento para terceiros em uma API exposta na internet.

Camadas externas possiveis para proteger a documentacao e a borda publica:

| Camada | Papel |
| --- | --- |
| VPN | Restringe acesso a quem estiver conectado a uma rede privada autorizada. |
| API Gateway | Recebe requisicoes publicas, aplica autenticacao, limites, logs e regras antes de encaminhar ao app. |
| Cognito | Servico AWS para login, usuarios, tokens, permissoes e integracao com APIs. |
| Keycloak | Plataforma IAM open-source para login, SSO, OAuth2/OpenID Connect, SAML, 2FA e permissoes. |
| Cloudflare Access | Exige login autorizado antes de liberar acesso a paginas ou APIs internas. |
| Basic Auth no proxy | Usuario e senha simples configurados em Nginx, Caddy ou proxy equivalente para proteger rotas como `/docs`. |
| Painel interno | Area administrativa separada, acessivel somente por operadores autorizados. |
| ALB - Application Load Balancer | Balanceador AWS que recebe trafego externo, aplica HTTPS, regras de rota e pode integrar autenticacao. |
| CloudFront + WAF | Proxy/CDN global com firewall de aplicacao para bloquear padroes suspeitos antes do app. |

Essas camadas nao substituem a autenticacao Bearer, validacoes, limites e logs do Mindvox. Elas reduzem exposicao publica e protegem a documentacao interativa quando houver necessidade real de mante-la acessivel fora do ambiente local.

Para testar o contrato HTTP da transcricao sem depender do motor real de STT, use:

```bash
uv run fastapi dev src/contract
```

Para testar o contrato HTTP da E03 sem depender de LLM real, use:

```bash
uv run fastapi dev src/contract
```

Se o terminal ja estiver dentro da pasta `src`, o comando equivalente e:

```bash
fastapi dev contract
```

Mesmo em `contract`, os endpoints protegidos continuam exigindo Bearer token. No
Swagger, clique em `Authorize` e informe `dev-token`. A diferenca e que o token
local ja vem da logica do app; nao precisa aparecer no comando.

Para testar E02 e E03 em modo real local, use:

```bash
uv run fastapi dev src/main.py
```

Nesse modo, o app usa STT real e tenta iniciar automaticamente o LLM local para o pos-processamento.
Tambem ativa o pipeline longo da E03 por padrao para transcricoes acima do limite
minimo configurado por `MINDVOX_POSTPROCESSING_CHUNKING_MIN_CHARS`.

Para simular o perfil de producao publica, use o perfil `prod` somente depois de
definir token forte, hosts confiaveis e segredos de provider no ambiente seguro da
instalacao. Exemplo de forma do comando:

```bash
uv run fastapi run src/prod
```

Dentro da pasta `src`, a forma equivalente e `fastapi run prod`. Esse perfil liga
`MINDVOX_PUBLIC_DEPLOYMENT=true`, desabilita docs por padrao, bloqueia
`dev-token`, exige `MINDVOX_TRUSTED_HOSTS` e nao inicia Llama local.
