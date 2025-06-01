# Plano de Aprimoramento: CodeTransformationEngine - Auto-Implementação Funcional

## Objetivo

Capacitar o `CodeTransformationEngine` (MTC) do AI-Genesis Core a gerar e integrar código Python funcional real, utilizando as sugestões do LLM (`tngtech/deepseek-r1t-chimera:free`), superando a limitação atual de gerar apenas placeholders ou comentários TODO. As modificações geradas devem ser validadas pela infraestrutura de testes automatizados existente.

## Etapas Detalhadas

1.  **Refinar Processamento de Sugestões LLM:**
    *   **Extração de Código:** Aprimorar a lógica em `generate_code_modification` para extrair blocos de código Python (` ```python ... ``` `) das `llm_suggestion` de forma mais robusta.
    *   **Tratamento de Formatos:** Implementar heurísticas para identificar e extrair código Python mesmo quando não estiver explicitamente formatado em blocos markdown.
    *   **Análise Preliminar:** Antes da inserção, realizar uma análise sintática básica (usando `ast.parse`) no *código extraído* para detectar erros óbvios fornecidos pelo LLM.

2.  **Implementar Inserção de Código Funcional:**
    *   **Lógica de Inserção:** Desenvolver lógica precisa para inserir o código extraído do LLM no local correto dentro da classe/método alvo.
        *   Para `expand_functionality`: Inserir como corpo de um novo método ou substituir um `pass`/`TODO` existente.
        *   Para `refactor_simplification` / `optimize_performance`: Tentar substituir o corpo do método/função alvo pelo código otimizado/refatorado sugerido (requer identificação precisa do método alvo).
    *   **Tratamento de Indentação:** Garantir que a indentação do código inserido seja ajustada corretamente ao contexto.

3.  **Gerenciamento de Imports (Tentativa Inicial):**
    *   **Identificação:** Tentar identificar declarações `import` dentro do código sugerido pelo LLM.
    *   **Inserção Global:** Adicionar os imports identificados no início do arquivo `core.py`, verificando se já não existem para evitar duplicatas. (Nota: Gerenciamento de imports é complexo; esta é uma abordagem inicial simplificada).

4.  **Validação Rigorosa via Testes:**
    *   **Integração com `test_modified_code`:** Garantir que *todo* código gerado, especialmente aquele derivado de sugestões LLM, passe pela função `test_modified_code`.
    *   **Feedback de Falha:** Se os testes falharem para um código sugerido pelo LLM, registrar essa falha claramente nos logs. Considerar mecanismos futuros para usar essa falha como feedback para refinar prompts ao LLM.

5.  **Melhorar Geração de Placeholders (Fallback):**
    *   **Estrutura Aprimorada:** Se a sugestão do LLM não puder ser processada ou não for fornecida, gerar placeholders mais úteis (ex: assinaturas de métodos com type hints básicos inferidos da hipótese) em vez de apenas `pass`.

6.  **Atualizar Logging:**
    *   **Clareza:** Aumentar a verbosidade dos logs em `generate_code_modification` para indicar claramente a origem do código (LLM ou template), o sucesso/falha da extração e inserção, e o resultado da validação sintática preliminar.

## Próximo Passo Imediato

Iniciar a modificação da função `generate_code_modification` na classe `CodeTransformationEngine` dentro de `core.py` para implementar as etapas 1 e 2 (Refinar Processamento de Sugestões LLM e Implementar Inserção de Código Funcional).
