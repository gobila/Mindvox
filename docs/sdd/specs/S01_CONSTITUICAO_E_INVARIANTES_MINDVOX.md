# Spec S01: Constituicao e Invariantes do Mindvox

## 1. Identificacao

- `ID`: `S01`
- `Tipo`: `Spec`
- `Status`: `fechada`
- `Escopo`: principios constitutivos, invariantes de projeto e limites do MVP do Mindvox
- `Documentos de origem`: `README.md`, `docs/mindvox_mentoring_agreement.md`

---

## 2. Finalidade

Esta Spec fixa os principios que governam o Mindvox durante sua construcao.

Ela existe para:

- impedir que o projeto se desvie de seu objetivo central;
- separar o MVP das ambicoes futuras;
- preservar a abordagem API First;
- proteger dados sensiveis, arquivos de audio, transcricoes e configuracoes privadas;
- orientar as Specs posteriores de endpoints;
- manter o trabalho simples, funcional, testavel, documentado e explicavel.

---

## 3. Escopo

Esta Spec cobre:

- objetivo central do Mindvox;
- escopo do MVP;
- relacao entre Mindvox, FastAPI e API First;
- regra de desenvolvimento por Specs;
- regra de completude por endpoint;
- prioridade entre seguranca, eficiencia e custo;
- tratamento de dados sensiveis;
- independencia operacional em relacao ao Atrium;
- uso de inspiracao tecnica de N02 e N04;
- documentacao, verificacao e explicabilidade como requisitos do projeto.

Esta Spec nao cobre:

- contrato detalhado de cada endpoint;
- escolha final de modelos STT, embeddings ou busca;
- estrutura final do banco de dados;
- implementacao concreta dos routers, schemas, services e testes;
- interface grafica;
- TTS;
- streaming;
- speech-to-speech.

Esses temas pertencem a Specs posteriores, notas tecnicas ou decisoes explicitas de escopo.

---

## 4. Regra de Precedencia

No escopo do Mindvox, esta Spec prevalece sobre:

- escolhas tecnicas locais;
- conveniencias de implementacao;
- ideias exploratorias ainda nao aprovadas;
- materiais historicos ou rascunhos que contrariem seus invariantes.

O `README.md` e o documento publico de apresentacao e execucao do projeto.

O `docs/mindvox_mentoring_agreement.md` preserva o acordo didatico e operacional entre autor/desenvolvedor humano e o assistente LLM.

As Specs de endpoints devem obedecer a esta S01.

Se houver conflito entre uma Spec de endpoint e esta Spec, a Spec de endpoint deve ser corrigida ou a S01 deve ser revisada explicitamente antes.

---

## 5. Definicoes Normativas

Para fins desta Spec:

- `Mindvox` e a API em FastAPI destinada a transformar aulas gravadas em memoria consultavel;
- `MVP` e a primeira versao funcional, demonstravel e explicavel do projeto;
- `API First` significa tratar contratos HTTP, entradas, respostas, erros, validacoes e documentacao como elementos centrais do projeto;
- `STT` significa Speech-to-Text, isto e, transformar fala em texto;
- `TTS` significa Text-to-Speech, isto e, transformar texto em fala;
- `speech-to-speech` significa receber fala e devolver fala como resposta;
- `nano-space` e o espaco isolado de memoria usado para impedir mistura entre memorias de origens diferentes;
- `projeto_mindvox` e o nano-space canonico do Mindvox;
- `dados sensiveis` incluem audios, transcricoes, metadados de aula, chaves, tokens, configuracoes privadas e qualquer dado que possa identificar pessoas, contextos ou conteudo academico privado;
- `Spec de endpoint` e uma Spec pequena, dedicada a um endpoint especifico.

---

## 6. Principios Constitutivos

### 6.1 Objetivo Central

O Mindvox existe para transformar aulas gravadas em memoria consultavel.

Interpretacao obrigatoria:

- a API deve receber arquivos de audio ja gravados;
- a API deve transcrever o audio;
- a API deve processar transcricoes;
- a API deve permitir consultas posteriores por sentido aproximado ou campos estruturados;
- funcionalidades que nao sirvam a esse objetivo devem ser tratadas como fora de escopo ou futuras.

### 6.2 MVP Controlado

O MVP do Mindvox deve permanecer simples, funcional, documentado, testavel e explicavel.

No MVP, o nucleo do projeto e:

1. transcricao de audio;
2. processamento de transcricoes;
3. busca e consulta da memoria.

Ficam fora do MVP, salvo decisao explicita do autor do projeto:

- TTS;
- resposta falada em streaming;
- speech-to-speech;
- interface grafica;
- captura de audio ao vivo dentro da API;
- dependencia obrigatoria de servicos internos do Atrium.

### 6.3 API First

O Mindvox segue abordagem API First.

Consequencia obrigatoria:

- cada funcionalidade deve ser pensada primeiro como contrato de API;
- rotas, metodos, entradas, respostas, erros e documentacao devem ser definidos antes ou junto da implementacao;
- endpoints de negocio versionados devem colocar a versao apos o nome do recurso ou servico, usando o padrao `/<recurso>/v1` ou `/<recurso>/<subrecurso>/v1`;
- endpoints operacionais simples, como health check, podem ficar fora desse padrao quando nao representarem recurso de negocio;
- a documentacao automatica do FastAPI nao e acabamento final, mas parte do contrato do projeto;
- endpoints nao devem ser implementados como detalhes improvisados de codigo.

### 6.4 FastAPI Como Decisao Tecnica Vigente

O Mindvox sera implementado em FastAPI nesta entrega.

Interpretacao obrigatoria:

- as Specs devem favorecer recursos proprios do FastAPI quando eles ajudarem a clareza do contrato;
- validacao, schemas, responses, status codes e documentacao automatica devem ser aproveitados;
- FastAPI e decisao tecnica da entrega atual, nao principio filosofico eterno do produto.

### 6.5 Spec Antes de Implementacao

Nenhum endpoint real do MVP deve ser implementado sem Spec propria, ainda que pequena.

Consequencia obrigatoria:

- cada endpoint deve ter uma Spec dedicada;
- a Spec do endpoint deve versar somente sobre a materia daquele endpoint;
- a implementacao deve seguir a Spec aprovada ou revisada;
- mudancas relevantes de contrato exigem revisao da Spec correspondente.
- os textos aprovados em spec revisora devem constar como adendo no corpo da própria spec, revisada.

### 6.6 Completude Didatica por Endpoint

Cada endpoint deve ser desenvolvido com a maior completude possivel antes do proximo endpoint ser iniciado, respeitando apenas as dependencias essenciais do codigo.

Interpretacao obrigatoria:

- a finalidade e permitir compreensao clara do que esta sendo feito;
- a repeticao sequencial das boas praticas em cada endpoint favorece a fixacao do conhecimento;
- cada endpoint deve percorrer, sempre que possivel, o ciclo completo: contrato de entrada, resposta de sucesso, respostas de erro, validacao, logs, seguranca basica, documentacao automatica, teste valido, teste invalido e explicacao;
- a intencao nao e apenas terminar o projeto, mas formar dominio tecnico suficiente para desenvolver APIs com eficacia tecnica e seguranca elevada.

### 6.7 Hierarquia de Decisao

A ordem normativa de precedencia do Mindvox e:

1. seguranca
2. eficiencia
3. custo

Interpretacao obrigatoria:

- seguranca prevalece sobre eficiencia;
- eficiencia prevalece sobre custo;
- custo baixo e objetivo permanente, mas subordinado aos dois anteriores;
- custo prevalece sobre fatores secundarios como conveniencia, preferencia estetica, sofisticacao desnecessaria ou curiosidade tecnica.

### 6.8 Seguranca Como Pre-condicao

Seguranca nao deve ser tratada como etapa tardia.

Consequencia obrigatoria:

- `.env` nao deve ser enviado ao GitHub;
- chaves, tokens e credenciais nao devem aparecer em commits, README ou exemplos publicos reais;
- endpoints devem validar entradas;
- endpoints que manipulem dados sensiveis devem nascer com controle de acesso proporcional ao risco;
- erros devem ser tratados sem expor detalhes sensiveis;
- arquivos de audio e transcricoes devem ser tratados como conteudo sensivel;
- qualquer exposicao publica do projeto deve passar por verificacao minima de seguranca.
- politicas de permissao e controle de acesso devem se tornar mais rigorosas conforme a sensibilidade dos dados, o risco operacional e a hierarquia de decisao definida em §6.7.
- o MVP deve simular padroes de seguranca, configuracao externa e separacao de responsabilidades compativeis com uma arquitetura endurecivel em AWS, sem tornar o deploy em AWS requisito da entrega;
- a arquitetura deve deixar aberta a evolucao para mecanismos como tokens, JWT, OAuth2, OpenID Connect, Keycloak, API Gateway, Cognito ou equivalentes, conforme necessidade futura.

### 6.9 Dados Sensiveis Ficam Protegidos

Audios, transcricoes e metadados de aula podem conter informacoes sensiveis.

Consequencia obrigatoria:

- o projeto deve evitar envio desnecessario de dados sensiveis a servicos externos;
- quando uso externo for necessario, deve ser explicito, justificado e documentado;
- exemplos publicos devem usar dados ficticios ou seguros;
- `.env.example` pode documentar variaveis esperadas, mas nao pode conter segredos reais;
- logs nao devem registrar transcricoes integrais, chaves ou dados privados sem necessidade.

### 6.10 Independencia Operacional

O Mindvox deve rodar como projeto proprio para a entrega.

Interpretacao obrigatoria:

- o repositorio deve conter API propria, endpoints proprios e instrucoes proprias de execucao;
- o projeto pode se inspirar em solucoes do Atrium, especialmente N02 e N04;
- o projeto nao deve depender obrigatoriamente de servicos internos do Atrium para cumprir o MVP;
- logicas aproveitadas devem ser adaptadas para o escopo menor e academico do Mindvox.

### 6.11 Memoria Isolada

A memoria do Mindvox deve ser tratada como memoria propria, isolada no nano-space:

```text
projeto_mindvox
```

Consequencia obrigatoria:

- conteudos do Mindvox nao devem ser misturados com memorias de outros projetos;
- Specs posteriores devem definir como esse isolamento sera aplicado na persistencia e na busca;
- busca semantica e busca relacional devem respeitar o escopo desse nano-space.

### 6.12 Explicabilidade

O projeto deve ser explicavel e não conter fatoração ou implementação pouco clara ao desenvolvedor humano.

Consequencia obrigatoria:

- decisoes tecnicas relevantes devem ser compreensiveis;
- termos tecnicos devem ser explicados quando necessario;
- cada endpoint deve poder ser apresentado com clareza: objetivo, entrada, processamento, saida, erro e teste;
- complexidade que prejudique explicacao e demonstracao deve ser evitada no MVP.

---

## 7. Regras Para Specs de Endpoint

Cada Spec de endpoint deve conter, no minimo:

- identificacao;
- finalidade;
- rota e metodo HTTP;
- entradas aceitas;
- resposta de sucesso;
- respostas de erro;
- validacoes;
- seguranca;
- logs;
- documentacao FastAPI esperada;
- criterios de aceite;
- exemplos de teste valido e invalido.

A documentacao deve ser topico proprio em cada Spec de endpoint.

---

## 8. Invariantes Operacionais

Os principios acima geram estes invariantes:

- o Mindvox nao deve se expandir para TTS, streaming ou speech-to-speech sem decisao explicita;
- nenhum endpoint real deve nascer sem Spec propria;
- cada endpoint deve ser concluido ao maximo antes do proximo, salvo dependencia tecnica justificada;
- seguranca prevalece sobre eficiencia;
- eficiencia prevalece sobre custo;
- custo prevalece sobre fatores secundarios;
- `.env` e segredos reais nao devem ir para o GitHub;
- endpoints que manipulem dados sensiveis devem exigir controle de acesso proporcional ao risco;
- audios e transcricoes devem ser tratados como dados sensiveis;
- o Mindvox deve rodar independentemente do Atrium para a entrega;
- o nano-space canonico do projeto e `projeto_mindvox`;
- README nao deve prometer funcionalidade que o codigo ainda nao implementa;
- documentacao automatica do FastAPI faz parte do contrato do projeto.

---

## 9. Questoes Abertas

Esta Spec ainda nao decide:

- qual motor STT sera usado no MVP;
- qual estrategia de embeddings sera usada;
- qual banco de dados sera adotado;
- qual formato final das tabelas relacionais;
- qual mecanismo de busca semantica sera usado;
- quais mecanismos concretos de autenticacao e autorizacao serao usados por cada endpoint do MVP;
- quais testes automatizados serao implementados primeiro.

Essas questoes devem ser resolvidas em Specs posteriores ou em decisoes tecnicas associadas a endpoints especificos.

---

## 10. Criterios de Fechamento

Esta Spec podera passar de `aberta` para `fechada` quando:

- O autor do projeto aprovar seus principios;
- o escopo do MVP estiver claro;
- a hierarquia seguranca > eficiencia > custo estiver aceita;
- a regra de Spec por endpoint estiver aceita;
- a regra de completude didatica por endpoint estiver aceita;
- nao houver conflito com o README nem com o contrato de mentoria.

---

## 11. Registro de Fechamento

Status atual: `fechada`.

Fechamento registrado em 2026-06-07.

Responsavel: Adalberto Batista, com auditoria auxiliar do assistente.

Motivo: a Spec foi revisada pelo autor do projeto e auditada contra `README.md` e `docs/mindvox_mentoring_agreement.md`. Nao foram encontrados conflitos materiais, omissoes significativas ou presencas capazes de gerar conflito futuro apos ajustes pontuais de clareza textual.
