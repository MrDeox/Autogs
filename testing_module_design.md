# Projeto do Módulo de Testes Automáticos (MTA)

## 1. Propósito

O Módulo de Testes Automáticos (MTA) tem como objetivo principal garantir a robustez e a estabilidade do AI-Genesis Core durante seu processo evolutivo. Ele validará as modificações de código geradas pelo Motor de Transformação de Código (MTC), com ou sem assistência de LLM, *antes* que essas modificações sejam aplicadas permanentemente ao código-fonte principal. Isso reduzirá o risco de regressões, erros de sintaxe ou falhas funcionais introduzidas durante a auto-modificação, permitindo transformações mais ousadas e seguras.

## 2. Arquitetura

O MTA será implementado como um novo componente dentro do AI-Genesis Core, residindo em seu próprio arquivo (`testing_engine.py`) para modularidade. Ele será integrado ao ciclo evolutivo principal, sendo invocado após a geração de uma modificação pelo MTC e antes da aplicação final dessa modificação.

**Componentes Principais do MTA:**

1.  **Gerador de Casos de Teste (GCT):** Responsável por criar casos de teste relevantes para a modificação proposta. Pode operar de forma:
    *   **Estrutural:** Analisar o código modificado (diff) e gerar testes básicos de unidade focados nas funções/métodos alterados (ex: verificar tipos de retorno, tratamento de exceções básicas).
    *   **Assistida por LLM:** Consultar o LLM configurado (ex: DeepSeek) para gerar casos de teste mais complexos e semanticamente relevantes com base na descrição da modificação e no código alterado.
    *   **Baseada em Histórico:** Reutilizar testes de ciclos anteriores que falharam para garantir a correção de bugs (regressão).
2.  **Executor de Testes em Sandbox (ETS):** Executa o código *modificado* (não o principal) em um ambiente isolado e seguro para avaliar seu comportamento.
    *   Utilizará `exec()` ou `subprocess` em um ambiente controlado para executar trechos de código ou o módulo modificado.
    *   Capturará saídas (stdout, stderr) e exceções.
    *   Comparará resultados com uma linha de base (output do código original) ou com asserções definidas nos casos de teste.
3.  **Avaliador de Resultados (AR):** Analisa os resultados da execução dos testes e determina se a modificação é segura para ser aplicada.
    *   Classifica o resultado como: `PASS`, `FAIL`, `ERROR`.
    *   Gera um relatório resumido dos testes executados.

## 3. Funcionalidades Detalhadas

*   **Geração de Testes:**
    *   O GCT receberá o código original, o código modificado e a descrição da hipótese.
    *   Para testes estruturais: Identificará funções/métodos modificados/adicionados e gerará chamadas simples com tipos de dados esperados ou aleatórios, verificando se não há exceções inesperadas.
    *   Para testes assistidos por LLM: Enviará um prompt ao LLM contendo o diff do código, a descrição da hipótese e solicitará a geração de casos de teste em formato Python (`unittest` ou similar).
*   **Execução em Sandbox:**
    *   O ETS criará um ambiente temporário (possivelmente um processo separado ou usando `exec` com um `globals`/`locals` restrito).
    *   Carregará o código modificado neste ambiente.
    *   Executará os casos de teste gerados pelo GCT.
    *   Registrará todas as saídas e exceções.
*   **Avaliação:**
    *   O AR comparará as saídas/exceções com os resultados esperados definidos nos casos de teste.
    *   Qualquer exceção inesperada ou falha de asserção resultará em `FAIL`.
    *   Erros durante a própria execução do teste (não relacionados à lógica do código modificado) resultarão em `ERROR`.
    *   Se todos os testes passarem, o resultado será `PASS`.

## 4. Integração com o Ciclo Evolutivo

O ciclo evolutivo principal em `AIGenesisCore.evolve()` será modificado:

```python
# Dentro de AIGenesisCore.evolve()

# ... (Geração de hipótese, consulta LLM, etc.)

# 3. Geração da Modificação
modified_code, description = self.code_transformer.generate_code_modification(
    current_code, best_hypothesis, llm_suggestion
)

# --- NOVA ETAPA: Teste da Modificação ---
if modified_code != current_code:
    test_result = self.testing_engine.run_tests(current_code, modified_code, best_hypothesis)
    cycle_log["test_result"] = test_result
    
    if test_result["status"] != "PASS":
        logger.warning(f"Modificação reprovada nos testes: {test_result["summary"]}. Revertendo.")
        # Não aplica a modificação
        # Pode gerar feedback para refinar a hipótese/transformação
        # ... (lógica de feedback para o NMC/MTC)
        continue # Pula para o próximo ciclo ou tenta outra hipótese
    else:
        logger.info("Modificação aprovada nos testes.")
        # Continua para aplicação da modificação
# --- FIM DA NOVA ETAPA ---

# 4. Aplicação da Modificação (apenas se passou nos testes)
if modified_code != current_code and test_result["status"] == "PASS":
    # ... (Salva diff, atualiza código, etc.)
    current_code = modified_code
    # ...

# ... (Avaliação de impacto, etc.)
```

## 5. Métricas

O MTA contribuirá com as seguintes métricas para a avaliação de impacto:

*   `test_status`: (PASS, FAIL, ERROR)
*   `tests_run_count`: Número de casos de teste executados.
*   `tests_passed_count`: Número de casos de teste que passaram.
*   `test_coverage_estimate`: (Opcional, se implementado) Estimativa da cobertura de código alcançada pelos testes.

## 6. Considerações

*   **Complexidade:** Gerar testes automaticamente, especialmente para código complexo ou com efeitos colaterais, é desafiador. A abordagem inicial será pragmática, focando em testes de unidade básicos e validação de sintaxe/execução sem erros.
*   **Sandbox Seguro:** A execução do código modificado deve ser rigorosamente isolada para evitar impacto no sistema principal.
*   **Desempenho:** A execução de testes adicionará tempo a cada ciclo evolutivo. O processo deve ser otimizado.
*   **Evolução dos Testes:** O próprio MTA pode se tornar um alvo para a evolução, aprimorando sua capacidade de gerar e executar testes mais eficazes.

## 7. Próximos Passos

1.  Implementar a classe `TestingEngine` em `testing_engine.py`.
2.  Desenvolver as funcionalidades básicas do GCT (geração estrutural) e ETS.
3.  Integrar a chamada ao `testing_engine.run_tests()` no ciclo evolutivo do `AIGenesisCore`.
4.  Validar o funcionamento com modificações simples.
5.  (Opcional) Implementar a geração de testes assistida por LLM.
6.  (Opcional) Implementar a reutilização de testes de regressão.
