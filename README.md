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
2. Processamento de transcricoes para preparacao da memoria.
3. Consulta da memoria por busca semantica e por filtros relacionais.

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
POST /transcripts/process/v1
```

Recebe uma transcricao e organiza o conteudo para memoria semantica e relacional.

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

O endpoint de transcricao ja possui contrato HTTP, autenticacao por token, validacoes, schema de resposta, documentacao FastAPI e testes automatizados. O motor real de STT fica isolado em camada de servico e pode ser executado quando a dependencia local estiver instalada.

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

Depois acesse a documentacao automatica:

```text
http://127.0.0.1:8000/docs
```

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
MINDVOX_API_TOKEN=dev-token MINDVOX_TRANSCRIPTION_MODE=real uv run fastapi dev src/main.py
```

Observacao sobre cache:

- aqui, `cache` nao significa memoria RAM;
- significa uma pasta local em disco onde arquivos baixados ficam guardados;
- se o modelo ja estiver no cache local, o Mindvox usa esses arquivos sem baixar tudo novamente;
- se o modelo ainda nao existir na maquina, o app busca o modelo no Hugging Face no primeiro uso;
- depois do primeiro download, chamadas futuras tendem a carregar o modelo localmente.

Em outra maquina, o mesmo fluxo se aplica: instalar dependencias, iniciar o app em modo real e permitir que o modelo seja baixado do Hugging Face no primeiro uso. Se a maquina nao tiver hardware compativel ou o motor real nao estiver instalado, o endpoint deve retornar erro controlado de indisponibilidade do servico.

Se o terminal ja estiver dentro da pasta `src`, use `fastapi dev main.py`. Se estiver na raiz do projeto, use `fastapi dev src/main.py`.

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
```

Para testar o contrato HTTP da transcricao sem depender do motor real de STT, use:

```bash
MINDVOX_API_TOKEN=dev-token MINDVOX_TRANSCRIPTION_MODE=contract uv run fastapi dev src/main.py
```
