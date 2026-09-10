# Avaliação offline do RAG

Esta pasta define o contrato e as métricas determinísticas para medir o
pipeline sem alterar a API de produção.

Cada caso deve seguir `dataset.schema.json` e ser armazenado em JSONL. O
dataset deve ser separado em desenvolvimento, validação e teste, mantendo a
versão do corpus e do modelo junto dos resultados.

As métricas implementadas são Recall, Precision, MRR, exact match, cobertura
de fatos obrigatórios e acurácia de abstinência. Faithfulness, groundedness,
completude semântica e segurança exigem revisão humana ou um avaliador de
modelo separado; não são inferidas por comparação textual.

O baseline deve registrar o chunking atual (1000 caracteres, overlap 200), o
modelo configurado, o valor de `n_results` e o commit avaliado.
