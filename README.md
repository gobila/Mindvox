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
POST /transcriptions/v1
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

O projeto esta em desenvolvimento inicial.

Ja existe uma estrutura base em FastAPI, mas os endpoints reais do MVP ainda estao em construcao.

## Como Executar

Entre na pasta do projeto:

```bash
cd /Users/adalbertobatista/Desenvolvedor/atrium/projetos/mindvox
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
