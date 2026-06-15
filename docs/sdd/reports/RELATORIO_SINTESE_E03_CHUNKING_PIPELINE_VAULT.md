# Relatorio Tecnico: Sintese da Estabilizacao da E03, Chunking Semantico e Pipeline Mindvox/Vault

## 1. Identificacao

- `Tipo`: relatorio tecnico de sintese e decisao
- `Status`: orientador para continuidade da E03
- `Data`: 2026-06-12
- `Escopo`: consolidar achados de benchmark, correcoes de contrato, decisoes arquiteturais e desenho de pipeline para a E03
- `Endpoint relacionado`: `POST /processed-transcriptions/v1.0.0`
- `Documentos relacionados`:
  - `docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/plans/P03_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/tasks/T03_TAREFAS_IMPLEMENTACAO_E03_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/reports/RELATORIO_BENCHMARK_E03_MODELOS_LLM.md`
  - `docs/sdd/reports/RELATORIO_DIRETRIZES_E03_SERVICO_IA_LLM.md`
  - `src/services/prompts/e03_postprocessing_manual.md`
  - `scripts/semantic_chunk_transcript.py`
  - `scripts/process_e03_semantic_chunks.py`
  - `scripts/benchmark_e03_models.py`

---

## 2. Resumo Executivo

A E03 foi inicialmente concebida como endpoint de pos-processamento textual por LLM para transformar transcricoes brutas em material didatico. O contrato publico permanece correto: receber audio ou texto bruto e entregar cinco produtos principais:

1. `raw_text`
2. `didactic_text`
3. `themes`
4. `technical_terms`
5. `technology_mentions`

O campo `processing_notes` permanece como auxiliar tecnico, voltado a registrar incertezas, correcoes e cuidados de processamento.

Os testes demonstraram que o modelo local mais eficiente ate agora continua sendo:

```text
Qwen3.6-35B-A3B-MTP-Q8.gguf
```

Entretanto, a abordagem inicial de mandar uma transcricao longa inteira para um unico ciclo de pos-processamento apresentou perda semantica relevante. A falha nao foi apenas tecnica; foi epistemica: o LLM atuou como filtro editorial, omitindo topicos, casos, autoria de falas e discussoes empiricas.

A solucao arquitetural mais promissora descoberta foi mudar a unidade de processamento:

```text
transcricao longa integral
  -> segmentacao/chunking tematico por codigo
  -> E03 executada chunk por chunk
  -> agregacao posterior
```

O benchmark real com `tfidf` + Qwen 35B-A3B Q8 processou `9/9` chunks com sucesso, sem erro 500, sem JSON invalido e com cobertura semantica substancialmente melhor.

Rodada posterior com pre-auditoria da transcricao bruta antes do Qwen confirmou a melhora do desenho:

```text
E02 raw JSON
  -> pre-auditoria lexical com timestamps, clipes e re-STT pontual
  -> raw_text_for_qwen.txt saneado
  -> chunking TF-IDF
  -> Qwen chunk-by-chunk
  -> merge canonico deterministico
  -> auditoria final dos artefatos semanticos
```

Na aula `Rogerio-A1S1-2026-05-09.m4a`, a pre-auditoria reduziu ruido lexical antes do LLM e a auditoria final corrigida fechou com `0` issues. Isso reforca a decisao de estabilizar a E03 por pipeline, e nao por troca precipitada de modelo.

Decisao principal:

- manter o contrato publico da E03 para clientes da API;
- usar chunking semantico como estrategia interna de estabilizacao;
- tratar a exportacao para Obsidian/Student Vault como segunda destinacao opcional, pessoal e local, nunca como requisito para o endpoint;
- separar claramente os artefatos publicos do Mindvox dos artefatos estudantis do Vault.

---

## 3. Problema Original Observado

O problema investigado foi a perda semantica no `didactic_text` produzido a partir de transcricao bruta longa.

Relatorio comparativo externo apontou que a saida processada pelo Qwen 35B-A3B Q8 nao continha tudo o que semanticamente estava no bruto. As perdas principais foram:

- omissao total do projeto Positivo sobre licitacoes publicas, editais, diarios oficiais, anexos nao estruturados e score de viabilidade;
- omissao ou abstracao excessiva da discussao sobre vies de respostas no NPS;
- reducao excessiva da discussao arquitetural sobre Data Warehouse, Data Lake, banco de producao e risco de derrubar sistemas de matricula;
- abstracao da metodologia de AutoML, omitindo a dor operacional que motivou o loop de testes temporais;
- perda de autoria e contexto humano em falas de alunos como Leo, Antonio, Mara, Carlos e Eduardo.

Diagnostico:

```text
O modelo nao estava apenas removendo redundancia.
Ele estava resumindo editorialmente a aula.
```

Esse comportamento viola a regra central da E03:

```text
semantica nao pode ser suprimida;
ela so pode ser enxugada onde houver redundancia real.
```

---

## 4. Correcoes Ja Aplicadas no Contrato E03

Antes da mudanca para chunking, foram introduzidas correcoes defensivas no proprio contrato de pos-processamento.

Principais mudancas:

- inclusao de ancoras semanticas protegidas;
- reforco do prompt em `src/services/prompts/e03_postprocessing_manual.md`;
- validacao posterior da cobertura semantica em `src/services/postprocessing_service.py`;
- rejeicao de resposta estruturalmente valida, mas semanticamente insuficiente;
- retry com motivo concreto quando a saida omite ancoras obrigatorias;
- erro especifico de cobertura insuficiente no roteador da E03;
- ajuste do benchmark para usar o mesmo prompt real do endpoint.

Objetivo dessas mudancas:

```text
reduzir a liberdade editorial do LLM
e transformar perda semantica em falha detectavel.
```

Limite encontrado:

- as ancoras ajudam, mas nao eliminam sozinhas o risco de perda quando a entrada e longa demais;
- quanto maior o texto enviado de uma vez, maior a tendencia do modelo a priorizar organizacao editorial sobre preservacao semantica fina;
- portanto, a correcao de prompt e validacao deve ser mantida, mas nao deve ser a unica defesa.

---

## 5. Benchmark Original de Modelos Locais

O benchmark original avaliou modelos locais via `llama.cpp`/`llama-server`, com endpoint compativel com OpenAI.

Entrada:

```text
transcription_id: tr_20260609T154710Z_35969e23
input_chars: 42.997 aproximados
```

Resultado comparativo principal:

| Modelo | Status | Tempo | Saida | Temas | Termos | Observacao |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Gemma 4 12B Q8 | passou | `77,26s` | `7.144` chars | `4` | `8` | valido, mas menos rico |
| Qwen 3.6 27B Q8 | passou | `188,46s` | `7.840` chars | `5` | `8` | muito mais lento |
| Qwen 3.6 35B-A3B Q8 | passou | `55,83s` | `11.426` chars | `6` | `10` | melhor resultado global |

Decisao:

```text
qwen35a3b-q8 permanece como modelo local preferencial da E03.
```

Razoes:

- melhor tempo total observado;
- melhor taxa de geracao;
- maior riqueza de saida;
- boa aderencia inicial ao JSON;
- arquitetura MoE/A3B reduz custo efetivo por geracao.

---

## 6. Teste de Texto Corrigido Integral

Foi testada a hipotese de fazer a E03 produzir uma versao quase integral corrigida da transcricao.

Resultados:

- `corrected_full_text` como string longa falhou em JSON por caractere de controle;
- versao em lista de paragrafos foi tecnicamente valida, mas gerou quase o mesmo tamanho do bruto;
- uma execucao valida produziu aproximadamente `42.892` caracteres para uma entrada de `42.998` caracteres;
- tempo observado: aproximadamente `225s`.

Decisao:

```text
Nao tornar corrected_full_text requisito padrao da E03.
```

Justificativa:

- duplica a funcao auditavel da E02;
- aumenta muito o custo;
- nao resolve por si so a organizacao didatica;
- cria ambiguidade entre transcricao bruta e texto didatico;
- a E03 deve transformar, nao retranscrever.

---

## 7. Teste LongWriter GLM4 9B

Foi testado o modelo:

```text
LongWriter-glm4-9B-Q8_0.gguf
```

Contexto do teste:

- modelo carregou com sucesso no `llama.cpp`;
- contexto operacional de `65536` tokens foi aceito;
- entrada real tinha `67015` caracteres;
- prompt tinha aproximadamente `19902` tokens.

Resultado:

- tempo total aproximado: `876,64s`;
- gerou `20000` tokens e bateu o teto configurado;
- saida nao foi JSON valido;
- campos publicos obrigatorios da E03 nao ficaram recuperaveis;
- diagnostico curto tambem retornou Markdown/fences em vez de JSON valido, mesmo com `response_format: {"type": "json_object"}`.

Decisao:

```text
LongWriter-glm4-9B-Q8_0.gguf foi descartado para a E03 sob o contrato atual.
```

Medidas executadas:

- arquivo local removido;
- artefatos de benchmark removidos;
- registro de descarte preservado em relatorio;
- decisao registrada para evitar repeticao acidental do trabalho.

Condicao para revisitar a familia:

- somente se houver mudanca material de runtime ou metodo, como JSON schema/grammar realmente forcado, outro servidor comprovadamente aderente a JSON estruturado, ou evidencia forte de compatibilidade com o contrato da E03.

---

## 8. Mudanca Arquitetural: Chunking Semantico

A virada principal foi reconhecer que o problema nao estava apenas no modelo, mas na unidade de processamento.

Hipotese:

```text
Se o texto bruto longo for dividido em blocos tematicos menores,
o modelo tende a preservar mais semantica,
obedecer melhor ao prompt
e reduzir falhas estruturais.
```

Foi criado o script experimental:

```text
scripts/semantic_chunk_transcript.py
```

Caracteristicas:

- ferramenta de bancada, nao parte da API publica;
- le transcricao bruta;
- segmenta o texto em unidades;
- agrupa segmentos por proximidade tematica;
- opera em memoria, sem banco vetorial;
- gera relatorios em `.benchmarks/e03_semantic_chunks/`;
- suporta `tfidf`, `bertimbau` e `all`;
- permite centralizacao de vetores para reduzir anisotropia do BERT cru.

Conclusao tecnica importante:

```text
Nao e necessario banco vetorial para esta fase.
O agrupamento pode ser feito em memoria porque o documento e unico.
```

---

## 9. Benchmark de Chunking Semantico

Entrada real:

```text
outputs/human/transcriptions/tr_20260611T190500Z_42f70772.txt
input_chars: 67015
segments: 61
```

### 9.1 TF-IDF baseline v2

Resultado escolhido para o primeiro teste real:

| Metrica | Valor |
| --- | ---: |
| metodo | `tfidf` |
| chunks | `9` |
| min tokens | `456` |
| max tokens | `3684` |
| media tokens | `1863,33` |
| tempo de chunking | `0,03s` |

Leitura qualitativa:

- conservador;
- rapido;
- preservou blocos criticos;
- produziu chunks menores e operacionalmente confortaveis;
- foi escolhido como default experimental inicial.

### 9.2 Bertimbau cru

| Metrica | Valor |
| --- | ---: |
| metodo | `bertimbau` |
| chunks | `4` |
| min tokens | `1873` |
| max tokens | `4999` |
| media tokens | `4192,25` |
| tempo | `136,18s` |

Leitura qualitativa:

- semanticamente interessante;
- gerou blocos grandes demais para o objetivo operacional;
- misturou trechos distantes;
- nao foi escolhido como primeiro default.

### 9.3 Bertimbau centered th020

| Metrica | Valor |
| --- | ---: |
| metodo | `bertimbau` com vetores centralizados |
| chunks | `9` |
| min tokens | `274` |
| max tokens | `3602` |
| media tokens | `1863,22` |
| tempo | `6,06s` |

Leitura qualitativa:

- melhorou muito em relacao ao Bertimbau cru;
- ficou proximo do perfil de tamanho do TF-IDF;
- ainda apresentou misturas tematicas que exigem avaliacao;
- permanece candidato promissor, mas nao default.

### 9.4 Bertimbau centered th030

| Metrica | Valor |
| --- | ---: |
| metodo | `bertimbau` com vetores centralizados |
| chunks | `10` |
| min tokens | `48` |
| max tokens | `2917` |
| media tokens | `1676,90` |
| tempo | `6,05s` |

Leitura qualitativa:

- criou chunk pequeno demais;
- risco de fragmentacao artificial;
- util para experimento, mas nao para default atual.

Decisao:

```text
Usar TF-IDF baseline v2 como primeira estrategia operacional.
Manter Bertimbau centered como linha de pesquisa secundaria.
```

---

## 10. Processamento E03 Chunk-by-Chunk

Foi criado o runner experimental:

```text
scripts/process_e03_semantic_chunks.py
```

Caracteristicas:

- le `chunks.json`;
- chama o servico real de pos-processamento da E03;
- processa cada chunk separadamente;
- grava resultado incremental;
- nao altera o endpoint publico;
- nao faz merge canonico final;
- gera relatorio local em `.benchmarks/e03_chunk_postprocessing/`.

Benchmark real:

```text
run: .benchmarks/e03_chunk_postprocessing/20260612T000603Z_qwen35a3b-tfidf-9chunks-real/
chunks_file: .benchmarks/e03_semantic_chunks/20260611T234456Z_e03-real-transcript-tfidf-baseline-v2/chunks.json
method: tfidf
postprocessing_mode: local
llm_model: qwen35a3b-q8
```

Resultado agregado:

| Metrica | Valor |
| --- | ---: |
| chunks | `9` |
| chunks com sucesso | `9` |
| chunks com erro | `0` |
| tempo total | `443,209s` |
| total didactic chars | `32001` |
| total themes | `41` |
| total technical terms | `67` |
| total technology mentions | `56` |

Resultado por chunk:

| Chunk | Status | Input chars | Didactic chars | Themes | Terms | Tech | Tempo |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `tfidf-01` | pass | `7605` | `3060` | `5` | `5` | `4` | `35,078s` |
| `tfidf-02` | pass | `8113` | `3631` | `4` | `8` | `9` | `47,652s` |
| `tfidf-03` | pass | `3553` | `3278` | `4` | `7` | `3` | `40,059s` |
| `tfidf-04` | pass | `14733` | `3921` | `6` | `10` | `8` | `57,732s` |
| `tfidf-05` | pass | `8064` | `4441` | `6` | `13` | `7` | `72,704s` |
| `tfidf-06` | pass | `7865` | `3949` | `4` | `7` | `9` | `54,831s` |
| `tfidf-07` | pass | `2594` | `2600` | `3` | `5` | `4` | `36,508s` |
| `tfidf-08` | pass | `12710` | `5281` | `6` | `8` | `8` | `69,066s` |
| `tfidf-09` | pass | `1822` | `1840` | `3` | `4` | `4` | `29,579s` |

Resultado tecnico:

```text
O processamento chunk-by-chunk eliminou o erro 500 observado na execucao longa
e reduziu o risco de JSON invalido sob a carga real testada.
```

---

## 11. Checagem de Cobertura Semantica

Foi feita uma checagem textual simples sobre os resultados agregados do benchmark chunk-by-chunk.

Itens criticos recuperados:

- Positivo;
- licitacoes;
- editais;
- diarios oficiais;
- score;
- NPS;
- Data Lake;
- banco de producao;
- AutoML / auto machine learning;
- separacao temporal de treino/teste;
- invisible banking;
- mainframe;
- Cobol;
- Mara;
- Carlos;
- Antonio;
- Leo;
- restaurante universitario / RU.

Item ainda nao recuperado nominalmente:

- Eduardo.

Interpretacao:

- a discussao de NPS apareceu;
- o nome `Eduardo` nao apareceu nominalmente na checagem textual;
- isso ainda exige revisao humana de qualidade;
- a melhora em relacao ao processamento monolitico e forte, mas nao encerra a validacao semantica.

Limite da checagem:

```text
Esta verificacao foi lexical, nao uma auditoria semantica completa.
Ela serve como evidencia inicial, nao como prova definitiva.
```

---

## 12. Interpretacao Tecnica dos Resultados

Os resultados apontam para uma conclusao consistente:

```text
O Qwen 35B-A3B Q8 nao deve ser descartado.
Ele deve ser usado com melhor estrategia de entrada.
```

Motivo:

- no processamento integral, o modelo foi rapido, mas editorializou demais;
- com chunking, o mesmo modelo produziu saidas mais completas e aderentes;
- modelos alternativos testados nao demonstraram vantagem operacional;
- LongWriter GLM4 9B falhou no contrato estrutural;
- Bertimbau e embeddings ajudam no chunking, nao necessariamente substituem o LLM de pos-processamento.

Decisao:

```text
Estabilizar a E03 por pipeline,
nao por troca precipitada de modelo.
```

---

## 13. Contrato Publico da API Continua Sendo Prioritario

O Mindvox e uma API avaliada academicamente. Portanto, a E03 deve continuar entregando diretamente ao cliente HTTP os artefatos contratados.

Saida publica obrigatoria:

```json
{
  "raw_text": "...",
  "didactic_text": "...",
  "themes": [],
  "technical_terms": [],
  "technology_mentions": [],
  "processing_notes": []
}
```

O cliente hipotetico do professor nao possui o Vault Obsidian do autor. Por isso:

- o endpoint nao pode depender do Vault;
- a resposta HTTP deve ser completa;
- os artefatos locais em `outputs/` continuam relevantes;
- a exportacao para Vault deve ser opcional e paralela.

Separacao correta:

```text
contrato API
  -> resposta HTTP
  -> outputs/human/
  -> outputs/technical/

contrato estudantil local
  -> Vault Obsidian
  -> Student Vault
```

---

## 14. Segunda Destinacao: Student Vault

A exportacao para o Vault foi definida como uma segunda destinacao local, util ao estudo pessoal, mas fora do contrato publico da API.

Estrutura recomendada por disciplina:

```text
01_Aulas/[Disciplina]/brutos/
  transcricoes-auditaveis/

01_Aulas/[Disciplina]/textos-didaticos/

00_Inbox/_captura-rapida.md
```

Mapeamento dos artefatos:

| Artefato Mindvox | Destino API | Destino Vault |
| --- | --- | --- |
| `raw_text` | resposta HTTP + outputs | `brutos/transcricoes-auditaveis/` |
| `didactic_text` | resposta HTTP + outputs | `textos-didaticos/` |
| `themes` | resposta HTTP + outputs | inbox como sintese preliminar |
| `technical_terms` | resposta HTTP + outputs | inbox como material preliminar |
| `technology_mentions` | resposta HTTP + outputs | inbox como material preliminar |
| ancoras semanticas/operacionais | interno/experimental | inbox ou captura operacional preliminar |

Racional:

- `raw_text` integral e diferente dos brutos recortados ja existentes no Student Vault;
- por isso, deve ficar em subpasta propria dentro de `brutos/`;
- `didactic_text` ja e texto estudantil longo e deve ir direto para pasta definitiva;
- listas e ancoras ainda podem exigir interpretacao, entao entram como material preliminar para processamento posterior.

---

## 15. Papel da Inbox no Novo Pipeline

A inbox nao deve receber o texto didatico longo definitivo.

Ela deve receber:

- candidatos a conceitos;
- tecnologias citadas;
- temas relevantes;
- links detectados;
- prazos;
- entregas;
- pendencias;
- nomes proprios relevantes;
- ancoras operacionais;
- observacoes marcadas como preliminares.

Exemplo de estatuto correto:

```markdown
- [sintese preliminar Mindvox] Temas detectados:
  - APIs como camada de abstracao
  - Integracao com sistemas legados
  - Data Lake e protecao do banco de producao

- [pendente] Confirmar URL citada sobre FastAPI do Zero.
```

O processamento final dentro do Vault deve ficar a cargo de uma segunda etapa com LLM mais potente ou com a skill `student-vault-processing`, que ja conhece:

- contrato de sessoes;
- destinos canonicos;
- relacao entre bruto, nota, conceito e resumo;
- subsetor operacional;
- guardrails epistemologicos.

---

## 16. Relacao com o Raycast Capture Router

Foi inspecionado o sistema local em:

```text
/Users/adalbertobatista/Desenvolvedor/raycast
```

Achados principais:

- `obsidian-capture-router.sh` ja sabe inserir capturas na `_captura-rapida.md`;
- existe perfil `ufg_pos_2` em modo `student-session`;
- o destino atual esta travado no perfil `ufg_pos_2`;
- o roteador le `sessao-ativa` no frontmatter da nota;
- a funcao `insert_entry_file_in_student_session()` injeta conteudo no bloco `## Sessao N`.

Config atual:

```json
{
  "defaultProfile": "ufg_pos_2",
  "profiles": {
    "ufg_pos_2": {
      "mode": "student-session",
      "vaultPath": "/Users/adalbertobatista/Library/Mobile Documents/iCloud~md~obsidian/Documents/UFG_Pos_2",
      "captureNote": "00_Inbox/_captura-rapida.md"
    }
  }
}
```

Decisao:

```text
Usar o Raycast router como referencia operacional,
mas nao acoplar a E03 diretamente ao estado global do Raycast.
```

Motivo:

- o roteador atual depende de `sessao-ativa`;
- o Mindvox deve poder inserir por sessao explicitamente;
- scripts de bancada devem ser testaveis sem UI;
- o Vault e uma segunda destinacao opcional, nao parte do endpoint.

---

## 17. Pipeline Consolidado Recomendado

Pipeline publico da API:

```text
audio ou raw_text
  -> E02, se entrada for audio
  -> raw_text auditavel
  -> chunking interno, se texto exceder limite operacional
  -> E03 por chunk
  -> merge/deduplicacao final
  -> auditoria final por evidencias, quando houver suspeitas
  -> resposta HTTP com cinco entregas publicas
  -> artefatos Mindvox em outputs/
```

Pipeline experimental de auditoria final:

```text
merged_public_result.json
  + transcricao tecnica E02 com segmentos/timestamps
  + merge_audit.json
  + audio original, quando disponivel
  -> deteccao conservadora de suspeitas
  -> localizacao em segmentos timestampados
  -> plano de recorte de audio por ocorrencia
  -> clipes WAV, quando audio estiver disponivel
  -> re-transcricao pontual futura
  -> correcao somente por evidencia
```

Pipeline refinado recomendado apos a segunda aula:

```text
audio original
  -> E02 gera transcricao bruta timestampada
  -> pre-auditoria da transcricao bruta
     -> siglas raras
     -> grafias canonicas provaveis
     -> termos tecnicos suspeitos
     -> re-STT pontual por clipe
     -> anotacoes/correcoes auditaveis antes do Qwen
  -> chunking semantico
  -> E03/Qwen por chunk
  -> merge deterministico
  -> auditoria final pos-merge
     -> omissoes
     -> entidades geradas
     -> autoria ausente
     -> grafias residuais
  -> resposta final e artefatos
```

Motivo:

```text
Quanto menos ruido lexical for entregue ao Qwen,
menor a chance de confusao interpretativa no texto didatico final.
```

Pipeline local para Vault:

```text
resultado E03
  -> raw_text
     -> 01_Aulas/[Disciplina]/brutos/transcricoes-auditaveis/

  -> didactic_text
     -> 01_Aulas/[Disciplina]/textos-didaticos/

  -> themes, technical_terms, technology_mentions, anchors
     -> 00_Inbox/_captura-rapida.md
     -> sessao correta quando conhecida
     -> marcados como sintese preliminar ou pendente

  -> Student Vault Processing
     -> 02_Conceitos/
     -> 03_Operacional/
     -> resumos/
     -> notas finais
```

Separacao de responsabilidades:

| Camada | Responsabilidade |
| --- | --- |
| E02 | transcricao bruta auditavel |
| E03 | reconstrucao didatica e extracao preliminar |
| chunking | reduzir carga e preservar semantica por unidade menor |
| merge final | recompor resposta publica unica |
| auditoria final | detectar suspeitas e preparar verificacao pontual por audio |
| Vault export | materializar artefatos no ambiente pessoal de estudo |
| Student Vault Processing | canonizar conhecimento e operacionalidade |

---

## 18. Proximos Passos Recomendados

### 18.1 Implementar merge canonico dos chunks

O runner atual nao faz merge final. Ele apenas processa cada chunk de forma independente e grava os resultados em `chunk_results.json`.

Definicao:

```text
merge canonico dos chunks =
  fusao deterministica dos chunks ja processados pela LLM
  em uma unica resposta final equivalente ao contrato publico da E03.
```

Portanto, o merge nao deve juntar novamente o texto bruto original. Ele deve juntar os produtos ja trabalhados pela LLM:

- `didactic_text` de cada chunk;
- `themes` de cada chunk;
- `technical_terms` de cada chunk;
- `technology_mentions` de cada chunk;
- `processing_notes` de cada chunk;
- metadados de origem do chunk, como `chunk_id`, segmentos e ordem na transcricao.

#### 18.1.1 Bancada experimental antes da imersao na E03

O merge canonico deve nascer primeiro como ferramenta de bancada, fora do contrato runtime da E03.

Justificativa:

- a fase atual ainda e de teste, pesquisa e benchmark;
- o objetivo imediato e descobrir a melhor forma de recompor os chunks processados;
- ajustes finos de merge provavelmente exigirao iteracoes rapidas;
- integrar cedo demais ao endpoint criaria atrito desnecessario com Spec, Plano e Tarefas;
- a burocracia SDD deve proteger contratos ja amadurecidos, nao dificultar experimentos ainda instaveis.

Decisao operacional:

```text
Primeiro criar e validar o merge como script experimental.
Depois, quando o resultado estiver satisfatorio, integrar a estrategia na E03.
```

Script sugerido:

```text
scripts/merge_e03_chunk_results.py
```

Status em `2026-06-12`:

```text
script criado em scripts/merge_e03_chunk_results.py
testes focados criados em tests/e03_processed_transcriptions/test_merge_e03_chunk_results.py
```

Entradas:

```text
.benchmarks/e03_chunk_postprocessing/[run]/chunk_results.json
raw_text original, quando necessario para lastro
metadados opcionais da aula
```

Saidas de bancada:

```text
.benchmarks/e03_chunk_merge/[run]/
  merged_result.json
  merged_public_result.json
  merged_didactic_text.md
  merge_audit.json
  README.md
```

Esse script deve ser livre para testar heuristicas, limiares, estrategias de deduplicacao e formatos de saida sem alterar o comportamento publico do endpoint.

Ultima rodada de bancada registrada:

```text
.benchmarks/e03_chunk_merge/20260612T113658Z_qwen35a3b-tfidf-9chunks-real-audited/
```

Resultado:

| Metrica | Valor |
| --- | ---: |
| `raw_text` | `67015` caracteres |
| `didactic_text` | `32032` caracteres |
| paragrafos | `24` |
| maior paragrafo | `1784` caracteres |
| headings Markdown no `didactic_text` | `0` |
| bullets no `didactic_text` | `0` |
| `themes` | `41` |
| `technical_terms` | `54` |
| `technology_mentions` | `46` |
| `processing_notes` | `34` |
| cobertura lexical critica | `19/20` |

Termo critico ainda ausente nominalmente:

```text
Eduardo
```

Interpretacao:

- o conteudo da discussao sobre NPS/RU foi preservado;
- a autoria nominal `Eduardo` ainda nao apareceu no merge final;
- isso deve entrar na auditoria de cobertura semantica, nao em reescrita global.

#### 18.1.2 Sequencia deterministica recomendada

A sequencia inicial do merge deve ser conservadora:

1. Ler `chunk_results.json`.
2. Filtrar apenas chunks com `status=pass`.
3. Ordenar chunks pela ordem original da transcricao, usando `first_segment_index`, `segment_indexes` ou a ordem ja preservada no arquivo.
4. Extrair o `didactic_text` de cada resposta.
5. Normalizar espacos, quebras de linha e paragrafos.
6. Remover duplicacoes obvias nas fronteiras entre chunks.
7. Concatenar os textos didaticos em ordem.
8. Consolidar `themes` por chave normalizada.
9. Consolidar `technical_terms` por termo normalizado.
10. Consolidar `technology_mentions` por nome normalizado.
11. Preservar referencias de origem por chunk.
12. Consolidar `processing_notes`.
13. Acrescentar nota tecnica informando que houve processamento chunk-by-chunk e merge deterministico.
14. Gerar uma resposta final unica no formato publico da E03.

Resultado esperado:

```json
{
  "raw_text": "...",
  "didactic_text": "...",
  "themes": [],
  "technical_terms": [],
  "technology_mentions": [],
  "processing_notes": [
    "O texto foi processado em chunks semanticos e fundido em ordem original.",
    "Itens repetidos entre chunks foram deduplicados por normalizacao textual."
  ]
}
```

#### 18.1.3 Nao repetir embeddings no merge inicial

O merge final nao deve repetir, por padrao, a etapa de embeddings ou proximidade semantica.

Motivo:

- embeddings foram uteis para dividir a transcricao bruta;
- o merge final tem outra funcao: recompor em ordem produtos ja processados;
- reagrupar novamente por similaridade semantica pode quebrar a progressao temporal da aula;
- em aulas, a ordem em que o professor e os alunos desenvolvem as ideias tambem e informacao relevante.

Regra:

```text
chunking pode usar proximidade semantica;
merge canonico deve priorizar ordem original, rastreabilidade e deduplicacao leve.
```

Embeddings podem ser avaliados depois apenas para deduplicacao auxiliar de listas, nunca para reordenar o texto didatico principal sem decisao especifica.

#### 18.1.4 Qualidade esperada do texto final

Ha alta probabilidade de o merge por codigo produzir texto final de boa qualidade no criterio mais importante da E03:

```text
fidelidade semantica > elegancia editorial
```

O codigo consegue garantir bem:

- ordem original dos chunks;
- preservacao do conteudo produzido por cada chamada LLM;
- reducao de duplicacoes obvias;
- consolidacao estavel das listas estruturadas;
- rastreabilidade por chunk;
- previsibilidade do resultado.

O codigo nao deve tentar ser autor literario. Ele nao deve reescrever livremente o conteudo para criar transicoes elegantes se isso introduzir risco de perda semantica.

Se for necessario um polimento posterior, ele deve ser uma etapa opcional, separada e validada, nunca requisito do primeiro merge canonico.

#### 18.1.5 Texto continuo nao significa bloco plano

A regra de evitar titulos artificiais precisa ser interpretada com cuidado.

O `didactic_text` da E03 deve ser um texto discursivo e continuo, mas isso nao significa produzir um bloco unico semelhante a arquivo `.txt` sem paragrafos, sem organizacao visual e sem respiracao textual.

Interpretacao correta:

```text
texto continuo =
  prosa didatica sequencial,
  organizada em paragrafos,
  sem headings inventados,
  sem secoes artificiais,
  sem topicos editoriais que nao existam no fluxo da aula.
```

Interpretacao incorreta:

```text
texto continuo =
  bloco unico sem paragrafos,
  sem quebras logicas,
  sem tabulacao visual minima,
  com perda de legibilidade.
```

Regras para o merge:

- preservar paragrafos produzidos pela LLM quando forem coerentes;
- inserir quebra de paragrafo entre chunks, quando necessario;
- remover titulos artificiais como `Introducao`, `Conclusao`, `Resumo`, `Topico 1` ou equivalentes, se nao forem parte real da aula;
- evitar listas dentro do `didactic_text`, salvo quando a lista fizer parte do conteudo explicado;
- nao compactar tudo em um unico paragrafo;
- nao inserir headings Markdown no texto didatico final;
- deixar organizacao enumerada para `themes`, `technical_terms` e `technology_mentions`, nao para o corpo discursivo principal.

Objetivo:

```text
evitar editorializacao artificial
sem sacrificar legibilidade didatica.
```

### 18.2 Implementar auditoria final por evidencias em bancada

Antes de integrar o chunking e o merge ao runtime da E03, e necessario criar tambem a etapa offline de auditoria final do texto resultante.

Definicao:

```text
auditoria final por evidencias =
  deteccao conservadora de termos, nomes ou ancoras suspeitas
  + localizacao dos trechos correspondentes na transcricao timestampada
  + preparacao de janelas curtas de audio
  + re-transcricao pontual futura
  + correcao somente quando houver evidencia suficiente.
```

Essa etapa nao deve funcionar como reescrita final por LLM. A LLM pode ajudar como auditora, mas nao como autora final do texto. O papel dela, quando usada, e marcar suspeitas em terminologia contratada. A decisao posterior deve ser lastreada por evidencias: transcricao segmentada, timestamp e, idealmente, novo STT sobre trecho curto de audio.

Script criado em `2026-06-12`:

```text
scripts/audit_e03_merged_result.py
```

Testes criados:

```text
tests/e03_processed_transcriptions/test_audit_e03_merged_result.py
```

Entradas:

```text
--merged-result-file
--transcription-json-file
--merge-audit-file
--audio-file, opcional
--issue-term, repetivel
--issue-terms-file, opcional
```

Saidas:

```text
.benchmarks/e03_final_audit/[run]/
  audit_issues.json
  README.md
  audio_clips/, quando --audio-file e --make-clips forem usados
```

Comportamento atual:

- identifica termos explicitamente suspeitos, como `NASA`;
- importa ancoras ausentes do `merge_audit.json`, como `Eduardo`;
- localiza ocorrencias nos segmentos da E02;
- calcula janelas de audio curtas por ocorrencia, com margem configuravel;
- evita criar um clipe gigante quando o mesmo termo aparece em momentos distantes;
- recorta WAVs quando o audio original e informado;
- re-transcreve cada clipe com o mesmo motor STT usado pela E02, quando `--transcribe-clips` e usado;
- grava transcricoes pontuais em `.txt` e `.json`;
- muda o status para `verified_by_clip_retranscription` quando o STT pontual confirma o termo;
- nao altera `didactic_text`, `themes`, `technical_terms` ou `technology_mentions`;

Rodada conservadora registrada:

```text
.benchmarks/e03_final_audit/20260612T115153Z_qwen35a3b-tfidf-9chunks-final-audit-v2/
```

Resultado:

| Item | Valor |
| --- | ---: |
| suspeitas | `2` |
| `needs_audio_verification` | `2` |
| clipes criados | `0`, porque nenhum audio original foi informado |

Suspeitas encontradas:

| Suspeita | Tipo | Segmentos | Janelas |
| --- | --- | ---: | ---: |
| `NASA` | possivel erro de transcricao | `2` | `2` |
| `Eduardo` | ancora de cobertura ausente no merge | `3` | `3` |

Interpretacao:

- `NASA` nao deve ser apagado por plausibilidade; deve ser verificado contra o audio, porque a propria transcricao aponta `Hackathon da Nasa` em Goiânia;
- `Eduardo` nao aparece no texto didatico final, mas aparece em tres pontos da transcricao bruta, exigindo decisao sobre autoria relevante;
- a proxima versao deve recortar o audio e reprocessar cada clipe com o mesmo motor de transcricao da E02.

Rodada agressiva opcional:

```text
.benchmarks/e03_final_audit/20260612T115208Z_qwen35a3b-tfidf-9chunks-final-audit-unconfirmed/
```

Resultado:

| Item | Valor |
| --- | ---: |
| suspeitas | `26` |
| `needs_audio_verification` | `2` |
| `not_found_in_segments` | `24` |

Conclusao da rodada agressiva:

```text
--include-unconfirmed-entities e util para investigacao,
mas e ruidoso demais para ser comportamento padrao.
```

Decisao:

- manter o padrao conservador;
- usar heuristicas agressivas apenas sob flag explicita;
- so integrar essa etapa ao runtime da E03 depois que o ciclo clipe -> re-transcricao -> proposta de correcao estiver validado em bancada.

Rodada com audio real e STT pontual:

```text
.benchmarks/e03_final_audit/20260612T120312Z_qwen35a3b-tfidf-9chunks-final-audit-audio-stt-v2/
```

Audio confirmado:

```text
/Users/adalbertobatista/Library/Mobile Documents/iCloud~md~obsidian/Documents/UFG_Pos_2/03_Audios/API/Rogerio-A1S2-2026-05-09.m4a
```

Confirmacao do audio:

- a duracao do arquivo e compativel com a transcricao tecnica da E02;
- o inicio do arquivo, re-transcrito pelo STT local, coincide com o inicio do bruto: referencia a Sandeco, Campus Party e espaco para expor startups;
- portanto, o audio usado na auditoria e o correspondente correto da transcricao `tr_20260611T190500Z_42f70772`.

Resultado final da rodada:

| Item | Valor |
| --- | ---: |
| suspeitas | `2` |
| `verified_by_clip_retranscription` | `2` |
| clipes WAV criados | `4` |
| re-transcricoes pontuais com sucesso | `4` |
| re-transcricoes pontuais com erro | `0` |

Conclusoes pontuais:

- `NASA`: confirmado pelo STT pontual no trecho sobre `Hackathon da NASA` em Goiania; nao deve ser eliminado por plausibilidade.
- `Eduardo`: confirmado pelo STT pontual em tres momentos; deve ser revisado como autoria ausente, especialmente na discussao sobre NPS.

Artefatos gerados:

```text
audit_issues.json
audio_clips/*.wav
clip_transcriptions/*.txt
clip_transcriptions/*.json
```

Interpretacao:

```text
O ciclo timestamp -> clipe -> STT pontual -> conclusao auditavel funcionou.
```

Isso valida a arquitetura da auditoria final como bancada experimental. A etapa ainda nao corrige automaticamente o texto final, mas ja produz evidencia suficiente para decidir correcoes pontuais sem reescrita global por LLM.

Rodada completa em segunda aula:

```text
audio: Rogerio-A1S1-2026-05-09.m4a
transcricao: tr_20260612T130204Z_e7aebe3c
chunking: .benchmarks/e03_semantic_chunks/20260612T130209Z_e03-a1s1-tfidf-baseline-v2/
processamento chunk-by-chunk: .benchmarks/e03_chunk_postprocessing/20260612T130215Z_qwen35a3b-a1s1-tfidf-9chunks-real/
merge: .benchmarks/e03_chunk_merge/20260612T130928Z_qwen35a3b-a1s1-tfidf-9chunks-real-audited/
auditoria final: .benchmarks/e03_final_audit/20260612T131303Z_qwen35a3b-a1s1-final-audit-rare-acronyms-v3/
```

Resultado da transcricao bruta:

| Item | Valor |
| --- | ---: |
| duracao | `4933.06s` |
| caracteres | `64843` |
| segmentos | `2439` |

Resultado do chunking:

| Item | Valor |
| --- | ---: |
| segmentos iniciais | `74` |
| chunks TF-IDF | `9` |
| menor chunk | `653` tokens estimados |
| maior chunk | `3197` tokens estimados |
| media | `1803.11` tokens estimados |

Resultado E03 chunk-by-chunk:

| Item | Valor |
| --- | ---: |
| chunks | `9` |
| aprovados | `9` |
| erros | `0` |
| tempo total | `426.689s` |
| texto didatico somado | `31179` caracteres |
| temas | `46` |
| termos tecnicos | `75` |
| tecnologias | `62` |

Resultado do merge:

| Item | Valor |
| --- | ---: |
| `raw_text` | `64842` caracteres |
| `didactic_text` | `31209` caracteres |
| paragrafos | `23` |
| maior paragrafo | `1792` caracteres |
| headings Markdown | `0` |
| bullets | `0` |
| temas | `46` |
| termos tecnicos | `58` |
| tecnologias | `39` |
| notas | `36` |

Resultado da auditoria final:

| Item | Valor |
| --- | ---: |
| suspeitas | `12` |
| confirmadas por re-STT pontual | `11` |
| nao confirmadas por re-STT pontual | `1` |
| clipes criados | `21` |
| re-transcricoes com sucesso | `21` |
| re-transcricoes com erro | `0` |

Conclusoes da politica de suspeitas:

- a politica generica de siglas raras funcionou fora do caso `NASA`;
- numeros puros foram removidos da politica por gerarem ruido;
- casos como `CIGA`, `UFNDE`, `IAC`, `EPT` e `GROC` exigem camada de grafia canonica provavel;
- `ICTI` nao foi confirmado pelo re-STT pontual e deve ser tratado como provavel erro de transcricao ou revisao manual;
- a auditoria pos-merge funciona, mas a pre-auditoria antes do Qwen passa a ser recomendada.

Grafias canonicas candidatas identificadas:

| Forma suspeita | Candidato canonico |
| --- | --- |
| `CIGA` | `SIGAA` |
| `UFNDE` | `FNDE` |
| `IAC` | `IaC` |
| `EPT` | `GPT` ou `ChatGPT` |
| `GROC` | `Groq` |

Decisao derivada da segunda aula:

```text
Nao integrar ainda diretamente no E02/E03.
Antes, implementar a pre-auditoria offline da transcricao bruta
e reaproveitar a mesma logica de clipe + re-STT pontual
antes do processamento pelo Qwen.
```

### 18.3 Implementar pre-auditoria offline da transcricao bruta

Nova etapa recomendada antes da integracao:

```text
scripts/audit_e02_raw_transcription.py
```

Objetivo:

- ler o JSON tecnico da E02;
- detectar siglas raras, grafias canonicas provaveis e termos tecnicos suspeitos;
- recortar os trechos de audio;
- re-transcrever pontualmente;
- gerar um `raw_transcription_audit.json`;
- gerar um `raw_text_for_qwen.txt` com anotacoes/correcoes controladas, sem apagar o bruto original.

Essa etapa responde ao risco de entregar ao Qwen uma transcricao com ruido lexical capaz de induzir interpretacoes incorretas.

Rodada validada em bancada:

```text
audio: Rogerio-A1S1-2026-05-09.m4a
transcricao E02: outputs/transcriptions/2026-05-09-aula-1-sessao-1-a1s1_tr_20260612T130204Z_e7aebe3c.json
pre-auditoria: .benchmarks/e02_raw_pre_audit/20260612T133316Z_a1s1-pre-qwen-raw-audit-v3/
chunking: .benchmarks/e03_semantic_chunks/20260612T133402Z_e03-a1s1-preaudited-v3-tfidf/
processamento Qwen: .benchmarks/e03_chunk_postprocessing/20260612T133408Z_qwen35a3b-a1s1-preaudited-v3-tfidf-9chunks-real/
merge: .benchmarks/e03_chunk_merge/20260612T134116Z_qwen35a3b-a1s1-preaudited-v3-tfidf-9chunks-real-audited/
auditoria final: .benchmarks/e03_final_audit/20260612T134324Z_qwen35a3b-a1s1-preaudited-v3-final-audit-scopefix/
```

Resultado da pre-auditoria:

| Item | Valor |
| --- | ---: |
| suspeitas | `11` |
| substituicoes canonicas prontas | `5` |
| substituicao pronta por nao confirmacao | `1` |
| confirmadas no audio e preservadas | `4` |
| nao confirmadas e nao corrigidas automaticamente | `1` |
| clipes criados | `31` |
| re-transcricoes pontuais com sucesso | `31` |
| re-transcricoes pontuais com erro | `0` |
| substituicoes aplicadas ao `raw_text_for_qwen.txt` | `6` |

Substituicoes canonicas aplicadas antes do Qwen:

| Forma suspeita | Forma entregue ao Qwen | Status |
| --- | --- | --- |
| `CIGA` | `SIGAA` | `canonical_replacement_ready` |
| `UFNDE` | `FNDE` | `canonical_replacement_ready` |
| `IAC` | `IaC` | `canonical_replacement_ready` |
| `ICTI` | `TI` | `canonical_replacement_ready_from_nonconfirmation` |
| `EPT` | `ChatGPT` | `canonical_replacement_ready` |
| `GROC` | `Groq` | `canonical_replacement_ready` |

Importante:

```text
Essas substituicoes foram implementadas como politica sistemica da pre-auditoria,
nao como ancora privada da transcricao A1S1.
```

A aplicacao continua rastreavel: cada substituicao aparece em `raw_transcription_audit.json`, com `issue_id`, `status`, candidato canonico, contagem, clipes e re-STT pontual quando executado. A transcricao bruta original permanece preservada; o arquivo saneado para o Qwen e um derivado operacional.

Resultado do processamento Qwen sobre o texto pre-auditado v3:

| Item | Valor |
| --- | ---: |
| chunks | `9` |
| aprovados | `9` |
| erros | `0` |
| tempo total | `419.584s` |
| texto didatico somado | `31282` caracteres |
| temas | `44` |
| termos tecnicos | `76` |
| tecnologias | `59` |

Resultado do merge canonico v3:

| Item | Valor |
| --- | ---: |
| `didactic_text` | `31310` caracteres |
| paragrafos | `21` |
| maior paragrafo | `1779` caracteres |
| headings Markdown | `0` |
| bullets | `0` |
| coverage anchors checadas | `0` nesta rodada |

Resultado da auditoria final v3:

| Item | Valor |
| --- | ---: |
| issues finais | `0` |
| clipes finais necessarios | `0` |
| status counts | `{}` |

A primeira execucao da auditoria final v3 ainda apontou `GMI`, `PNI` e `AI`, mas a inspecao mostrou que essas ocorrencias estavam apenas em `processing_notes`, nao no `didactic_text`, `themes`, `technical_terms` ou `technology_mentions`. A politica de siglas raras foi entao corrigida para auditar apenas artefatos semanticos entregaveis. As `processing_notes` permanecem preservadas como rastreabilidade interna, mas nao devem gerar alarme automatico de conteudo.

Decisao consolidada:

```text
O pipeline correto tem duas portas de qualidade:

1. pre-auditoria da transcricao bruta antes do Qwen;
2. auditoria final dos artefatos semanticos depois do merge canonico.
```

Essa decisao evita que ruido lexical contamine a inferencia do Qwen e evita que notas internas de processamento sejam confundidas com conteudo didatico final.

### 18.3.1 Contexto de pre-auditoria no prompt do Qwen

Apos a validacao da pre-auditoria, foi identificado um requisito adicional: o Qwen precisa saber que recebeu um texto ja auditado. Sem essa informacao, o modelo pode tentar inferir novamente suspeitas ja resolvidas, gerar notas de incerteza desnecessarias ou tratar grafias canonicas como se ainda fossem duvidosas.

Decisao implementada em bancada:

```text
scripts/process_e03_semantic_chunks.py
  --pre-audit-file raw_transcription_audit.json
```

Quando esse arquivo e informado, o runner injeta antes de cada chunk um bloco delimitado:

```text
<<< Mindvox pre-audit context >>>
...
<<< End Mindvox pre-audit context >>>
```

Esse bloco e metadado operacional, nao conteudo de aula. Ele informa:

- quantidade de suspeitas analisadas;
- contagens por status;
- substituicoes canonicas aplicadas antes do Qwen;
- existencia ou inexistencia de suspeitas remanescentes.

Regra refinada:

```text
Se nao houver suspeitas remanescentes,
o Qwen deve tratar o corpo da transcricao como a melhor evidencia textual disponivel
e nao deve criar novas incertezas por plausibilidade.

Se houver suspeitas remanescentes,
elas nao sao conteudo verificado.
O Qwen nao deve promove-las a didactic_text, themes, technical_terms ou technology_mentions
sem evidencia semantica independente no corpo da transcricao.
No maximo, devem aparecer em processing_notes.
```

Smoke test executado:

```text
.benchmarks/e03_chunk_postprocessing/20260612T135112Z_qwen35a3b-a1s1-preaudit-context-smoke-v2/
```

Resultado:

| Item | Valor |
| --- | ---: |
| chunks testados | `1` |
| aprovados | `1` |
| erros | `0` |
| tempo | `44.615s` |
| suspeita remanescente `PNI` em campos principais | `0` |
| suspeita remanescente `PNI` em `processing_notes` | `sim` |

Conclusao:

```text
O Qwen agora recebe contexto operacional suficiente para distinguir:
1. grafias ja normalizadas e confiaveis;
2. transcricao pre-auditada sem suspeitas remanescentes;
3. termos ainda suspeitos, que nao devem ser promovidos a conteudo final.
```

### 18.4 Integrar chunking como estrategia interna opcional da E03

Nao iniciar como substituicao invisivel sem teste.

Pre-condicao:

```text
Integrar ao endpoint somente depois que o merge canonico experimental
e a auditoria final por evidencias produzirem resultados satisfatorios em bancada.
```

Proposta:

- manter fluxo atual para textos curtos;
- ativar chunking quando entrada ultrapassar limite configurado;
- criar variavel de configuracao para estrategia:

```text
MINDVOX_POSTPROCESSING_CHUNKING_MODE=off|tfidf
```

### 18.5 Criar exportador experimental para Vault

Script sugerido:

```text
scripts/build_student_vault_update_plan.py
```

Modo inicial:

```text
draft
```

Saidas:

```text
.benchmarks/student_vault_update_plan/[run]/
  update_plan.json
  update_plan.md
```

Regra:

```text
Nao escrever diretamente no Vault na primeira versao.
Gerar plano auditavel primeiro.
```

### 18.6 Criar modo apply seguro

Somente depois do plano aprovado.

Operacoes seguras:

- criar `brutos/transcricoes-auditaveis/`;
- criar `textos-didaticos/`;
- escrever arquivos definitivos de `raw_text` e `didactic_text`;
- inserir candidatos preliminares na inbox com marcador explicito.

### 18.7 Fazer auditoria humana de cobertura

Usar Gemini, outro LLM forte ou revisao humana para comparar:

- transcricao bruta;
- saida monolitica antiga;
- saida chunk-by-chunk;
- saida final mergeada.

Critico:

- verificar nao apenas topicos, mas autoria, exemplos, casos empiricos e discussoes de alunos.

---

## 18.5 Refinamento apos prova longa EGI S02

Em `2026-06-14`, a E03 foi exercitada com transcricao longa de
`Introducao ao Gerenciamento de Projetos`, sessao `S02`, com aproximadamente
`176` minutos, `5362` segmentos, `131093` caracteres e `23471` palavras.

A execucao inicial nao indicou falta de contexto do `llama-server` nem limite
primario de `MINDVOX_LLM_MAX_OUTPUT_TOKENS`. O `runtime_snapshot` mostrou
chunking TF-IDF ativo, `17` chunks e nenhum chunk acima do alvo estimado. A
falha observada foi mais precisa:

- a validacao monolitica de cobertura semantica estava sendo aplicada a chunk
  individual;
- um chunk administrativo, sobre lista de presenca, squads, Discord/Classroom,
  papeis e entregas, ultrapassou levemente `20000` caracteres e recebeu minimo
  monolitico de tamanho, temas e ancoras;
- palavras discursivas capitalizadas, como `Então`, `Acho`, `Alguém` e
  `Temos`, podiam ser promovidas indevidamente a ancoras protegidas;
- ruido repetitivo de STT, como sequencias longas de `ste` e `os`, degradava o
  texto entregue ao LLM sem acrescentar semantica.

Correcao consolidada:

- chunks individuais agora usam prompt local sem a regua monolitica completa;
- a validacao bloqueante de cobertura semantica fica no merge canonico final;
- a pre-auditoria remove ruido repetitivo apenas do texto interno enviado ao
  LLM, preservando o `raw_text` publico;
- a politica de ancoras ignora palavras capitalizadas de discurso comum sem
  evidencia semantica real;
- se o merge final ainda for reprovado, a saida rejeitada fica em quarentena
  com `runtime_snapshot` e artefatos humanos para auditoria.

Essa prova mudou a interpretacao tecnica do problema: o erro nao era
principalmente "audio grande demais", mas sim um conflito entre granularidade de
chunk e regua de cobertura desenhada para transcriptos completos.

---

## 19. Riscos Abertos

| Risco | Situacao | Mitigacao |
| --- | --- | --- |
| perda semantica residual | ainda possivel | validacao por ancoras + chunking + auditoria |
| duplicacao entre chunks | esperada | merge/deduplicacao final |
| fragmentacao excessiva | possivel com thresholds altos | manter TF-IDF v2 como baseline |
| dependencia de Qwen local | aceitavel localmente | manter provider/contract modes |
| exportacao indevida para Vault | risco de poluir notas canonicas | iniciar por plano `draft` |
| confusao entre contrato API e Vault | risco arquitetural | manter Vault como segunda destinacao opcional |
| nome proprio omitido | observado com Eduardo | checagem de autoria como criterio de qualidade |
| regua errada por granularidade | validacao de transcrito inteiro pode punir chunk administrativo | manter regua monolitica apenas no merge final |
| texto didatico em bloco plano | risco de confundir texto continuo com `.txt` sem paragrafos | exigir prosa continua com paragrafos e sem headings artificiais |
| correcao por plausibilidade | risco de apagar termo correto, como `NASA` | exigir timestamp, clipe e re-transcricao pontual antes de corrigir |
| heuristica agressiva de suspeitas | gera muito ruido | manter sob flag explicita, fora do padrao conservador |

---

## 20. Decisoes Consolidadas

1. A E03 continua sendo endpoint publico de IA textual.
2. O contrato publico da E03 continua independente do Vault.
3. As cinco entregas principais continuam sendo `raw_text`, `didactic_text`, `themes`, `technical_terms` e `technology_mentions`.
4. `processing_notes` permanece como campo auxiliar.
5. Qwen 35B-A3B Q8 continua como modelo local preferencial.
6. LongWriter GLM4 9B Q8 esta descartado sob o contrato atual.
7. A estrategia mais promissora e chunking semantico + processamento chunk-by-chunk.
8. TF-IDF baseline v2 e o default experimental inicial.
9. Bertimbau centered permanece como linha secundaria de pesquisa.
10. O merge canonico dos chunks nasceu primeiro como script experimental e foi integrado ao runtime da E03 apos resultado satisfatorio em bancada.
11. O fluxo chunked da E03 deve aplicar regua bloqueante de cobertura apenas ao merge final, nao a cada chunk isolado.
12. O `didactic_text` final deve ser prosa continua organizada em paragrafos, sem headings artificiais e sem virar bloco plano.
13. O `didactic_text` longo deve ir para pasta definitiva no Vault, nao para inbox.
14. O `raw_text` integral deve ir para subpasta propria dentro de `brutos/`, como transcricao auditavel.
15. Temas, termos, tecnologias e ancoras devem entrar na inbox apenas como material preliminar.
16. O processamento final do Vault deve ser uma segunda etapa, guiada pelo Student Vault.
17. A primeira escrita no Vault deve ser precedida por plano auditavel.
18. A auditoria final por evidencias deve nascer em bancada, fora da E03.
19. A auditoria final nao deve reescrever globalmente o texto; deve apenas localizar suspeitas, preparar evidencias e permitir correcao pontual.
20. Nenhum termo suspeito deve ser eliminado por plausibilidade sem timestamp e evidencia sonora ou textual suficiente.

---

## 21. Conclusao

O achado central desta fase e que o problema da E03 nao se resolve apenas escolhendo outro modelo.

O Qwen 35B-A3B Q8 continua sendo o melhor motor local observado, mas precisa receber a tarefa em unidades menores e semanticamente mais estaveis. O chunking tematico por codigo transformou o comportamento do sistema: reduziu falhas estruturais, preservou mais topicos criticos e abriu caminho para um pipeline mais confiavel.

O desenho final separa tres responsabilidades que antes tendiam a se misturar:

```text
Mindvox API
  -> entrega artefatos ao cliente do endpoint

Mindvox outputs
  -> preserva evidencias e resultados locais demonstraveis

Student Vault
  -> organiza o material no ambiente pessoal de estudo
```

Essa separacao preserva o valor academico do endpoint, protege a rastreabilidade da transcricao e permite que o Vault receba material ja enriquecido sem se tornar dependencia da API.

Portanto, a fase atual ja consolidou o merge canonico dos chunks dentro do runtime da E03. A proxima validacao deve se concentrar em provas reais longas, especialmente aulas acima de duas horas, conferindo se a regua final identifica resumo editorial sem punir chunks administrativos ou material legitimamente compacto. Em paralelo, pode ser criado o exportador experimental para o Student Vault em modo `draft`, sem escrita direta inicial no Vault.
Antes dessa integracao, entretanto, deve-se concluir tambem a auditoria final por evidencias: detectar suspeitas no resultado mesclado, localizar timestamps na transcricao tecnica, recortar audio quando disponivel e reprocessar pontualmente os trechos duvidosos. Essa etapa fecha o ciclo de qualidade sem transformar a LLM em reescritora final.
