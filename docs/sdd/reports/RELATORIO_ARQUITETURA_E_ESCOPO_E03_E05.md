# Relatorio Tecnico: Arquitetura e Escopo do Mindvox entre E03 e E05

## 1. Identificacao

- `Tipo`: Relatorio tecnico orientador / ADR leve
- `Status`: orientador, nao normativo
- `Data`: 2026-06-09
- `Escopo`: registrar decisao arquitetural sobre entrega academica imediata e arquitetura completa futura do Mindvox
- `Documentos relacionados`:
  - `docs/sdd/specs/S01_CONSTITUICAO_E_INVARIANTES_MINDVOX.md`
  - `docs/sdd/specs/S02_GOVERNANCA_DAS_SPECS_MINDVOX.md`
  - `docs/sdd/specs/E02_ENDPOINT_TRANSCRIPTIONS.md`
  - `docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/reports/RELATORIO_DIRETRIZES_E03_SERVICO_IA_LLM.md`

---

## 2. Finalidade

Este relatorio registra a decisao arquitetural discutida apos a prova real da E02.

O objetivo e impedir que a decisao se perca no historico de conversa e separar claramente:

- o escopo viavel da entrega academica imediata;
- o escopo completo futuro do app;
- o papel de cada endpoint;
- a regra de composicao interna por servicos, sem encadear endpoints HTTP dentro do mesmo app.

Este relatorio nao substitui Specs de endpoint.

Conforme a S02, quando uma diretriz aqui passar a orientar implementacao, ela deve ser convertida em Spec, Plano, Tarefas ou emenda aprovada na Spec aplicavel.

---

## 3. Contexto

A E02 foi validada com transcricao real de aula longa.

Resultado observado:

- `POST /transcriptions/v1.0.0` retornou `200 OK`;
- o motor real foi `mlx-whisper`;
- o modelo foi `mlx-community/whisper-large-v3-turbo-fp16`;
- a transcricao bruta foi extensa, coerente e segmentada;
- a qualidade foi suficiente para alimentar processamento posterior;
- tambem ficou claro que a transcricao bruta nao e, por si so, um produto final ideal para uso comercial sem pos-processamento.

Essa constatacao motivou a definicao da E03 como endpoint intermediario de pos-processamento de alto nivel.

---

## 4. Decisao Principal

O Mindvox deve ser entendido em duas camadas de escopo:

1. escopo da entrega academica imediata;
2. escopo completo futuro do app.

### 4.1 Escopo da Entrega Academica Imediata

A entrega viavel ate sexta-feira deve fechar com:

```text
E01 - health
E02 - transcricao bruta real
E03 - pos-processamento de alto nivel
```

Interpretacao:

- E01 demonstra saude operacional da API;
- E02 demonstra IA/STT real;
- E03 demonstra segundo servico de IA, agora textual, voltado a pos-processar transcricao;
- E03 deve ser simples o bastante para ser implementada, testada, explicada e demonstrada sem comprometer a entrega;
- E03 nao deve incluir banco, memoria persistente, embeddings ou busca.

### 4.2 Escopo Completo Futuro do App

O app completo planejado deve evoluir para:

```text
E01 - health
E02 - transcricao bruta
E03 - pos-processamento de alto nivel
E04 - ingestao em memoria relacional/vetorial
E05 - recuperacao por busca semantica e relacional
```

Interpretacao:

- E04 sera a porta de entrada para inserir conhecimento na memoria do sistema;
- E05 sera a porta de consulta da memoria ja existente;
- E04 e E05 pertencem ao escopo completo do app, mas nao ao escopo obrigatorio da entrega imediata.

---

## 5. Papel de Cada Endpoint

### 5.1 E01: Health

Endpoint:

```text
GET /health
```

Papel:

- verificar se a API esta viva;
- nao e endpoint de IA;
- nao manipula dados sensiveis;
- serve como base operacional e didatica.

### 5.2 E02: Transcricao Bruta

Endpoint:

```text
POST /transcriptions/v1.0.0
```

Papel:

- receber audio gravado;
- executar STT real;
- devolver transcricao bruta;
- preservar rastreabilidade do que foi ouvido;
- retornar segmentos temporais, metadados e engine.

Uso comercial parcial possivel:

- cliente que deseja apenas transcricao bruta pode usar E02 diretamente.

Limite:

- E02 nao promete texto final editado;
- erros de STT, termos tecnicos aproximados, marcas de oralidade e ausencia de diarizacao final sao limites esperados da transcricao bruta.

### 5.3 E03: Pos-processamento de Alto Nivel

Endpoint proposto:

```text
POST /processed-transcriptions/v1.0.0
```

Papel:

- receber audio ou transcricao bruta;
- se receber audio, usar internamente o servico de transcricao ja criado para E02;
- produzir texto limpo e mais legivel;
- separar ou organizar por temas;
- normalizar termos tecnicos provaveis;
- devolver resultado estruturado sem gravar em memoria.

Uso comercial parcial possivel:

- cliente que deseja uma transcricao mais utilizavel, limpa e organizada pode usar E03 diretamente.

Limite:

- E03 nao cria memoria persistente;
- E03 nao faz busca;
- E03 nao substitui revisao humana definitiva.

### 5.4 E04: Ingestao em Memoria

Endpoint futuro sugerido:

```text
POST /memory/ingestions/v1.0.0
```

Papel:

- receber audio, transcricao bruta ou transcricao ja processada;
- orquestrar internamente os servicos necessarios;
- se receber audio, usar o servico de transcricao;
- se receber transcricao bruta, usar o servico de pos-processamento;
- se receber texto ja processado, seguir para ingestao;
- gravar informacao na memoria relacional e/ou vetorial do Mindvox;
- distribuir informacao por relacoes estruturadas e proximidade semantica.

Uso comercial parcial mais completo:

- cliente que deseja inserir novo conhecimento na memoria do sistema usa E04.

Limite:

- E04 ainda nao e busca;
- E04 e ingestao/indexacao.

### 5.5 E05: Recuperacao de Informacao

Endpoint futuro sugerido:

```text
POST /memory/search/v1.0.0
```

Ou, se a Spec futura preferir separar por metodo/recurso:

```text
GET /memory/search/v1.0.0
```

Papel:

- consultar a memoria ja existente;
- recuperar informacao por busca semantica;
- recuperar informacao por filtros relacionais;
- devolver trechos, temas, fontes e referencias conforme a memoria disponivel.

Uso comercial completo:

- cliente que deseja consultar informacoes ja inseridas no Mindvox usa E05.

Limite:

- E05 depende da memoria criada por E04 ou por processos equivalentes de ingestao.

---

## 6. Regra Arquitetural de Composicao

Endpoints nao devem chamar endpoints HTTP internos dentro do mesmo app quando o objetivo for encadear funcoes do proprio Mindvox.

Regra:

```text
Errado:
E03 -> HTTP -> E02
E04 -> HTTP -> E03 -> HTTP -> E02

Correto:
E02 -> transcription_service
E03 -> transcription_service + postprocessing_service
E04 -> transcription_service + postprocessing_service + memory_ingestion_service
E05 -> memory_search_service
```

Motivo:

- evita latencia desnecessaria;
- evita acoplamento artificial por rede;
- evita duplicacao de autenticacao interna;
- facilita testes unitarios e de contrato;
- preserva clareza de responsabilidade;
- mantem a API modular sem transformar a arquitetura interna em cadeia de chamadas HTTP.

---

## 7. Modelo de Servicos Internos

Servicos internos previstos ou sugeridos:

| Servico | Responsabilidade |
| --- | --- |
| `transcription_service` | STT e montagem da transcricao bruta |
| `postprocessing_service` | texto didatico, organizacao tematica, normalizacao tecnica e inventario de tecnologias citadas |
| `memory_ingestion_service` | criacao de registros de memoria e chunks |
| `vector_store_service` | operacoes vetoriais e embeddings |
| `relational_store_service` | persistencia relacional e filtros estruturados |
| `memory_search_service` | recuperacao semantica e relacional |

Interpretacao:

- endpoints sao contratos publicos;
- services sao blocos internos reutilizaveis;
- composicao de funcionalidades deve ocorrer nos services, nao em chamadas HTTP internas.

---

## 8. Consequencias Para a Entrega

### 8.1 Consequencias Positivas

- reduz o escopo da entrega imediata;
- permite apresentar dois servicos de IA de forma clara;
- preserva qualidade e explicabilidade;
- evita tentar implementar memoria e busca em prazo curto;
- facilita o roteiro da apresentacao;
- permite mostrar arquitetura evolutiva completa sem prometer que tudo estara implementado agora.

### 8.2 Riscos Evitados

- misturar pos-processamento, banco, embeddings e busca dentro da E03;
- transformar E03 em endpoint grande demais;
- iniciar E04/E05 antes de E03 estar testada;
- perder rastreabilidade entre transcricao bruta e texto processado;
- vender E02 como texto final quando ela entrega corretamente apenas o bruto.

### 8.3 Riscos Restantes

- E03 depende de uma decisao pragmatica sobre motor textual;
- provider externo pode exigir chave e internet;
- modelo local pode aumentar requisito de hardware;
- pos-processamento de alto nivel precisa ter escopo simples para caber no prazo;
- E03 tambem precisara de prova real humana antes do commit de fechamento.

---

## 9. Escopo Recomendado Para a E03

Para manter a entrega viavel, a E03 deve entregar:

- `raw_text`;
- `didactic_text`;
- `themes`;
- `technical_terms`;
- `technology_mentions`;
- `processing_notes`;
- `metadata`;
- `source`;
- `processing_engine`.

Interpretacao:

- `raw_text` preserva o lastro bruto;
- `didactic_text` substitui qualquer ideia anterior de `clean_text`;
- `themes` organiza os nucleos semanticos;
- `technical_terms` normaliza conceitos tecnicos;
- `technology_mentions` lista ferramentas, plataformas, bibliotecas, APIs, providers e tecnologias citadas;
- `processing_notes` registra incertezas e cuidados sem expor prompt integral ou raciocinio interno.

E03 nao deve entregar nesta fase:

- memoria persistida;
- embeddings;
- busca;
- chunks vetoriais;
- tabelas relacionais definitivas;
- interface grafica;
- agente complexo.

---

## 10. Ponto de Apresentacao Academica

Na apresentacao, a arquitetura pode ser explicada assim:

> O Mindvox foi desenhado como uma API modular. A entrega implementa a saude da API, a transcricao real de audio e o pos-processamento textual. Esses endpoints ja sao utilizaveis de forma parcial. A arquitetura completa futura adiciona ingestao em memoria relacional/vetorial e busca semantica/relacional.

Mensagem essencial:

- o projeto nao esta abandonando memoria e busca;
- memoria e busca foram isoladas em E04/E05 para controlar escopo;
- a entrega ate E03 demonstra um pipeline funcional e explicavel;
- o app completo continua arquitetado ate E05.

---

## 11. Status da Decisao

Status atual: `aceita como diretriz orientadora`.

Decisao:

- entrega academica imediata fecha com E03;
- app completo futuro vai ate E05;
- E03 deve permanecer limitada a pos-processamento de alto nivel;
- E04 deve tratar ingestao em memoria;
- E05 deve tratar recuperacao de informacao;
- endpoints publicos nao devem chamar endpoints publicos internos por HTTP para compor funcionalidades do proprio app.

Proxima acao:

- revisar e fechar a Spec E03;
- criar Plano P03;
- criar Tarefas T03;
- implementar E03 apenas depois da Spec E03 estar aprovada.
