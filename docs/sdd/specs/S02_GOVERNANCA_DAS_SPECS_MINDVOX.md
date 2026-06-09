# Spec S02: Governanca das Specs do Mindvox

## 1. Identificacao

- `ID`: `S02`
- `Tipo`: `Spec`
- `Status`: `aberta`
- `Escopo`: organizacao, precedencia, nomenclatura e ciclo de manutencao das Specs do Mindvox
- `Dependencia normativa`: `S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md`

---

## 2. Finalidade

Esta Spec define como as Specs do Mindvox devem ser organizadas e mantidas.

Ela existe para:

- impedir dispersao de decisoes entre varios documentos;
- separar principios gerais de contratos de endpoint;
- manter cada Spec pequena, legivel e util para implementacao;
- registrar o que esta aberto e o que ja esta fechado;
- evitar que README, contrato de mentoria, rascunhos ou notas virem fontes paralelas de verdade tecnica.

---

## 3. Escopo

Esta Spec cobre:

- tipos documentais usados no SDD do Mindvox;
- regra de precedencia entre documentos;
- status oficiais das Specs;
- padrao de nomenclatura;
- regra de criacao de novas Specs;
- forma esperada das Specs de endpoint;
- criterios de fechamento de Specs.

Esta Spec nao cobre:

- conteudo tecnico detalhado de endpoints;
- escolha de modelos, banco, embeddings ou mecanismos de busca;
- arquitetura interna da aplicacao;
- implementacao de codigo;
- apresentacao academica ou roteiro de video.

Esses temas pertencem a Specs proprias, notas tecnicas ou documentos de entrega.

---

## 4. Regra de Precedencia

No Mindvox, a ordem de autoridade documental e:

1. `S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md`
2. esta `S02_GOVERNANCA_DAS_SPECS_MINDVOX.md`
3. Specs de endpoint fechadas
4. Specs tecnicas fechadas
5. Specs abertas, apenas como rascunho orientador
6. notas tecnicas, relatorios e registros de auditoria
7. `README.md`
8. `docs/mindvox_mentoring_agreement.md`, no que disser respeito ao metodo de trabalho e aos papeis de colaboracao
9. conversas, ideias soltas e rascunhos nao consolidados

Interpretacao obrigatoria:

- a S01 prevalece sobre todos os demais documentos do Mindvox;
- esta S02 governa a organizacao das Specs, mas nao altera os principios da S01;
- uma Spec de endpoint fechada prevalece sobre README ou rascunhos quando o assunto for o contrato daquele endpoint;
- uma Spec tecnica fechada prevalece dentro de seu escopo transversal, mas nao pode alterar o contrato especifico de um endpoint sem revisao da Spec de endpoint correspondente;
- o README deve refletir o estado publico do projeto, sem prometer funcionalidade nao implementada;
- o contrato de mentoria governa a colaboracao didatica, mas nao substitui Specs tecnicas aprovadas.

---

## 5. Tipos Documentais

### 5.1 Spec

Documento normativo que fixa decisoes ja suficientemente maduras para orientar implementacao.

Uma Spec deve:

- declarar seu escopo;
- dizer o que cobre e o que nao cobre;
- registrar dependencias;
- explicitar criterios de aceite ou fechamento;
- evitar misturar assuntos sem necessidade.

### 5.2 Spec de Endpoint

Spec pequena dedicada a um unico endpoint.

Uma Spec de endpoint deve versar somente sobre a materia daquele endpoint.

Ela deve conter, no minimo:

- identificacao;
- finalidade;
- metodo HTTP e rota;
- entradas aceitas;
- resposta de sucesso;
- respostas de erro;
- validacoes;
- seguranca;
- logs;
- documentacao FastAPI esperada;
- exemplos de teste valido e invalido;
- criterios de aceite.

### 5.3 Nota Tecnica

Documento exploratorio para registrar hipoteses, alternativas, pesquisa ou comparacao tecnica.

Uma nota tecnica:

- pode orientar uma decisao futura;
- nao governa implementacao por si so;
- nao substitui uma Spec fechada;
- deve ser convertida em Spec para suas decisoes passarem a orientar codigo.

### 5.4 Relatorio de Verificacao

Documento datado que registra testes, auditorias, achados ou validacoes executadas.

Um relatorio de verificacao:

- registra evidencia;
- pode apontar falhas ou pendencias;
- nao altera uma Spec por si so;
- pode justificar revisao posterior de uma Spec.

### 5.5 README

Documento publico de apresentacao e execucao do projeto.

O README deve ser claro para instruir usuarios e desenvolvedores sobre o projeto, mas nao deve carregar detalhes internos de decisao que pertencem a Specs ou ao acordo de trabalho.

---

## 6. Status Oficiais

As Specs do Mindvox devem usar apenas estes status:

- `aberta`: documento em elaboracao ou revisao, ainda nao aprovado como contrato estavel;
- `fechada`: documento aprovado e valido como referencia normativa dentro de seu escopo;
- `substituida`: documento que deixou de ser vigente porque uma Spec posterior o substituiu explicitamente.

Interpretacao obrigatoria:

- uma Spec aberta pode orientar discussao, mas nao deve ser tratada como contrato final;
- uma Spec fechada pode orientar implementacao;
- uma Spec substituida deve informar isso e apontar para o documento que a substituiu;
- nao usar rotulos vagos como "quase pronta", "em progresso" ou "estavel o bastante".

---

## 7. Nomenclatura

### 7.1 Specs Gerais

Specs gerais devem usar o prefixo `S` seguido de dois digitos:

```text
S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md
S02_GOVERNANCA_DAS_SPECS_MINDVOX.md
```

### 7.2 Specs de Endpoint

Specs de endpoint devem usar o prefixo `E` seguido de dois digitos:

```text
E01_ENDPOINT_HEALTH.md
E02_ENDPOINT_TRANSCRIPTIONS.md
E03_ENDPOINT_TRANSCRIPTS_PROCESS.md
E04_ENDPOINT_SEARCH_SEMANTIC.md
E05_ENDPOINT_SEARCH_RELATIONAL.md
```

Interpretacao obrigatoria:

- o numero indica a ordem didatica de implementacao;
- o nome deve apontar para o endpoint ou recurso principal;
- cada endpoint real do MVP deve ter Spec propria.

### 7.3 Notas e Relatorios

Notas tecnicas e relatorios devem ter nomes datados ou descritivos:

```text
NOTA_STT_ENGINE_CHOICES.md
RELATORIO_VERIFICACAO_E02_TRANSCRIPTIONS_2026-06-07.md
```

Relatorios tecnicos orientadores devem ficar preferencialmente em:

```text
docs/sdd/reports/
```

Interpretacao obrigatoria:

- relatorios em `docs/sdd/reports/` podem consolidar decisoes, auditorias, riscos ou diretrizes;
- relatorios nao governam codigo por si so;
- quando uma diretriz de relatorio passar a orientar implementacao, ela deve ser convertida em Spec, Plano, Tarefas ou emenda aprovada na Spec aplicavel.

---

## 8. Arvore Inicial de Specs

A arvore inicial recomendada para o Mindvox e:

```text
docs/sdd/specs/
  S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md
  S02_GOVERNANCA_DAS_SPECS_MINDVOX.md
  E01_ENDPOINT_HEALTH.md
  E02_ENDPOINT_TRANSCRIPTIONS.md
  E03_ENDPOINT_TRANSCRIPTS_PROCESS.md
  E04_ENDPOINT_SEARCH_SEMANTIC.md
  E05_ENDPOINT_SEARCH_RELATIONAL.md
```

Estado esperado neste momento:

| ID | Documento | Tipo | Status esperado | Funcao |
| --- | --- | --- | --- | --- |
| S01 | `S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md` | Spec geral | `fechada` | Fixar principios e invariantes do Mindvox |
| S02 | `S02_GOVERNANCA_DAS_SPECS_MINDVOX.md` | Spec geral | `aberta` | Governar organizacao das Specs |
| E01 | `E01_ENDPOINT_HEALTH.md` | Spec de endpoint | `fechada` | Definir endpoint de saude da API |
| E02 | `E02_ENDPOINT_TRANSCRIPTIONS.md` | Spec de endpoint | `fechada` | Definir endpoint de transcricao |
| E03 | `E03_ENDPOINT_TRANSCRIPTS_PROCESS.md` | Spec de endpoint | futura | Definir processamento de transcricao |
| E04 | `E04_ENDPOINT_SEARCH_SEMANTIC.md` | Spec de endpoint | futura | Definir busca semantica |
| E05 | `E05_ENDPOINT_SEARCH_RELATIONAL.md` | Spec de endpoint | futura | Definir busca relacional |

---

## 9. Regra de Criacao de Nova Spec

Uma nova Spec deve ser criada quando:

- houver endpoint real a implementar;
- uma decisao tecnica tiver impacto persistente no projeto;
- houver risco de misturar assuntos diferentes em um unico documento;
- precisar ser feita implementacao que ainda nao esta prevista em Spec;
- uma nota tecnica deixar de ser exploratoria e passar a governar comportamento;
- outra Spec precisar ser alterada significativamente.

Uma nova Spec nao deve ser criada apenas por organizacao estetica.

---

## 10. Regra de Manutencao

Mudancas em Specs devem preferir emenda localizada.

Interpretacao obrigatoria:

- evitar reescrita integral sem motivo forte;
- preservar o sentido aprovado pelo autor do projeto;
- nao suprimir justificativas didaticas sem argumento explicito e concordancia do autor;
- registrar adendos relevantes no corpo da propria Spec revisada;
- se uma Spec mudar contrato de endpoint ja implementado, a implementacao e os testes devem ser revisados depois.

### 10.1 Emenda, Adendo, Spec Revisora e Substituicao

Quando uma Spec precisar mudar, escolher a menor forma suficiente:

- `emenda localizada`: ajuste pontual dentro da propria Spec, sem mudar seu sentido principal;
- `adendo`: complemento aprovado que adiciona regra, contexto ou criterio sem substituir a estrutura da Spec;
- `Spec revisora`: nova Spec ou nova versao quando a mudanca for ampla o bastante para reorganizar decisoes, alterar contrato relevante ou exigir nova leitura integral;
- `substituicao`: encerramento explicito da vigencia de uma Spec por outra, com status `substituida` e referencia ao documento sucessor.

Interpretacao obrigatoria:

- mudancas pequenas devem preferir emenda ou adendo;
- mudancas que alterem contrato de endpoint devem revisar a Spec do endpoint;
- mudancas que afetem principios da S01 exigem revisao explicita da S01 antes de qualquer Spec subordinada;
- Spec revisora ou substituicao deve preservar rastreabilidade do motivo da mudanca.

---

## 11. Criterios de Fechamento de Specs

Uma Spec pode ser fechada quando:

- seu escopo estiver claro;
- suas decisoes forem suficientes para orientar o proximo passo;
- nao houver conflito com a S01;
- nao houver conflito com Specs fechadas de maior precedencia;
- as questoes abertas estiverem explicitamente isoladas;
- Adalberto aprovar o conteudo.

Para Specs de endpoint, tambem e necessario que:

- identificacao esteja presente;
- rota e metodo estejam definidos;
- entrada e saida estejam descritas;
- erros principais estejam listados;
- validacoes estejam descritas;
- seguranca esteja descrita;
- logs estejam descritos;
- documentacao FastAPI esperada esteja descrita;
- criterios de teste valido e invalido estejam claros.
- checklist aplicavel do endpoint esteja extraido do modelo geral desta S02;
- todos os itens aplicaveis estejam marcados ou explicitamente justificados como `N/A`.

---

## 12. Modelo Geral de Checklist por Endpoint

Toda Spec de endpoint deve consultar este modelo geral e criar, dentro da propria Spec, uma secao chamada:

```text
Checklist Aplicavel do Endpoint
```

Essa secao deve conter somente os itens aplicaveis ao endpoint atual, copiando ou adaptando os itens abaixo.

Regra de leveza:

- nao e obrigatorio aplicar todos os itens a todos os endpoints;
- itens nao aplicaveis devem ser marcados como `N/A`, com justificativa curta;
- a Spec so pode ser fechada quando todos os itens aplicaveis estiverem marcados;
- o checklist nao substitui a Spec: ele serve como trava final de completude.

### 12.1 Contrato HTTP

- [ ] Metodo HTTP definido.
- [ ] Rota definida.
- [ ] Padrao de versionamento decidido.
- [ ] Finalidade do endpoint explicada.
- [ ] Diferenca entre endpoint operacional e endpoint de negocio esclarecida, quando relevante.

### 12.2 Entrada

- [ ] Parametros de path definidos ou marcados como `N/A`.
- [ ] Parametros de query definidos ou marcados como `N/A`.
- [ ] Body definido ou marcado como `N/A`.
- [ ] Headers exigidos definidos ou marcados como `N/A`.
- [ ] Tipos, obrigatoriedade e limites de entrada descritos.

### 12.3 Saida

- [ ] Resposta de sucesso definida.
- [ ] Status code de sucesso definido.
- [ ] Campos da resposta descritos.
- [ ] Ausencia de dados sensiveis verificada.
- [ ] Schema de resposta definido ou justificadamente omitido.

### 12.4 Erros

- [ ] Erros principais listados.
- [ ] Status codes de erro definidos.
- [ ] Mensagens de erro nao expõem stack trace, paths locais, tokens ou configuracoes internas.
- [ ] Metodo HTTP invalido considerado.
- [ ] Entrada invalida considerada, quando houver entrada.

### 12.5 Seguranca

- [ ] Necessidade de autenticacao decidida.
- [ ] Necessidade de autorizacao decidida.
- [ ] Dados sensiveis identificados ou marcados como `N/A`.
- [ ] Regras de nao vazamento descritas.
- [ ] Uso de `.env`, tokens ou configuracao externa definido ou marcado como `N/A`.

### 12.6 Logs e Observabilidade

- [ ] Eventos permitidos em log descritos.
- [ ] Dados proibidos em log descritos.
- [ ] Logs existentes do servidor considerados.
- [ ] Necessidade de logger proprio decidida.
- [ ] Persistencia de logs decidida ou adiada explicitamente.

### 12.7 Documentacao FastAPI

- [ ] `summary` definido.
- [ ] `description` definida.
- [ ] Respostas principais aparecem na documentacao.
- [ ] Ausencia ou presenca de parametros/body aparece corretamente.
- [ ] Parametros/body possuem descricoes didaticas com exemplos curtos na documentacao interativa, quando existirem.
- [ ] `/openapi.json` deve refletir o contrato aprovado.

### 12.8 Implementacao

- [ ] Router definido.
- [ ] Handler definido com nome explicavel.
- [ ] Router registrado no `app`, quando aplicavel.
- [ ] Endpoint temporario ou exemplo removido, quando aplicavel.
- [ ] Dependencias fora do escopo nao sao importadas.
- [ ] Codigo compila.

### 12.9 Testes Perenes

- [ ] Pasta propria de testes criada em `tests/<spec>_<endpoint>/`.
- [ ] `README.md` da pasta de testes criado.
- [ ] README da pasta de testes explica as hipoteses verificadas.
- [ ] README da pasta de testes explica como executar os testes daquele endpoint.
- [ ] Teste automatizado de sucesso criado.
- [ ] Teste automatizado de erro principal criado.
- [ ] Teste automatizado de metodo invalido criado, quando aplicavel.
- [ ] Teste automatizado do OpenAPI criado, quando relevante.
- [ ] Comando de teste registrado na Spec, plano ou tarefas.
- [ ] Todos os testes passam antes de iniciar o proximo endpoint.
- [ ] Teste funcional manual real executado e registrado, quando o endpoint envolver IA, motor externo, modelo local ou efeito que os testes automatizados de contrato nao comprovem integralmente.

### 12.10 Demonstracao e Explicabilidade

- [ ] Comando de execucao local documentado.
- [ ] Exemplo de chamada valida documentado.
- [ ] Exemplo de falha relevante documentado.
- [ ] Endpoint demonstrado com entrada real representativa, quando aplicavel.
- [ ] Endpoint consegue ser explicado por finalidade, entrada, processamento, saida, erro e teste.
- [ ] Limites de escopo estao claros para evitar crescimento indevido.

### 12.11 Fechamento e Versionamento

Este checklist deve ser executado imediatamente antes do commit final da Spec/endpoint.

- [ ] `git status` revisado.
- [ ] `git diff` revisado.
- [ ] Arquivos alterados pertencem ao escopo da Spec/endpoint atual ou estao justificados.
- [ ] Nenhum segredo, token, `.env`, path sensivel ou dado privado aparece no diff.
- [ ] Nenhum cache, `__pycache__`, arquivo temporario ou artefato gerado indevido aparece no diff.
- [ ] Testes automatizados da Spec/endpoint passaram.
- [ ] Testes gerais passaram.
- [ ] Checklist aplicavel da Spec esta todo marcado ou justificado como `N/A`.
- [ ] README da pasta de testes esta atualizado.
- [ ] Materiais didaticos externos ao repo foram atualizados, quando aplicavel.
- [ ] Mensagem de commit planejada identifica a Spec/endpoint concluida.
- [ ] Commit de fechamento realizado antes de iniciar a proxima Spec/endpoint.

### 12.12 Regra de Extracao

Cada Spec de endpoint deve conter uma tabela curta derivada deste modelo:

```markdown
| Item | Status | Justificativa |
| --- | --- | --- |
| Metodo e rota definidos | [ ] |  |
| Body | N/A | Endpoint nao recebe body |
| Pasta de testes do endpoint | [ ] |  |
| README da pasta de testes | [ ] |  |
| Teste automatizado de sucesso | [ ] |  |
| git status revisado | [ ] |  |
| Commit de fechamento realizado | [ ] |  |
```

Status permitidos:

- `[ ]`: pendente;
- `[x]`: concluido;
- `N/A`: nao aplicavel, sempre com justificativa curta.

---

## 13. Invariantes Operacionais

- A S01 governa todas as demais Specs.
- Esta S02 governa apenas a organizacao das Specs.
- Cada endpoint real do MVP deve ter sua propria Spec.
- Specs de endpoint devem ser pequenas e focadas.
- README nao deve substituir Spec.
- Contrato de mentoria nao deve substituir Spec tecnica.
- Nota tecnica nao deve governar codigo sem conversao ou referencia em Spec.
- Spec aberta nao deve ser tratada como contrato final.
- Spec fechada deve orientar implementacao dentro de seu escopo.

---

## 14. Questoes Abertas

Esta Spec ainda nao decide:

- se havera um indice automatico de Specs;
- se relatorios de verificacao ficarao em `docs/sdd/reports/` ou em outro diretorio;
- se as Specs de endpoint terao template fixo separado;
- se as Specs futuras terao numeracao por modulo alem de `E`.

Essas questoes nao bloqueiam a criacao das primeiras Specs de endpoint.

---

## 15. Criterios de Fechamento Desta Spec

Esta Spec podera passar de `aberta` para `fechada` quando:

- O autor do projeto aprovar a taxonomia documental;
- a precedencia entre S01, S02, Specs de endpoint, README e contrato de mentoria estiver aceita;
- a nomenclatura `Sxx` e `Exx` estiver aceita;
- a regra de Spec pequena por endpoint estiver aceita;
- nao houver conflito com a S01 fechada.

---

## 16. Registro de Fechamento

Status atual: `aberta`.

Esta secao deve ser atualizada quando a Spec for aprovada e fechada.
