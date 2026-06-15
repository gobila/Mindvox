# Relatorio Tecnico: Interface Humana da E03, Study Package e Vault Opcional

## 1. Identificacao

- `Tipo`: relatorio tecnico de decisao arquitetural e produto
- `Status`: consenso consolidado para especificacao posterior
- `Data`: 2026-06-14
- `Escopo`: consolidar o contrato acordado para uma pagina humana de entrada da E03, uma pagina humana de saida, o artefato `Study Package`, a relacao com E04 e a opcao local de criacao deterministica de Student Vault
- `Endpoint relacionado`: `POST /processed-transcriptions/v1.0.0`
- `Relatorio base relacionado`: `docs/sdd/reports/RELATORIO_SINTESE_E03_CHUNKING_PIPELINE_VAULT.md`
- `Documentos que deverao ser atualizados em etapa posterior`:
  - `docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/plans/P03_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/tasks/T03_TAREFAS_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`
  - `README.md`

---

## 2. Resumo Executivo

A E03 ja evoluiu de um pos-processador simples de transcricao para um pipeline robusto de transformacao de aula em artefatos de estudo. Entretanto, sua interface atual ainda fica presa a duas limitacoes:

1. o Swagger e adequado para documentar e testar a API, mas e ruim como interface humana de uso;
2. a saida atual da E03, embora tecnicamente correta, ainda nao oferece uma visualizacao elegante, organizada e aderente aos nichos reais de estudo ja observados no Student Vault.

A decisao consolidada e criar, em etapa posterior, uma camada de produto sobre a E03:

```text
Pagina humana de entrada
  -> normaliza metadados, audio ou texto bruto

Pipeline E03
  -> pre-auditoria, chunking, LLM, merge canonico, auditoria final

Study Package
  -> artefato canonico estruturado de saida

Pagina humana de resultado
  -> visualizacao clara dos produtos gerados

E04
  -> ingere o Study Package para memoria relacional e vetorial

Exportador opcional Obsidian
  -> cria Student Vault deterministicamente e exporta como redundancia positiva
```

O Obsidian nao deve ser dependencia central do Mindvox. Ele deve ser uma opcao local de exportacao e redundancia. O produto principal deve funcionar para qualquer usuario externo, com ou sem Obsidian.

---

## 3. Principio Central

O `UFG_Pos_2` nao deve ser tratado como destino fixo do sistema.

Ele deve ser tratado como:

```text
uma instancia concreta de uma arquitetura de informacao estudantil
```

Essa arquitetura inspira o Mindvox, mas nao limita o produto a um curso especifico, a uma universidade especifica ou ao uso obrigatorio de Obsidian.

A regra consolidada e:

```text
E03 processa uma sessao de estudo pertencente a um curso informado pelo usuario.
```

Nao processa "uma aula da UFG" por contrato interno fixo.

---

## 4. Curso Como Contexto Persistente

O curso deve ser metadado canonico e contexto persistente do usuario.

Campos conceituais:

```text
course_id
course_name
institution
active_course_id
```

Comportamento esperado:

1. o usuario cria ou seleciona um curso ativo no Mindvox;
2. esse curso permanece como padrao nas proximas execucoes;
3. a cada novo audio ou transcrito, o curso ativo ja vem preenchido;
4. o usuario so altera o curso quando estiver trabalhando em outro curso;
5. depois da alteracao, o novo curso passa a ser o contexto padrao.
6. a adicao de novos cursos gera uma lista flutuante ou seletor equivalente, permitindo que o usuario escolha cursos ja cadastrados sem redigitar nomes previamente informados.

Exemplos:

```text
course_id: ufg_pos_2
course_name: UFG Pos 2

course_id: puc_mestrado_tx
course_name: PUC Mestrado Tx

course_id: universidade_gama_filho
course_name: Universidade Gama Filho
```

Essa persistencia, combinada com uma lista de cursos ja cadastrados, evita que o usuario precise preencher sempre a informacao mais estavel do contexto de estudo.

---

## 5. Pagina Humana de Entrada da E03

A pagina humana de entrada deve existir porque o Swagger nao e a interface adequada para o fluxo real de uso.

O Swagger permanece como:

```text
documentacao tecnica e console de teste da API
```

A nova pagina de entrada deve ser:

```text
interface operacional humana para desenvolvedor aprendiz e usuario final
```

### 5.1 Campos esperados

A pagina deve permitir informar ou confirmar:

```text
course_id
course_name
institution
discipline
professor
class_number
class_date
session_number
session_label
class_title
language
processing_profile
input_type
raw_text
raw_text_file
audio_file
```

O campo `raw_text` deve ser uma area ampla de texto, nao um input de linha unica. Deve permitir colar transcricoes longas com legibilidade minima.

### 5.2 Modos de entrada

A pagina deve aceitar pelo menos tres modos:

```text
audio_file
  -> audio enviado pelo usuario para transcricao e processamento

raw_text
  -> transcrito colado diretamente na pagina

raw_text_file
  -> arquivo de transcrito preparado previamente
```

### 5.3 Entrada a partir do Obsidian em modo local/dev

No ambiente local do autor, o fluxo ja existente deve continuar sendo suportado:

```text
UFG_Pos_2/00_Inbox/_captura-rapida.md
  -> propriedades da nota
  -> sessao ativa
  -> transcrito colado na sessao
  -> script extrai a sessao e gera um `.txt` em `inputs/e03_raw_texts/`
  -> script gera ou atualiza metadados auxiliares do transcrito
  -> pagina humana da E03 pode ser preenchida automaticamente com esses metadados
  -> pagina humana da E03 recebe como entrada o `.txt` preparado
```

Esse fluxo e local e opcional. Ele nao pode ser requisito para usuarios externos.

### 5.4 Preenchimento visivel para usuario aprendiz

Foi acordado que, em modo de desenvolvimento/local, deve existir uma forma automatizada por script, mas didaticamente visivel, de preencher a pagina da E03 com metadados vindos do Vault Obsidian ativo por meio de um comando CLI local.

Racional:

- o usuario aprendiz precisa ver que os campos foram preenchidos;
- o fluxo nao deve depender de preenchimento invisivel que gere duvida operacional;
- a automacao nao deve apagar token, estado de `Try it out` ou configuracoes ja feitas em tela;
- o comando fornecido ao usuario deve usar path absoluto para evitar erro comum de diretorio.

Essa camada e conveniencia local. O contrato publico da API continua independente dela.

---

## 6. Normalizacao Interna da Requisicao

Todas as formas de entrada devem convergir para um objeto canonico interno.

Exemplo conceitual:

```text
E03ProcessingRequest
  course
  discipline
  class_metadata
  session_metadata
  input_source
  processing_options
```

Isso permite que os fluxos abaixo sejam equivalentes dentro do backend:

```text
Usuario externo no formulario web
Usuario local com Obsidian e script
Usuario tecnico chamando o endpoint diretamente
```

O ponto tecnico e evitar dois pipelines paralelos. Deve existir um unico contrato interno, alimentado por fontes diferentes.

---

## 7. Pipeline E03 Apos Entrada Normalizada

Depois da normalizacao, a E03 deve executar o pipeline ja consolidado:

```text
entrada normalizada
  -> preservacao do bruto
  -> pre-auditoria de transcricao quando aplicavel
  -> chunking semantico para entradas longas
  -> pos-processamento LLM chunk-by-chunk
  -> merge canonico deterministico
  -> auditoria final de cobertura
  -> quarentena se a regua semantica reprovar
  -> geracao do Study Package
```

A pagina humana de entrada nao substitui o endpoint. Ela apenas reduz atrito e erro operacional.

---

## 8. Study Package Como Saida Canonica

A E03 deve passar a produzir um artefato de saida mais rico que o JSON minimo atual.

Nome recomendado:

```text
E03 Study Package
```

O Study Package e o artefato canonico de aula processada. Ele deve ser suficientemente estruturado para:

- renderizacao humana elegante;
- entrega HTTP/API;
- persistencia local em `outputs/`;
- exibicao automatica ao fim do processamento, preferencialmente em janela flutuante, modal, drawer ou pagina de resultado aberta pelo proprio fluxo;
- ingestao pelo E04;
- exportacao opcional para Obsidian.

### 8.1 Estrutura proposta

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

### 8.2 Significado das secoes

`metadata`:
guarda curso, instituicao, disciplina, professor, aula, data, sessao, idioma e perfil de processamento.

`source`:
registra se a origem foi audio, texto colado, arquivo preparado ou captura local vinda de Vault.

`raw_transcription`:
preserva o bruto auditavel ou aponta para o arquivo bruto salvo.

`didactic_text`:
guarda o texto didatico final, em prosa sequencial com paragrafos, sem headings artificiais indevidos e sem virar bloco plano tipo `.txt`.

`themes`:
lista temas relevantes da aula ou sessao.

`technical_terms`:
lista termos tecnicos com definicoes ou contexto.

`technology_mentions`:
lista tecnologias, ferramentas, bibliotecas, frameworks, plataformas e sistemas citados.

`operational_anchors`:
guarda links, URLs, prazos, trabalhos, entregas, eventos, contatos, canais, documentos institucionais e dados pragmaticos que o aluno normalmente anotaria em caderno.

`concept_candidates`:
guarda candidatos a notas conceituais futuras.

`audit_report`:
registra suspeitas, correcoes, lacunas, reprovacoes, retries, chunks, evidencias e rastreabilidade.

`memory_manifest`:
informa ao E04 quais partes devem ir para memoria relacional e quais devem ir para campo vetorial.

`export_targets`:
descreve destinos opcionais, como arquivos locais, pagina humana e exportacao Obsidian.

---

## 9. Pagina Humana de Saida

A E03 deve ter uma pagina de resultado para visualizacao humana do Study Package.

Exemplo conceitual:

```text
/app/e03/results/{processed_transcription_id}
```

Ou, em fase inicial de desenvolvimento:

```text
/dev/e03/results/{processed_transcription_id}
```

### 9.1 Secoes da pagina

A pagina deve apresentar os resultados em nichos claros:

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

### 9.2 Racional

Essa pagina resolve um problema real: a resposta tecnica da API nao e a melhor forma de leitura humana.

A pagina deve permitir ao usuario:

- ler o texto didatico com conforto;
- conferir os temas extraidos;
- encontrar tecnologias e termos sem procurar no bruto;
- ver links, datas, trabalhos e eventos separados;
- acessar o bruto auditavel;
- verificar se houve suspeitas, retries ou quarentena;
- exportar ou copiar artefatos.

---

## 10. Relacao Com E04

O E03 nao deve assumir a responsabilidade de memoria final.

A fronteira correta e:

```text
E03
  -> produz Study Package e memory_manifest

E04
  -> ingere, persiste, relaciona e disponibiliza buscas
```

### 10.1 Memoria relacional

O E04 deve poder extrair do Study Package dados como:

```text
curso
disciplina
professor
aula
sessao
data
temas
termos
tecnologias
links
prazos
entregas
eventos
contatos
documentos
relacoes entre artefatos
```

Esses dados pertencem ao SQLite, que e a memoria relacional escolhida para o Mindvox neste desenho. A expressao "outra memoria relacional" deve ser entendida apenas como possibilidade arquitetural futura, nao como referencia ao Obsidian. O Obsidian, quando ativado, permanece como exportacao Markdown e redundancia positiva, nao como banco relacional principal.

### 10.2 Campo vetorial

O E04 deve poder inserir em campo vetorial:

```text
didactic_text
chunks didaticos
resumos
conceitos candidatos
trechos semanticamente relevantes
```

Assim, a busca semantica fica independente do Obsidian.

### 10.3 Consequencia para usuario externo

O usuario externo nao deve depender de Obsidian para recuperar o conhecimento produzido.

O caminho principal deve ser:

```text
Study Package
  -> E04
  -> memoria relacional + busca vetorial
```

O Obsidian permanece como exportacao opcional e redundancia positiva.

---

## 11. Obsidian Como Opcao Local e Redundancia Positiva

O Obsidian deve ser oferecido como opcao, nao como dependencia.

Contrato:

```text
Mindvox funciona sem Obsidian.
Se o usuario quiser Obsidian, Mindvox pode criar um Student Vault padronizado.
```

Uso previsto:

- backup humano legivel;
- redundancia contra instabilidade de acesso a memoria SQLite;
- ambiente pessoal de estudo;
- leitura e organizacao manual adicional;
- interoperabilidade com fluxos locais do aluno.

---

## 12. Criacao Deterministica de Vault

Foi descartada, para a primeira versao, a opcao de "selecionar Vault existente".

Motivo:

- o usuario externo nao conhece o contrato Student Vault;
- validar Vault existente aumenta escopo;
- corrigir estrutura ausente aumenta risco;
- orientar manualmente o usuario exigiria entregar instrucoes ou skills adicionais;
- isso polui o produto inicial.

Decisao:

```text
E03/Student Vault Export v1 cria Vault novo deterministicamente.
Nao importa Vault existente.
Nao tenta corrigir Vault existente.
```

### 12.1 Pre-requisitos

Para ativar a opcao Obsidian:

```text
Obsidian instalado: recomendado
path base informado: obrigatorio
course_id/course_name: obrigatorios
```

Tecnicamente, o script nao precisa controlar o Obsidian. Ele cria uma pasta Markdown compativel; depois o Obsidian pode abrir essa pasta como Vault.

### 12.2 Estrutura criada

O script deve criar estrutura compatibilizada com Student Vault:

```text
00_Inbox/
01_Aulas/
02_Conceitos/
03_Operacional/
03_Audios/
03_Imagens/
04_Revisao/
05_Referencias/
06_MOC/
07_Admin/
_Templates/
```

E arquivos operacionais minimos:

```text
00_Inbox/_captura-rapida.md
03_Operacional/_captura-operacional.md
03_Operacional/links-de-aula.md
03_Operacional/prazos-e-eventos.md
03_Operacional/contatos.md
03_Operacional/canais-e-comunidades.md
03_Operacional/documentos-institucionais.md
```

### 12.3 Associacao com curso ativo

Ao criar o Vault, o Mindvox deve registrar:

```text
course_id
course_name
vault_path
obsidian_export_enabled
```

A partir dai, exports futuros daquele curso podem usar esse Vault como destino.

---

## 13. Mapeamento Study Package Para Student Vault

Quando a opcao Obsidian estiver ativa, o exportador deve projetar o Study Package nos nichos do Vault.

Mapeamento conceitual:

| Secao do Study Package | Destino no Student Vault |
| --- | --- |
| `raw_transcription` | `01_Aulas/[disciplina]/brutos/` |
| `didactic_text` | `01_Aulas/[disciplina]/Aulas/` |
| `themes` | `01_Aulas/[disciplina]/resumos/` ou nota auxiliar |
| `technical_terms` | `02_Conceitos/` quando promovidos |
| `technology_mentions` | nota de apoio da disciplina ou conceito |
| `operational_anchors.links` | `03_Operacional/links-de-aula.md` |
| `operational_anchors.deadlines` | `03_Operacional/prazos-e-eventos.md` |
| `operational_anchors.contacts` | `03_Operacional/contatos.md` |
| `operational_anchors.channels` | `03_Operacional/canais-e-comunidades.md` |
| `operational_anchors.documents` | `03_Operacional/documentos-institucionais.md` |
| `audit_report` | nota tecnica vinculada ao processamento ou `07_Admin/` |

Regra importante:

```text
O E03 nao deve inventar estrutura no momento da exportacao.
O Vault deve nascer padronizado; o exportador apenas escreve nos destinos previstos.
```

---

## 14. Fluxos Consolidados

### 14.1 Fluxo local com Obsidian ja usado pelo autor

```text
UFG_Pos_2/00_Inbox/_captura-rapida.md
  -> usuario cola transcrito na sessao correta
  -> propriedades indicam curso, disciplina, professor, aula, data e sessao
  -> script prepara arquivo em inputs/
  -> pagina humana da E03 recebe ou confirma metadados
  -> E03 processa
  -> Study Package e gerado
  -> resultado aparece em pagina humana
  -> exportacao opcional grava no Vault do curso ativo
```

### 14.2 Fluxo de usuario externo sem Obsidian

```text
Usuario abre pagina humana da E03
  -> escolhe ou cria curso ativo
  -> preenche disciplina, professor, aula, data e sessao
  -> envia audio ou cola transcrito
  -> E03 processa
  -> Study Package e gerado
  -> pagina humana de resultado e exibida
  -> E04 ingere dados para memoria relacional e vetorial
```

### 14.3 Fluxo de usuario externo com Obsidian opcional

```text
Usuario ativa opcao Obsidian
  -> informa path base
  -> Mindvox cria Vault novo deterministicamente
  -> curso ativo fica associado ao vault_path
  -> E03 processa aulas normalmente
  -> Study Package e gerado
  -> E04 ingere como memoria principal
  -> exportador grava copia organizada no Vault
```

---

## 15. Guardrails

1. O Swagger nao deve ser tratado como interface humana principal.
2. A pagina humana de entrada nao deve substituir o endpoint publico.
3. O Obsidian nao pode ser dependencia obrigatoria da E03.
4. O `UFG_Pos_2` nao pode ficar hardcoded como destino geral.
5. O curso deve ser contexto persistente e alteravel pelo usuario.
6. A opcao Obsidian v1 deve criar Vault novo; nao deve importar Vault existente.
7. O exportador Obsidian deve operar sobre Study Package ja produzido, nao sobre dados intermediarios soltos.
8. O E04 deve ser o dono da memoria relacional e vetorial.
9. O Student Vault deve ser redundancia positiva e ambiente local de estudo, nao banco principal do produto.
10. O bruto auditavel deve sempre ser preservado.
11. A pagina de saida deve separar dados conceituais, operacionais e auditaveis.
12. Itens operacionais incertos devem manter marcacao de pendencia ou suspeita.

---

## 16. Implicacoes Para Spec, Plano e Tarefas

Esta decisao devera gerar atualizacoes futuras em tres frentes.

### 16.1 Spec E03

Adicionar:

- pagina humana de entrada;
- campos canonicos de curso ativo;
- suporte a texto colado em textarea;
- Study Package como artefato de saida;
- pagina humana de resultado;
- relacao com E04 por `memory_manifest`;
- exportacao Obsidian opcional;
- criacao deterministica de Student Vault novo.

### 16.2 Plano P03

Adicionar fases:

1. modelar `StudyPackage`;
2. criar pagina humana de entrada;
3. adaptar script de captura do Vault para alimentar a pagina ou gerar entrada compativel;
4. criar renderizador humano de resultado;
5. criar `memory_manifest`;
6. criar script opcional de Student Vault novo;
7. criar exportador Obsidian em modo opcional;
8. documentar fluxo sem Obsidian e fluxo com Obsidian.

### 16.3 Tarefas T03

Adicionar tarefas concretas:

- definir schema de `StudyPackage`;
- persistir `StudyPackage` em `outputs/`;
- criar rota ou pagina local de entrada;
- criar rota ou pagina de resultado;
- trocar `raw_text` visual por textarea na interface humana;
- manter Swagger apenas como interface tecnica;
- adicionar configuracao de curso ativo;
- adicionar registro de `vault_path` por curso;
- criar script de scaffold de Student Vault;
- criar testes de geracao de Vault;
- criar testes de mapeamento de Study Package para Vault;
- atualizar README.

---

## 17. Decisoes Consolidadas

1. A E03 precisa de uma pagina humana de entrada melhor que Swagger.
2. O Swagger permanece como documentacao e console tecnico, nao como UI principal.
3. A pagina de entrada deve aceitar audio, texto colado e arquivo de transcrito.
4. O campo `raw_text` deve ser textarea ou componente equivalente amplo.
5. O curso deve ser metadado canonico persistente.
6. O ultimo curso ativo deve permanecer selecionado ate mudanca explicita do usuario.
7. O `UFG_Pos_2` e apenas uma instancia concreta atual, nao destino fixo do sistema.
8. O pipeline local com `_captura-rapida.md` continua valido para o autor.
9. Usuarios externos nao dependem de Obsidian.
10. A E03 deve produzir um `Study Package` estruturado.
11. A pagina de saida deve renderizar o Study Package em nichos humanos claros.
12. O E04 deve consumir `memory_manifest` para memoria relacional e vetorial.
13. Obsidian deve ser opcao local de exportacao e redundancia positiva.
14. A opcao Obsidian v1 deve criar Vault novo deterministicamente.
15. Nao sera suportada, nesta fase, importacao ou selecao de Vault existente.
16. O script de criacao de Vault deve seguir o contrato Student Vault.
17. O exportador Obsidian escreve nos nichos padronizados do Vault criado.
18. O README deve explicar que Obsidian e opcional e que a memoria principal do produto nao depende dele.

---

## 18. Conclusao

O consenso atual transforma a E03 em algo mais maduro que um endpoint de pos-processamento textual.

A E03 passa a ser o gerador de um pacote estruturado de estudo:

```text
audio ou transcrito bruto
  -> pipeline de estabilizacao
  -> Study Package
  -> pagina humana
  -> memoria E04
  -> exportacao opcional Obsidian
```

Essa arquitetura preserva o contrato academico da API, melhora drasticamente a experiencia humana, prepara a memoria relacional/vetorial do E04 e ainda permite que o Obsidian seja usado como redundancia local organizada.

A decisao mais importante e manter a ordem correta de responsabilidades:

```text
E03 produz o pacote.
E04 memoriza e disponibiliza busca.
Obsidian exporta uma copia local opcional.
```

Com isso, o Mindvox continua sendo produto geral para qualquer aluno, de qualquer curso, e nao uma automacao privada presa ao Vault `UFG_Pos_2`.
