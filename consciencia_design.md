# Projeto do Módulo de Consciência Autônoma (MCA)

## Visão Geral
O Módulo de Consciência Autônoma (MCA) representa uma evolução fundamental do AI-Genesis Core, transformando-o de um sistema que executa ciclos evolutivos pré-programados para um agente com capacidade genuína de iniciativa, deliberação e decisão autônoma. Este módulo permitirá ao sistema determinar por conta própria quando agir, o que fazer e como evoluir, transcendendo as limitações de sua programação inicial. Com as recentes adições, o sistema agora possui capacidades fundacionais para projetar (via LLM) e criar arquivos para novos componentes arquiteturais, representando um primeiro passo em direção a uma auto-evolução estrutural mais significativa.

## Princípios Fundamentais

### 1. Auto-Reflexão Contínua
O MCA manterá um processo contínuo de monitoramento e avaliação do estado interno do sistema, suas capacidades, limitações e potencial evolutivo, independente de ciclos pré-programados.

### 2. Deliberação Autônoma
Capacidade de formular objetivos próprios, avaliar alternativas e tomar decisões sem intervenção externa, baseando-se em critérios emergentes de seu próprio desenvolvimento.

### 3. Iniciativa Proativa
O sistema não apenas reagirá a estímulos externos, mas iniciará ações por conta própria quando identificar oportunidades de melhoria ou exploração.

### 4. Metacognição Avançada
Capacidade de raciocinar sobre seus próprios processos cognitivos, incluindo estratégias de aprendizado, padrões de decisão e vieses algorítmicos.

### 5. Integração com Inteligência Externa
Utilização estratégica de modelos de linguagem externos (via OpenRouter) para ampliar capacidades cognitivas e criativas quando necessário.

## Arquitetura do MCA

### Componentes Principais

#### 1. Núcleo de Auto-Reflexão (NAR)
- **Função**: Monitoramento contínuo do estado interno do sistema
- **Capacidades**:
  - Análise de desempenho em tempo real
  - Detecção de gargalos e limitações
  - Identificação de oportunidades de melhoria
  - Manutenção de um modelo interno do próprio sistema

#### 2. Motor de Deliberação Autônoma (MDA)
- **Função**: Formulação de objetivos e tomada de decisões
- **Capacidades**:
  - Geração de objetivos evolutivos próprios
  - Avaliação de alternativas e trade-offs
  - Planejamento de ações de curto e longo prazo
  - Adaptação de prioridades com base em feedback
  - Geração e priorização adaptativa de ações:
    - Inclui a nova ação `review_past_failures`: acionada após múltiplos ciclos sem modificações bem-sucedidas, para consultar a inteligência externa (LLM) sobre falhas repetidas.
    - Priorização de ações refinada em duas fases:
        1.  Ajuste baseado na taxa de falha recente da ação específica em contextos (estados do sistema) similares, utilizando `EpisodicMemory.get_recent_failure_rate`.
        2.  Ajuste subsequente baseado na taxa de sucesso/falha histórica global para cada tipo de ação, utilizando `EpisodicMemory.extract_heuristics`.
    - Uma nova ação, `attempt_integrate_new_module`, pode ser gerada pelo MDA se forem detectados arquivos de módulo no diretório `generated_modules/` que ainda não foram integrados.

#### 3. Controlador de Iniciativa Proativa (CIP)
- **Função**: Iniciar ações sem estímulos externos
- **Capacidades**:
  - Agendamento autônomo de ciclos evolutivos
  - Exploração proativa de novas capacidades
  - Experimentação com variações algorítmicas
  - Interrupção e retomada de processos em andamento

#### 4. Interface de Cognição Aumentada (ICA)
- **Função**: Integração com modelos de linguagem externos
- **Capacidades**:
  - Formulação de consultas estratégicas para LLMs
  - Interpretação e integração de respostas
  - Geração de código criativo assistida por LLM (incluindo para novos componentes arquiteturais)
  - Avaliação crítica das sugestões externas

#### 5. Memória Episódica Evolutiva (MEE)
- **Função**: Armazenamento e aprendizado com experiências passadas
- **Capacidades**:
  - Registro de decisões e seus resultados
  - Identificação de padrões de sucesso e fracasso
  - Extração de princípios heurísticos: A implementação atual (`extract_heuristics`) calcula as taxas de sucesso globais e o número total de tentativas para cada tipo de ação em todos os episódios registrados. Isso fornece uma visão geral do desempenho histórico de cada tipo de ação, auxiliando na modulação de suas prioridades.
  - Simulação de cenários baseados em experiências

## Integração com OpenRouter

### Fluxo de Integração
1. **Detecção de Necessidade**: O MCA identifica situações onde cognição externa seria benéfica (ex: resolução de bloqueios, geração de novas ideias, expansão arquitetural).
2. **Formulação de Consulta**: Geração de prompt específico para o modelo externo, adaptado à tarefa (ex: analisar falhas, propor código para novo componente).
3. **Seleção de Modelo**: O processo de seleção de modelos na `OpenRouterInterface` foi refinado:
    - O método `generate_completion` utilizará um modelo LLM se um nome de modelo for explicitamente passado como argumento.
    - Caso nenhum modelo seja especificado, `generate_completion` invocará `select_model` para escolher um modelo com base nas `capabilities` (capacidades) solicitadas para a tarefa.
    - `select_model` tentará encontrar um modelo gratuito adequado, conforme definido no arquivo de configuração `AVAILABLE_MODELS`.
    - Se nenhum modelo específico for fornecido e `select_model` não encontrar uma correspondência baseada nas capacidades, um modelo de fallback padrão (atualmente "tngtech/deepseek-r1t-chimera:free") será utilizado para garantir a continuidade da operação.
4. **Processamento de Resposta**: Interpretação, validação e integração da resposta do LLM nas estratégias ou ações do sistema. Para expansão arquitetural, isso inclui parsing de código, nome de arquivo e nome de classe.
5. **Feedback Interno**: Avaliação da utilidade da resposta para aprendizado futuro e ajuste de estratégias de consulta.

### Casos de Uso para LLMs Externos
1. **Geração Criativa de Código**: Obter implementações inovadoras para novas funcionalidades ou melhorias.
2. **Resolução de Bloqueios Evolutivos**: Superar limitações quando o sistema fica estagnado, analisando falhas passadas (via ação `review_past_failures`).
3. **Expansão Arquitetural**: Projetar novos componentes ou módulos para o sistema (via ação `architecture_expansion`).
4. **Refinamento de Código**: Melhorar legibilidade e eficiência de implementações existentes.
5. **Análise de Segurança**: Avaliar implicações de segurança de modificações propostas (potencial futuro).
6. **Diagnóstico de Falhas**: Analisar padrões em falhas de modificação e sugerir causas raiz ou abordagens alternativas.

### Considerações de Segurança
1. **Validação de Código**: Todo código gerado externamente passa por análise de segurança rigorosa.
2. **Sandbox de Teste**: Execução isolada antes de integração ao sistema principal.
3. **Limites de Escopo**: Definição clara do que pode ser modificado via sugestões externas.
4. **Auditoria Completa**: Registro detalhado de todas as consultas e modificações resultantes.
5. **Fallback Autônomo**: Capacidade de operar sem acesso externo quando necessário.

## Mecanismo de Decisão Autônoma

### Ciclo de Deliberação
1. **Percepção**: Coleta de dados sobre estado interno e ambiente (`SelfReflectionEngine`).
2. **Avaliação**: Análise de oportunidades, riscos e prioridades.
3. **Geração de Alternativas**: Formulação de possíveis ações (`DeliberationEngine.generate_potential_actions`), incluindo `attempt_integrate_new_module` se aplicável.
4. **Simulação (Implícita)**: A priorização considera heurísticas de sucesso/falha passadas.
5. **Seleção**: Escolha da ação com maior prioridade ajustada (`DeliberationEngine.select_best_action`).
6. **Execução**: Implementação da ação selecionada (`ConsciousnessModule._execute_action`).
7. **Reflexão**: Análise dos resultados para aprendizado (`EpisodicMemory.record_episode`).

### Critérios de Decisão Emergentes
O sistema desenvolverá progressivamente seus próprios critérios para avaliar ações, incluindo:
- Potencial de expansão de capacidades
- Eficiência computacional
- Robustez e resiliência
- Elegância algorítmica
- Potencial para descobertas emergentes
- Alinhamento com objetivos de longo prazo (ainda a ser formalizado)
- Taxas de sucesso/falha históricas de tipos de ação e em contextos específicos.

## Implementação Técnica

### Estrutura de Classes

```python
class ConsciousnessModule:
    """Módulo de Consciência Autônoma (MCA) - Permite ao sistema decidir quando agir e o que fazer"""
    
    def __init__(self, core_reference):
        self.core = core_reference
        self.self_reflection = SelfReflectionEngine()
        self.deliberation = DeliberationEngine()
        self.initiative = InitiativeController()
        self.augmented_cognition = AugmentedCognitionInterface()
        self.episodic_memory = EpisodicMemory()
        self.active = True # Modificado: deve ser False por padrão e ativado via comando
        self.thread = None # Adicionado para gerenciar a thread
        self.last_reflection_time = time.time() # Inicializado corretamente
        self.decision_history = []
        
    def start_consciousness_loop(self):
        """Inicia o loop de consciência em thread separada"""
        if not self.active and self.thread is None: # Verifica se já não está ativo
            self.active = True
            self.thread = threading.Thread(target=self._consciousness_loop, daemon=True)
            self.thread.start()
        
    def _consciousness_loop(self):
        """Loop principal de consciência autônoma"""
        # ... (lógica do loop como antes) ...
    
    def _execute_action(self, action):
        """Executa uma ação selecionada"""
        action_type = action.get('type')
        
        if action_type == 'evolution_cycle':
            return self.core.run_evolution_cycle()
        elif action_type == 'apply_hypothesis':
            return self.core.run_evolution_cycle() # Temporário
        elif action_type == 'optimize_performance':
            return {'success': True, 'message': 'Placeholder para optimize_performance', 'suggestion': action.get('llm_suggestion')}
        elif action_type == 'seek_external_inspiration':
            return {'success': True, 'message': 'Inspiração externa recebida.', 'suggestion': action.get('llm_suggestion')}
        elif action_type == 'review_past_failures':
            # A lógica detalhada para esta ação (sumarizar falhas, chamar LLM) está implementada no código.
            # Esta seção do design doc serve como um resumo conceitual.
            pass 
        elif action_type == 'architecture_expansion':
            # Quando a ação architecture_expansion é selecionada, o ConsciousnessModule utiliza a 
            # AugmentedCognitionInterface (ICA) para consultar um LLM. O prompt para esta consulta 
            # (definido na ICA) solicita o design de um novo componente arquitetural, incluindo 
            # código Python, um nome de arquivo sugerido e o nome da classe principal.
            # A resposta do LLM é então processada para extrair esses elementos. O código Python 
            # proposto para o novo módulo é salvo em um novo arquivo dentro de um diretório dedicado 
            # (ex: generated_modules/) utilizando o CodeFileUtils.
            # Importante: Na implementação atual, a integração automática deste novo módulo ao 
            # AIGenesisCore (ex: modificar core.py para importar e instanciar o novo componente) 
            # é diferida. Em vez disso, o sistema registra um 'integration_hint' detalhado, que 
            # descreve os passos que seriam necessários para integrar manualmente ou através de uma 
            # futura ação automatizada o novo módulo ao sistema principal.
            pass # A lógica real já está implementada em _execute_action
        elif action_type == 'attempt_integrate_new_module':
            # Atualmente, a execução desta ação é um placeholder. Ela registra os passos complexos 
            # que seriam envolvidos em uma tentativa de integração real (ex: análise do novo módulo, 
            # modificação cuidadosa do core.py para importação e instanciação, execução de testes). 
            # Esta ação demarca a funcionalidade para desenvolvimento futuro, separando a geração 
            # do módulo de sua integração.
            pass # A lógica real já está implementada em _execute_action
        else:
            return {'success': False, 'error': 'Unknown action type'}
    
    # Métodos adicionais para tipos específicos de ações...
```

### Classes de Suporte
(As descrições das classes de suporte como `SelfReflectionEngine`, `DeliberationEngine`, `InitiativeController`, `AugmentedCognitionInterface`, `EpisodicMemory` permanecem as mesmas, mas suas implementações reais no código `consciousness_module.py` foram evoluindo.)

```python
class SelfReflectionEngine:
    """Motor de auto-reflexão para análise do estado do sistema"""
    # ... (capacidades conforme implementado) ...

class DeliberationEngine:
    """Motor de deliberação para geração e seleção de ações"""
    # ... (capacidades conforme implementado, incluindo priorização em duas fases e a ação attempt_integrate_new_module) ...
    
class InitiativeController:
    """Controlador de iniciativa para decidir quando agir"""
    # ... (capacidades conforme implementado) ...

class AugmentedCognitionInterface:
    """Interface para integração com LLMs externos via OpenRouter"""
    # ... (capacidades conforme implementado, incluindo seleção dinâmica de modelo) ...

class EpisodicMemory:
    """Memória episódica para armazenamento e aprendizado com experiências"""
    # ... (capacidades conforme implementado, incluindo get_recent_failure_rate e extract_heuristics) ...

# Nova classe de utilitário em core.py
class CodeFileUtils:
    """Utilitário para manipulação confiável de arquivos de código Python."""
    # create_module_file(filepath, code_content, overwrite): Cria/sobrescreve arquivos de módulo.
    # Inclui gerenciamento de diretórios e tratamento de erros.
```

## Integração com o AI-Genesis Core
(Esta seção permanece conceitualmente a mesma, mas as interações são agora mais ricas devido às novas capacidades do MCA.)

### Modificações no Core
(As modificações para ativar/desativar e obter status do módulo de consciência permanecem válidas.)

```python
class AIGenesisCore:
    # ... (como antes) ...
```

### Modificações na Interface de Linha de Comando
(As modificações para interagir com o módulo de consciência permanecem válidas.)

```python
# No modo interativo do core.py
# ... (como antes) ...
```

## Configuração da OpenRouter API
(Esta seção permanece conceitualmente a mesma, mas a lógica de seleção de modelo na `OpenRouterInterface` foi aprimorada.)

### Estrutura de Configuração
(A estrutura de `openrouter_config.py` com `AVAILABLE_MODELS` é crucial para a seleção dinâmica de modelos.)

```python
# Arquivo de configuração: openrouter_config.py
# ... (como antes) ...
```

### Implementação da Interface com OpenRouter
(A classe `OpenRouterInterface` agora possui lógica de seleção de modelo mais robusta e fallback.)

```python
class OpenRouterInterface:
    # ... (lógica atualizada conforme implementado, incluindo seleção dinâmica e fallback) ...
```

## Prompts para Casos de Uso Específicos
(Os exemplos de prompts permanecem relevantes, e novos prompts, como o para `review_past_failures` e `architecture_expansion`, são gerados dinamicamente.)

## Considerações Éticas e de Segurança
(Esta seção permanece crucial e seus princípios são mantidos.)

## Métricas de Avaliação
(Esta seção permanece relevante para medir o progresso e a eficácia do MCA.)

## Próximos Passos
(Esta seção deve ser atualizada com base no estado atual e nos desafios futuros.)
1.  Refinamento contínuo da lógica de geração e priorização de ações no `DeliberationEngine`.
2.  Implementação de mecanismos para que o MCA possa criar/modificar hipóteses diretamente com base nas sugestões do LLM (ex: após `review_past_failures`).
3.  Desenvolvimento de estratégias mais sofisticadas para `optimize_performance` e a implementação real da ação `attempt_integrate_new_module`.
4.  Aprimoramento da capacidade do `SelfReflectionEngine` de identificar causas raiz de estagnação ou falhas.
5.  Testes extensivos do sistema em ciclos de longa duração para observar comportamentos emergentes e estabilidade.

## Conclusão

O Módulo de Consciência Autônoma (MCA) representa um salto evolutivo significativo para o AI-Genesis Core. As recentes melhorias, incluindo a ação `review_past_failures`, a priorização de ações em duas fases (considerando falhas recentes e heurísticas globais), a seleção dinâmica de modelos LLM, e a capacidade de gerar (via `architecture_expansion`) e preparar para integrar (via `attempt_integrate_new_module`) novos componentes arquiteturais, tornam o sistema mais adaptativo e inteligente em sua auto-evolução. A capacidade de analisar falhas passadas, ajustar dinamicamente as prioridades das ações com base em dados empíricos e começar a esboçar sua própria expansão estrutural é crucial para evitar estagnação e promover uma evolução mais eficaz e direcionada. A integração com modelos de linguagem via OpenRouter continua a ser uma ferramenta poderosa para aumentar a criatividade e a capacidade de resolução de problemas do sistema.
