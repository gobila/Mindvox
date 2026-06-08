# Spec E01: Endpoint de Saude da API

## 1. Identificacao

- `ID`: `E01`
- `Tipo`: `Spec de Endpoint`
- `Status`: `fechada`
- `Endpoint`: `GET /health`
- `Escopo`: verificacao simples de disponibilidade da API
- `Dependencias normativas`:
  - `S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md`
  - `S02_GOVERNANCA_DAS_SPECS_MINDVOX.md`

---

## 2. Finalidade

Este endpoint informa se a API Mindvox esta viva e apta a responder requisicoes HTTP basicas.

Ele existe para:

- permitir verificacao rapida de execucao local;
- facilitar testes iniciais no navegador, terminal ou Postman;
- servir como primeiro endpoint didatico do projeto;
- oferecer base simples para futuras verificacoes de infraestrutura.

---

## 3. Escopo

Este endpoint cobre:

- resposta simples de saude da API;
- contrato HTTP minimo;
- resposta estruturada;
- documentacao automatica no FastAPI;
- teste valido simples;
- logs operacionais sem dados sensiveis.

Este endpoint nao cobre:

- verificacao do motor STT;
- carregamento de modelo;
- teste de banco de dados;
- teste de memoria semantica;
- autenticacao de usuarios;
- verificacao de filas, storage externo ou servicos cloud;
- exposicao de configuracoes internas.

Esses temas pertencem a endpoints ou specs futuras de readiness, diagnostico ou observabilidade.

---

## 4. Metodo e Rota

Metodo HTTP:

```text
GET
```

Rota:

```text
/health
```

Interpretacao:

- `health` indica verificacao simples de disponibilidade;
- a rota fica fora do padrao versionado `/<recurso>/v1` por ser endpoint operacional basico;
- a rota nao representa recurso de negocio do Mindvox.

---

## 5. Entrada

O endpoint nao recebe body.

Parametros:

| Campo | Tipo | Obrigatorio | Descricao |
| --- | --- | --- | --- |
| nenhum | - | - | Este endpoint nao exige parametros |

Headers:

- nao exige `Authorization`;
- nao exige headers especiais.

Justificativa:

- `GET /health` nao manipula dados sensiveis;
- a resposta deve ser generica e segura;
- endpoints operacionais simples podem ser usados por ferramentas de monitoramento ou verificacao de disponibilidade.

---

## 6. Validacoes

Validacoes minimas:

- aceitar apenas metodo `GET`;
- nao exigir body;
- nao depender de arquivo, banco, modelo de IA ou servico externo;
- nao retornar dados sensiveis.

---

## 7. Processamento

Fluxo esperado:

```text
receber requisicao
  -> montar resposta padrao de saude
  -> registrar log operacional minimo
  -> devolver resposta HTTP
```

Separacao esperada de responsabilidades:

- `router`: declara a rota e o contrato FastAPI;
- `schema`: define o formato de resposta, se o projeto optar por schema dedicado;
- `service`: opcional neste endpoint; pode ser omitido se nao houver logica alem da resposta estatica;
- `settings`: pode fornecer nome do servico ou versao publica, sem expor segredos.

Regra:

- o endpoint deve permanecer simples;
- nao deve carregar modelo STT;
- nao deve validar configuracoes sensiveis;
- nao deve chamar dependencias externas.

---

## 8. Resposta de Sucesso

Status HTTP:

```text
200 OK
```

Formato planejado:

```json
{
  "status": "ok",
  "service": "mindvox-api",
  "version": "v1.0.0"
}
```

Campos:

| Campo | Descricao |
| --- | --- |
| `status` | Estado basico da API; valor esperado: `ok` |
| `service` | Nome publico e generico do servico |
| `version` | Versao publica do contrato ou da API, em formato semantico prefixado por `v`, como `v1.0.0` |

Regra de seguranca:

- a resposta nao deve expor paths locais;
- a resposta nao deve expor `.env`, tokens, chaves, configuracoes privadas ou detalhes de infraestrutura;
- a resposta nao deve listar modelos carregados, provedores, bancos ou credenciais.

---

## 9. Respostas de Erro

### 9.1 Metodo Nao Permitido

Status:

```text
405 Method Not Allowed
```

Uso:

- quando a rota for chamada com metodo diferente de `GET`.

Observacao:

- esse comportamento pode ser tratado automaticamente pelo FastAPI.

### 9.2 Erro Interno Inesperado

Status:

```text
500 Internal Server Error
```

Resposta exemplo:

```json
{
  "detail": "Internal health check error."
}
```

Regra:

- erros internos nao devem expor stack trace, paths locais ou configuracoes privadas.

---

## 10. Seguranca

Regras minimas:

- nao exigir token no MVP, pois o endpoint nao manipula dados sensiveis;
- nao retornar informacoes internas;
- nao retornar configuracoes de ambiente;
- nao retornar status de dependencias sensiveis;
- nao registrar headers sensiveis;
- manter a resposta generica.

Horizonte futuro:

- uma spec futura podera criar endpoint de readiness autenticado ou restrito;
- uma spec futura podera separar liveness, readiness e diagnostics;
- em cenario cloud, `GET /health` podera ser usado como verificacao simples por infraestrutura, desde que continue sem dados sensiveis.

---

## 11. Logs

Logs devem registrar apenas dados operacionais necessarios.

Permitido:

- chamada ao endpoint;
- status HTTP retornado;
- duracao da requisicao;
- identificador generico de requisicao, se existir.

Nao permitido:

- headers sensiveis;
- tokens;
- `.env`;
- paths locais;
- configuracoes internas;
- dados de audio, transcricao ou memoria.

---

## 12. Documentacao FastAPI Esperada

A documentacao automatica deve mostrar:

- titulo claro do endpoint;
- descricao curta da finalidade;
- ausencia de body;
- resposta de sucesso;
- erros principais;
- indicacao de que este endpoint nao verifica STT, banco, memoria ou dependencias externas.

Texto sugerido para `summary`:

```text
Health Check
```

Texto sugerido para `description`:

```text
Returns a minimal health status for the Mindvox API.
```

---

## 13. Criterios de Aceite

O endpoint podera ser considerado pronto quando:

- a rota `GET /health` existir;
- a rota devolver `200 OK` quando a API estiver rodando;
- a resposta seguir schema estruturado;
- a resposta nao expuser dados sensiveis;
- a documentacao do FastAPI exibir o endpoint corretamente;
- metodo diferente de `GET` nao for aceito;
- logs nao vazarem dados sensiveis;
- houver teste valido;
- O autor do projeto conseguir explicar o papel limitado do endpoint.

---

## 14. Exemplos de Teste

### 14.1 Teste Valido

Entrada:

```text
GET /health
```

Resultado esperado:

```text
200 OK
```

Resposta esperada:

```json
{
  "status": "ok",
  "service": "mindvox-api",
  "version": "v1.0.0"
}
```

### 14.2 Teste Invalido: Metodo Nao Permitido

Entrada:

```text
POST /health
```

Resultado esperado:

```text
405 Method Not Allowed
```

### 14.3 Teste Automatizado Perene

O endpoint deve possuir teste automatizado no repositorio para que o contrato da E01 possa ser reexecutado antes da E02 e em mudancas futuras.

Comando:

```bash
uv run python -m unittest discover -s tests -v
```

Cobertura minima:

- `GET /health` retorna `200 OK`;
- resposta contem `status`, `service` e `version` conforme a E01;
- resposta contem somente campos publicos aprovados;
- `POST /health` retorna `405 Method Not Allowed`;
- OpenAPI nao declara parametros de URL nem body para este endpoint;
- OpenAPI documenta `summary` e `description` do endpoint.

---

## 15. Checklist Aplicavel do Endpoint

Checklist extraido do modelo geral da S02.

| Item | Status | Justificativa |
| --- | --- | --- |
| Metodo HTTP definido | [x] | `GET` aprovado para verificacao simples de disponibilidade |
| Rota definida | [x] | `/health` aprovada |
| Padrao de versionamento decidido | [x] | Endpoint operacional simples fica fora do padrao `/<recurso>/v1` |
| Finalidade explicada | [x] | Verificar se a API esta viva e apta a responder HTTP basico |
| Diferenca entre endpoint operacional e endpoint de negocio esclarecida | [x] | Spec declara que `/health` nao representa recurso de negocio |
| Parametros de path | N/A | Endpoint nao exige identificador na rota |
| Parametros de query | N/A | Endpoint nao exige filtros ou consulta adicional |
| Body | N/A | Endpoint nao recebe corpo de requisicao |
| Headers exigidos | N/A | Endpoint nao exige `Authorization` nem headers especiais |
| Tipos, obrigatoriedade e limites de entrada | [x] | Entrada explicitamente definida como ausente |
| Resposta de sucesso definida | [x] | JSON com `status`, `service` e `version` |
| Status code de sucesso definido | [x] | `200 OK` |
| Campos da resposta descritos | [x] | Campos documentados em tabela |
| Ausencia de dados sensiveis verificada | [x] | Resposta nao expoe paths, `.env`, tokens, modelos ou infraestrutura |
| Schema de resposta | N/A | O endpoint usa resposta estatica minima; schema dedicado foi omitido para preservar simplicidade do MVP |
| Erros principais listados | [x] | `405` e erro interno inesperado descritos |
| Status codes de erro definidos | [x] | `405 Method Not Allowed` e `500 Internal Server Error` |
| Mensagens de erro sem vazamento sensivel | [x] | Spec proibe stack trace, paths locais e configuracoes privadas |
| Metodo HTTP invalido considerado | [x] | `POST /health` deve retornar `405` |
| Entrada invalida considerada | N/A | Nao ha entrada a validar |
| Necessidade de autenticacao decidida | [x] | Sem autenticacao no MVP por nao manipular dados sensiveis |
| Necessidade de autorizacao decidida | [x] | Sem autorizacao no health simples |
| Dados sensiveis identificados | [x] | Spec declara que o endpoint nao deve retornar dados sensiveis |
| Regras de nao vazamento descritas | [x] | Regras definidas em seguranca e resposta |
| Uso de `.env`, tokens ou configuracao externa | N/A | Endpoint nao deve ler configuracao sensivel nem depender de `.env` |
| Eventos permitidos em log descritos | [x] | Chamada, status HTTP, duracao e identificador generico |
| Dados proibidos em log descritos | [x] | Headers sensiveis, tokens, `.env`, paths locais, audio, transcricao e memoria |
| Logs existentes do servidor considerados | [x] | Logs operacionais minimos podem ser produzidos pelo servidor ASGI/FastAPI durante execucao |
| Necessidade de logger proprio decidida | N/A | Logger proprio adiado; nao ha logica de negocio neste endpoint |
| Persistencia de logs decidida | N/A | Persistencia de logs fica para observabilidade futura |
| `summary` definido | [x] | `Health Check` |
| `description` definida | [x] | `Returns a minimal health status for the Mindvox API.` |
| Respostas principais aparecem na documentacao | [x] | OpenAPI deve documentar o endpoint e resposta `200` |
| Parametros/body aparecem corretamente | [x] | Teste automatizado confirma que OpenAPI nao declara parametros de URL nem body |
| `/openapi.json` reflete o contrato aprovado | [x] | Teste automatizado cobre ausencia de entrada, `summary` e `description` |
| Router definido | [x] | `src/routers/health.py` declara `APIRouter` |
| Handler definido com nome explicavel | [x] | `health_check` descreve a funcao do endpoint |
| Router registrado no `app` | [x] | `src/main.py` inclui `app.include_router(health_router)` |
| Endpoint temporario ou exemplo removido | [x] | `/items/` nao pertence ao MVP e nao deve existir |
| Dependencias fora do escopo nao sao importadas | [x] | Rota incompleta de transcricao nao deve ser importada na E01 |
| Codigo compila | [x] | Verificacao por `py_compile` prevista |
| Pasta propria de testes criada | [x] | `tests/e01_health/` |
| README da pasta de testes criado | [x] | `tests/e01_health/README.md` |
| README da pasta de testes explica hipoteses verificadas | [x] | README descreve sucesso, metodo invalido, OpenAPI, ausencia de entrada e resposta sem campos sensiveis |
| README da pasta de testes explica como executar os testes | [x] | README registra comando geral e comando especifico da E01 |
| Teste automatizado de sucesso criado | [x] | `tests/e01_health/test_health.py` cobre `GET /health` e resposta publica esperada |
| Teste automatizado de erro principal criado | [x] | `tests/e01_health/test_health.py` cobre `POST /health` como metodo nao permitido |
| Teste automatizado de metodo invalido criado | [x] | `POST /health` retorna `405` |
| Teste automatizado do OpenAPI criado | [x] | `tests/e01_health/test_health.py` valida metadados e ausencia de entrada no OpenAPI |
| Comando de teste registrado | [x] | `uv run python -m unittest discover -s tests -v` |
| Todos os testes passam antes do proximo endpoint | [x] | Requisito registrado para bloquear inicio da E02 |
| Comando de execucao local documentado | [x] | `uv run fastapi dev src/main.py` |
| Exemplo de chamada valida documentado | [x] | `GET /health` |
| Exemplo de falha relevante documentado | [x] | `POST /health` |
| Endpoint explicavel por finalidade, entrada, processamento, saida, erro e teste | [x] | Spec cobre cada uma dessas dimensoes |
| Limites de escopo claros | [x] | STT, banco, memoria, readiness e diagnostics adiados |
| `git status` revisado | [x] | Revisado na auditoria final antes do commit manual |
| `git diff` revisado | [x] | Diff revisado na auditoria final antes do commit manual |
| Arquivos alterados pertencem ao escopo da E01 ou estao justificados | [x] | Alteracoes correlatas de governanca, E02 e materiais didaticos foram solicitadas no mesmo ciclo de fechamento |
| Nenhum segredo, token, `.env`, path sensivel ou dado privado aparece no diff | [x] | Busca por padroes sensiveis nao encontrou ocorrencias nos arquivos relevantes |
| Nenhum cache, `__pycache__`, temporario ou artefato gerado indevido aparece no diff | [x] | Caches gerados foram removidos antes do commit manual |
| Testes automatizados da E01 passaram | [x] | `uv run python -m unittest discover -s tests/e01_health -v` passou na auditoria final |
| Testes gerais passaram | [x] | `uv run python -m unittest discover -s tests -v` passou na auditoria final |
| Checklist aplicavel da E01 esta todo marcado ou justificado como `N/A` | [x] | Todos os itens aplicaveis foram resolvidos; commit manual fica registrado em item proprio |
| README da pasta de testes esta atualizado | [x] | `tests/e01_health/README.md` atualizado |
| Materiais didaticos externos ao repo foram atualizados | [x] | Checklists didaticos criados no vault `UFG_Pos_2` |
| Mensagem de commit planejada identifica a E01 concluida | [x] | Sugestao: `feat(e01): implement health endpoint with tests and governance` |
| Commit de fechamento realizado | [ ] | Aguardando commit manual do autor do projeto |

---

## 16. Decisoes de MVP e Detalhes de Implementacao

Decisoes adotadas para o MVP:

- rota: `GET /health`;
- resposta minima e generica;
- sem autenticacao no health simples;
- sem verificacao de dependencias;
- sem exposicao de dados internos.

Esta Spec adia explicitamente para specs futuras:

- endpoint de readiness;
- endpoint de diagnostics;
- verificacao de modelo STT carregado;
- verificacao de banco, memoria, filas ou storage;
- health checks especificos para ambiente cloud.

---

## 17. Criterios de Fechamento Desta Spec

Esta Spec podera passar de `aberta` para `fechada` quando:

- rota e metodo forem aprovados;
- formato de resposta for aprovado;
- limites de escopo forem aprovados;
- regras de seguranca e logs forem aprovadas;
- documentacao FastAPI esperada for aprovada;
- criterios de teste valido e invalido estiverem aceitos;
- checklist aplicavel do endpoint estiver totalmente marcado ou justificado como `N/A`.

---

## 18. Registro de Fechamento

Status atual: `fechada`.

Fechada em: `2026-06-07`.

Motivo do fechamento:

- rota e metodo aprovados;
- resposta minima aprovada;
- ausencia de autenticacao aprovada para health simples;
- limites de escopo aprovados;
- regras de seguranca e logs aprovadas;
- documentacao FastAPI esperada aprovada;
- criterios de teste valido e invalido aceitos;
- readiness, diagnostics e verificacoes de dependencias explicitamente adiados.

Emenda localizada em `2026-06-08`:

- o valor esperado de `version` na resposta do health foi ajustado de `v1` para `v1.0.0`;
- motivo: adotar anotacao semantica completa para a versao publica da API.

Emenda localizada em `2026-06-08`:

- checklist aplicavel do endpoint incorporado conforme modelo geral da S02;
- criterios de fechamento atualizados para exigir checklist resolvido antes de fechar Specs de endpoint;
- textos de `summary` e `description` alinhados com a implementacao e os testes automatizados.
