# Relatorio Tecnico: Benchmark e Decisao do Motor LLM da E03

## 1. Identificacao

- `Tipo`: Relatorio tecnico circunstanciado
- `Status`: orientador para E03
- `Data`: 2026-06-10
- `Escopo`: registrar testes reais de modelos LLM locais para o pos-processamento da E03
- `Endpoint relacionado`: `POST /processed-transcriptions/v1.0.0`
- `Documentos relacionados`:
  - `docs/sdd/specs/E03_ENDPOINT_PROCESSED_TRANSCRIPTIONS.md`
  - `docs/sdd/reports/RELATORIO_DIRETRIZES_E03_SERVICO_IA_LLM.md`
  - `docs/sdd/reports/RELATORIO_ARQUITETURA_E_ESCOPO_E03_E05.md`
  - `scripts/benchmark_e03_models.py`

---

## 2. Finalidade

Este relatorio registra a avaliacao real de modelos LLM locais candidatos ao motor de pos-processamento da E03.

O objetivo nao foi medir modelos em abstrato, mas verificar qual deles atende melhor ao caso real do Mindvox:

```text
transcricao bruta longa de aula
  -> pos-processamento textual
  -> texto semanticamente util
  -> temas
  -> termos tecnicos
  -> tecnologias citadas
  -> notas de processamento
```

A entrada usada foi a transcricao bruta real produzida pela E02 durante prova manual:

```text
transcription_id: tr_20260609T154710Z_35969e23
engine: mlx-whisper
model: mlx-community/whisper-large-v3-turbo-fp16
input_chars: 42.998
```

O arquivo de evidencia operacional foi mantido em `.benchmarks/`, que e pasta local ignorada pelo Git, pois contem saidas de teste e pode conter texto real de aula.

---

## 3. Ambiente de Teste

Os testes locais foram executados com `llama.cpp` via `llama-server`, usando endpoint compativel com a API OpenAI.

Configuracao comum:

```text
ctx-size: 32768
parallel: 1
flash-attn: auto
reasoning: off
host: 127.0.0.1
```

O modo `reasoning off` foi usado porque a E03 precisa de uma resposta final estruturada, nao de exposicao de raciocinio interno.

Decisao operacional posterior ao benchmark:

- o benchmark inicial acima mediu candidatos com `ctx-size 32768`;
- a configuracao local padrao final da E03 foi elevada para `ctx-size 65536`, `parallel 1`, `MINDVOX_LLM_MAX_OUTPUT_TOKENS=20000` e `MINDVOX_LLM_TIMEOUT_SECONDS=1200`;
- a elevacao decorre de calculo sobre transcricao real de aula, projetada para aproximadamente duas horas, com prioridade de preservacao semantica;
- o GGUF local selecionado declara janela maxima de `262144` tokens, portanto `65536` permanece abaixo da janela maxima do modelo.

O benchmark foi registrado por script proprio:

```text
scripts/benchmark_e03_models.py
```

Esse script mede tempo total, validade do JSON, presenca de campos minimos, tamanho da entrada, tamanho da saida, quantidade de temas, quantidade de termos tecnicos e quantidade de tecnologias citadas.

---

## 4. Modelos Avaliados

Foram avaliados os seguintes candidatos locais:

| Modelo | Arquivo local | Papel no teste |
| --- | --- | --- |
| Gemma 4 12B Q8 | `gemma-4-12b-it-Q8_0.gguf` | Candidato atualizado e menor |
| Qwen 3.6 27B Q8 | `Qwen3.6-27B-MTP-Q8_0.gguf` | Baseline local maior ja instalado |
| Qwen 3.6 35B-A3B Q8 | `Qwen3.6-35B-A3B-MTP-Q8.gguf` | Candidato MoE/A3B local |

Observacao:

- `A3B` indica que o modelo possui arquitetura de mistura de especialistas e ativa apenas parte dos parametros por passo;
- por isso, mesmo tendo arquivo maior, ele pode entregar geracao mais rapida que um modelo denso menor ou equivalente.

---

## 5. Resultado Comparativo Principal

Todos os modelos abaixo foram testados com a mesma transcricao bruta real da E02.

| Modelo | Status | Tempo total | Caracteres de saida | Temas | Termos tecnicos |
| --- | --- | ---: | ---: | ---: | ---: |
| Gemma 4 12B Q8 | passou | `77,26s` | `7.144` | `4` | `8` |
| Qwen 3.6 27B Q8 | passou | `188,46s` | `7.840` | `5` | `8` |
| Qwen 3.6 35B-A3B Q8 | passou | `55,83s` | `11.426` | `6` | `10` |

Resultado de velocidade observado em servidor:

| Modelo | Leitura do prompt | Geracao da resposta |
| --- | ---: | ---: |
| Gemma 4 12B Q8 | nao registrado neste relatorio para o caso integral | cerca de `33 tokens/s` em teste anterior |
| Qwen 3.6 27B Q8 | `226,59 tokens/s` | `13,66 tokens/s` |
| Qwen 3.6 35B-A3B Q8 | `1.102,87 tokens/s` | `62,12 tokens/s` |

Conclusao da comparacao:

- o Qwen 3.6 35B-A3B Q8 foi o melhor em tempo total;
- foi o melhor em taxa de geracao;
- produziu a saida estruturada mais rica;
- preservou cobertura tematica ampla;
- tornou-se o candidato local preferencial para a E03.

---

## 6. Qualidade Semantica da Saida Vencedora

A saida do Qwen 3.6 35B-A3B Q8 identificou e organizou temas centrais da aula:

- fundamentos e evolucao das APIs;
- arquitetura de microservicos versus arquitetura monolitica;
- REST, JSON, HTTP e metodos;
- SOAP/XML;
- GraphQL;
- gRPC;
- escalabilidade, custos e uso de GPU;
- API First;
- dependencia externa;
- logs, versionamento e perenidade;
- seguranca e LGPD;
- automacao, RPA, CAPTCHA, Playwright, Selenium e OpenAI Vision;
- Cloudflare, CNJ e indisponibilidade de servicos externos.

Tambem corrigiu artefatos relevantes da transcricao bruta:

- `SOP` para `SOAP`;
- `GRASH` para `REST`;
- `Selenia` para `Selenium`;
- `PlayWard` para `Playwright`;
- `2Capt` para `2Captcha`;
- `CloudFair` para `Cloudflare`;
- `Chat APT` para `ChatGPT`.

Essa correcao e relevante porque a E03 nao deve apenas encurtar texto. Ela deve transformar uma transcricao bruta em material didatico mais util e mais confiavel.

---

## 7. Teste da Versao Fiel e Integral

Apos o primeiro benchmark, foi levantada a hipotese de incluir na E03 uma segunda saida chamada `corrected_full_text`, mais fiel e quase integral.

Foram feitos dois testes adicionais:

1. `corrected_full_text` como string longa.
2. `corrected_full_text_paragraphs` como lista de paragrafos.

O primeiro teste gerou texto longo, mas falhou como JSON valido por problema de estrutura em string extensa.

O segundo teste foi tecnicamente valido:

| Saida | Tamanho | Tempo total |
| --- | ---: | ---: |
| Transcricao bruta E02 | `42.998` caracteres | ja existente |
| `corrected_full_text_paragraphs` | `42.892` caracteres | `225,00s` |
| texto didatico processado do mesmo teste | `2.846` caracteres | incluido no mesmo processamento |

Taxa observada nesse teste:

```text
prompt eval: 1.157,19 tokens/s
eval: 59,37 tokens/s
total: 224,91s
```

Conclusao:

- a versao fiel e quase integral praticamente replica o tamanho da transcricao bruta;
- o custo de processamento e muito maior;
- ela nao acrescenta valor proporcional ao que a E02 ja preserva;
- ela cria risco de duplicidade conceitual entre E02 e E03;
- a transcricao bruta da E02 ja e o melhor lastro de auditoria e conferencia.

---

## 8. Decisao Sobre Saidas Processadas

A decisao tecnica recomendada e que a E03 produza saidas processadas didaticas e semanticamente organizadas, removendo apenas redundancia semantica e ruido de fala, e nao uma segunda transcricao quase integral.

Motivo:

Aulas contem muita redundancia semantica:

- repeticoes naturais do professor;
- retomadas de pontos ja explicados;
- perguntas de alunos que voltam ao mesmo nucleo de sentido;
- interrupcoes;
- hesitacoes;
- exemplos repetidos;
- ajustes de fala;
- marcas conversacionais sem valor informacional.

Portanto, uma saida menor nao e necessariamente uma perda. No caso testado, ela representa um enxugamento semantico: remove redundancias e conserva os nucleos de sentido relevantes.

Comparacao:

| Versao | Tamanho | Funcao |
| --- | ---: | --- |
| `raw_text` da E02 | `42.998` caracteres | prova bruta do que foi ouvido |
| `corrected_full_text_paragraphs` | `42.892` caracteres | quase duplicacao da prova bruta |
| texto didatico estruturado do E03 vencedor | `5.091` caracteres no texto discursivo; `10.853` caracteres com estrutura completa | produto didatico pos-processado |

A checagem semantica nao indicou perda relevante dos conceitos principais.

Assim, a E03 deve entregar:

- `raw_text`, para rastreabilidade e conferencia;
- `didactic_text`, como texto discursivo, sequencial, logico, didatico e semanticamente enxuto;
- `themes`, como mapa tematico estruturado para estudo e futura ingestao pela E04;
- `technical_terms`, para normalizacao tecnica;
- `technology_mentions`, para listar tecnologias, ferramentas, frameworks, plataformas, bibliotecas, servicos, APIs e providers citados na aula;
- `processing_notes`, para registrar correcoes, incertezas e cuidados.

A E03 nao deve entregar, por padrao, um `corrected_full_text` quase integral.

Se o usuario quiser conferir se houve perda ou distorcao, deve comparar o resultado processado com o `raw_text` preservado pela E02 ou retornado pela propria E03 quando a entrada passar por audio.

---

## 9. Decisao Recomendada

Modelo local preferencial para E03:

```text
Qwen3.6-35B-A3B-MTP-Q8.gguf
```

Nome operacional recomendado:

```text
qwen35a3b-q8
```

Papel:

- motor local preferencial para pos-processamento real da E03;
- escolhido por resultado demonstravel em transcricao real longa;
- configuravel por variaveis de ambiente;
- substituivel sem alterar o contrato HTTP.

Modelos que perderam:

- `Gemma 4 12B Q8`: bom candidato, mas perdeu em tempo total, riqueza da estrutura e taxa de geracao observada;
- `Qwen 3.6 27B Q8`: perdeu principalmente por velocidade de geracao muito inferior no teste real integral.

Modelo descartado posteriormente:

- `LongWriter-glm4-9B-Q8_0.gguf`: descartado em `2026-06-11` para uso na E03 sob o contrato atual.

Motivo do descarte:

- o modelo foi carregado com sucesso em `llama.cpp`/`llama-server`;
- a janela de contexto operacional de `65536` tokens foi aceita;
- o teste real recebeu uma transcricao de `67015` caracteres, com prompt de aproximadamente `19902` tokens;
- a geracao longa levou aproximadamente `876,64s`;
- o modelo gerou `20000` tokens, atingindo o teto configurado;
- a saida nao foi JSON valido;
- os campos publicos obrigatorios da E03 nao ficaram recuperaveis;
- a validacao de cobertura semantica nao pode ser aplicada porque a resposta falhou antes, no contrato estrutural;
- um diagnostico curto, sem transcricao longa, tambem retornou Markdown/fences em vez de JSON valido mesmo com `response_format: {"type": "json_object"}`.

Decisao:

- nao manter o arquivo local desse modelo;
- nao manter artefatos de benchmark desse modelo;
- nao repetir o teste do `LongWriter-glm4-9B-Q8_0.gguf` como candidato E03 enquanto o contrato exigir JSON estruturado via endpoint OpenAI-compatible do `llama-server`;
- eventual teste futuro de variantes GLM/LongWriter so deve ser considerado se houver mudanca material de metodo, como gramatica/schema forçada no `llama.cpp`, outro runtime comprovadamente aderente a JSON estruturado, ou evidencia externa forte de compatibilidade com saida JSON estrita.

Decisao prudente:

- manter suporte generico a modelo local via `llama-server`;
- documentar Qwen 35B-A3B Q8 como preferencial;
- manter provider externo como opcao de portabilidade;
- nao acoplar a Spec ao path local da maquina do autor;
- nao registrar chaves, prompts integrais ou transcricoes integrais em logs.

---

## 10. Consequencias para a Spec E03

A Spec E03 deve ser interpretada assim:

- E02 entrega transcricao bruta;
- E03 entrega pos-processamento semantico;
- a E03 possui cinco entregas publicas: `raw_text`, `didactic_text`, `themes`, `technical_terms` e `technology_mentions`;
- `didactic_text`, `themes`, `technical_terms` e `technology_mentions` sao produtos processados;
- `raw_text` continua preservado para rastreabilidade;
- o modelo preferencial local passa a ser `Qwen3.6-35B-A3B-MTP-Q8.gguf`;
- `corrected_full_text` quase integral nao deve ser requisito padrao do MVP;
- qualquer perfil futuro que produza revisao integral deve ser opcional e expressamente separado do perfil `study_notes`.

---

## 11. Conclusao

Os testes demonstraram que o Qwen 3.6 35B-A3B Q8 e o melhor candidato local atual para a E03.

A decisao mais pragmatica para o Mindvox e usar a E03 como motor de enxugamento semantico e organizacao didatica, nao como segundo transcritor.

Essa decisao fortalece a arquitetura:

- E02 preserva o bruto;
- E03 transforma o bruto em conhecimento organizado;
- E04 futuramente ingere esse conhecimento em memoria relacional e vetorial;
- E05 futuramente recupera informacao dessa memoria.

Com isso, o Mindvox evita duplicidade, reduz custo operacional e entrega um resultado mais util para aulas longas.
