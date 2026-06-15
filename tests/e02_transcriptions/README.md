# Testes da E02: `POST /transcriptions/v1.0.0`

Esta pasta concentra os testes automatizados da Spec E02, relativa ao endpoint de transcricao de audio.

O objetivo destes testes e verificar o contrato HTTP do endpoint: rota, autenticacao, entrada, saida, erros previsiveis, documentacao OpenAPI e cuidado para nao vazar dados sensiveis.

## Hipoteses verificadas

- Uma requisicao valida com `Authorization: Bearer <token>` e arquivo `.wav` aceito retorna `200 OK`.
- Uma requisicao valida com arquivo `.m4a` e `content_type` compativel tambem retorna `200 OK`.
- A resposta de sucesso segue o schema esperado, com `transcription_id`, `text`, `language`, `segments`, `metadata` e `engine`.
- Cada transcricao bruta produzida pelo STT salva automaticamente JSON tecnico no diretorio configurado por `MINDVOX_TRANSCRIPTION_OUTPUT_DIR` e TXT humano no diretorio configurado por `MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR`.
- Quando metadados de aula forem enviados, os artefatos locais podem usar prefixo seguro com data/titulo/sessao para facilitar localizacao, mas continuam terminando com `transcription_id` opaco.
- O TXT humano da E02 contem somente a transcricao bruta, sem cabecalho artificial, para preservar auditabilidade; quando houver segmentos do STT, o texto e paragrafado para leitura humana sem inserir timestamps.
- A resposta de sucesso contem `artifact_locations`, indicando caminho relativo do arquivo humano e do JSON tecnico sem expor path absoluto local.
- O `transcription_id` e opaco, usa prefixo `tr_` e nao incorpora nome de arquivo, token ou path.
- A ausencia de `language` aplica o padrao `pt-BR`.
- O modo usado nos testes e `MINDVOX_TRANSCRIPTION_MODE=contract`, para testar o contrato sem depender do motor real de STT.
- A API rejeita requisicao sem token com `401 Unauthorized`.
- A API rejeita token invalido com `401 Unauthorized`.
- A API rejeita header `Authorization` malformado com `401 Unauthorized`.
- Em desenvolvimento local, `MINDVOX_API_TOKEN` ausente ou vazio usa automaticamente o token didatico `dev-token`.
- A API trata placeholder de `MINDVOX_API_TOKEN` e `dev-token` em deploy publico como token ausente.
- Em `MINDVOX_PUBLIC_DEPLOYMENT=true`, a API rejeita `POST /transcriptions/v1.0.0` quando a aplicacao nao recebe scheme `https`, retornando `403 Forbidden`.
- Em `MINDVOX_PUBLIC_DEPLOYMENT=true`, a API aceita requisicao que chega a aplicacao com scheme `https`.
- Em `MINDVOX_PUBLIC_DEPLOYMENT=true`, a aplicacao rejeita `MINDVOX_TRUSTED_HOSTS=*`.
- A API rejeita requisicao sem arquivo com `422 Unprocessable Entity`.
- A API rejeita arquivo sem nome com `422 Unprocessable Entity`.
- A API rejeita extensao nao suportada com `400 Bad Request`.
- A API rejeita `content_type` incompativel com a extensao com `400 Bad Request`.
- A API rejeita arquivo com extensao aceita mas conteudo invalido com `422 Unprocessable Entity`.
- A API rejeita arquivo acima do limite configurado com `413 Payload Too Large`.
- A API rejeita metadados invalidos em `class_date`, `session_label` e `language` com `422 Unprocessable Entity`.
- A API retorna `503 Service Unavailable` quando o motor de transcricao esta indisponivel.
- A API retorna `500 Internal Server Error` controlado quando ocorre erro interno inesperado.
- A API rejeita metodo HTTP incorreto para a rota.
- A documentacao OpenAPI apresenta o endpoint, o formulario multipart, o esquema Bearer e as respostas principais, incluindo `403`, `500` e `503`.
- A documentacao OpenAPI global informa `Active startup profile`, indicando se a API subiu em `dev`, `contract` ou `prod`.
- A resposta, os erros e os logs nao devem expor token, `.env`, paths locais, audio bruto, transcricao integral ou conteudo interno sensivel.

## Observacao sobre logs

A E02 registra logs operacionais no logger `mindvox.transcriptions`, sem persistencia propria nesta fase do MVP. A persistencia propria de logs fica explicitamente adiada; os logs atuais dependem do processo/servidor usado para executar a API.

## Observacao sobre artefatos de transcricao

Os testes usam diretorios temporarios para `MINDVOX_TRANSCRIPTION_OUTPUT_DIR` e `MINDVOX_TRANSCRIPTION_TEXT_OUTPUT_DIR`. No app real em modo `dev`, os padroes sao `outputs/transcriptions/` para JSON tecnico e `outputs/human/transcriptions/` para TXT humano, ambos fora do Git. Essa persistencia e do artefato bruto da transcricao, nao dos logs. Os nomes podem incluir prefixo sanitizado de metadados para uso humano local, mas o sufixo tecnico `transcription_id` permanece obrigatorio.

## Como executar somente os testes da E02

```bash
uv run python -m unittest discover -s tests/e02_transcriptions -v
```

## Como executar todos os testes

```bash
uv run python -m unittest discover -s tests -v
```

## Observacao sobre o motor de STT

Estes testes nao validam qualidade de transcricao por `mlx-whisper`. Eles validam a borda HTTP da E02.

O motor real deve ser integrado e verificado por testes proprios quando a dependencia local de STT estiver instalada e operacional. Ate la, o modo `contract` e permitido apenas para testes automatizados ou demonstracao controlada do contrato.
