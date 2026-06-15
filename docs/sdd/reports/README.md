# Indice Evolutivo dos Relatorios SDD

Esta pasta guarda relatorios tecnicos produzidos durante a evolucao da E03 e de decisoes relacionadas. Eles nao devem ser lidos como documentos todos igualmente atuais.

Os relatorios sao historicos e evolutivos: documentos mais novos podem corrigir, superar ou refinar conclusoes de documentos anteriores. Para implementar, priorize sempre a Spec, o Plano e as Tarefas atuais. Use estes relatorios como trilha de decisao, evidencias, auditorias e justificativas.

## Ordem de leitura recomendada

A numeracao abaixo preserva a ordem aproximada de criacao dos relatorios, sem renomear arquivos para evitar quebra de referencias.

| Ordem | Relatorio | Papel na evolucao |
| --- | --- | --- |
| R01 | `RELATORIO_DIRETRIZES_E03_SERVICO_IA_LLM.md` | Diretrizes iniciais para a E03 como servico de IA/LLM. |
| R02 | `RELATORIO_ARQUITETURA_E_ESCOPO_E03_E05.md` | Enquadramento arquitetural entre E03, E04/E05 e escopo academico. |
| R03 | `RELATORIO_BENCHMARK_E03_MODELOS_LLM.md` | Benchmark inicial de modelos locais para pos-processamento. |
| R04 | `RELATORIO_CORRECAO_AUDITORIA_IMPLEMENTACAO_E03.md` | Correcao apos auditoria inicial da implementacao. |
| R05 | `RELATORIO_SEGUNDA_AUDITORIA_IMPLEMENTACAO_E03.md` | Segunda auditoria; contem pontos historicos depois superados. |
| R06 | `RELATORIO_CORRECAO_SEGUNDA_AUDITORIA_IMPLEMENTACAO_E03.md` | Correcoes decorrentes da segunda auditoria. |
| R07 | `RELATORIO_NOVA_AUDITORIA_POS_CORRECAO_E03.md` | Nova auditoria pos-correcao; tambem inclui achados historicos. |
| R08 | `RELATORIO_CORRECAO_NOVA_AUDITORIA_E03.md` | Correcoes decorrentes da nova auditoria. |
| R09 | `RELATORIO_AUDITORIA_FINAL_POS_CORRECAO_E03.md` | Auditoria final daquela fase de correcao. |
| R10 | `RELATORIO_SINTESE_E03_CHUNKING_PIPELINE_VAULT.md` | Sintese ampla: chunking, merge canonico, auditoria, Vault e decisoes consolidadas. |
| R11 | `RELATORIO_E03_INTERFACE_STUDY_PACKAGE_E_VAULT_OPCIONAL.md` | Decisao mais recente sobre pagina humana de entrada, Study Package, pagina de saida, E04 e Vault opcional. |

## Regra pratica

Se houver conflito entre relatorios, leia primeiro o relatorio mais novo da linha tematica e confirme a decisao final nos documentos canonicos:

```text
docs/sdd/specs/
docs/sdd/plans/
docs/sdd/tasks/
```

Relatorios antigos podem conter diagnosticos corretos para a epoca, mas estados de implementacao ja superados.
