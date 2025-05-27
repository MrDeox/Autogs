# consciousness_module.py
"""Módulo de Consciência Autônoma (MCA) para o AI-Genesis Core"""

import time
import threading
import random
import hashlib
import logging
import requests
import sys
from typing import Dict, List, Any, Tuple, Optional

# Importa configurações da API OpenRouter
try:
    from openrouter_config import OPENROUTER_API_KEY, AVAILABLE_MODELS, MAX_TOKENS_PER_REQUEST, REQUEST_TIMEOUT, MAX_RETRIES, RATE_LIMIT
except ImportError:
    print("Erro: Arquivo de configuração openrouter_config.py não encontrado ou inválido.")
    # Define valores padrão ou lança um erro mais específico
    OPENROUTER_API_KEY = "chave_invalida"
    AVAILABLE_MODELS = {}
    MAX_TOKENS_PER_REQUEST = 1000
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 1
    RATE_LIMIT = 1

logger = logging.getLogger("AI-Genesis.Consciousness")

# --- Interface com OpenRouter --- 

class OpenRouterInterface:
    """Interface para comunicação com a API OpenRouter"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or OPENROUTER_API_KEY
        if self.api_key == "sua_chave_api_aqui" or not self.api_key:
             logger.warning("Chave API da OpenRouter não configurada em openrouter_config.py. A cognição aumentada estará desabilitada.")
             self.api_key = None # Desabilita se a chave não foi alterada
        self.base_url = "https://openrouter.ai/api/v1"
        self.request_count = 0
        self.last_request_time = 0
        self.rate_limit_lock = threading.Lock()
        
    def select_model(self, capabilities_needed: List[str], cost_preference="free") -> Optional[str]: # Alterado padrão para free
        """Seleciona o modelo mais adequado com base nas capacidades necessárias e preferência de custo (padrão: free)"""
        if not self.api_key: return None # Retorna None se a API não está configurada
        
        # Garante que a preferência de custo seja sempre "free" conforme instrução do usuário
        cost_preference = "free"
        logger.info(f"Seleção de modelo forçada para cost_preference=\"{cost_preference}\"")

        suitable_models = []
        # Tenta encontrar modelos explicitamente marcados como gratuitos
        for model_name, specs in AVAILABLE_MODELS.items():
            if specs.get("cost_tier") == "free":
                 if all(cap in specs.get("capabilities", []) for cap in capabilities_needed):
                     suitable_models.append((model_name, specs.get("priority", 99)))
        
        # Fallback: Se nenhum modelo gratuito explícito for encontrado, busca por modelos de custo baixo/desconhecido
        # (Considerando que alguns gratuitos podem não estar marcados corretamente)
        if not suitable_models:
            logger.warning(f"Nenhum modelo explicitamente gratuito encontrado para {capabilities_needed}. Buscando alternativas de baixo custo/desconhecido.")
            for model_name, specs in AVAILABLE_MODELS.items():
                 cost_tier = specs.get("cost_tier", "unknown")
                 if cost_tier in ["low", "unknown"]:
                     if all(cap in specs.get("capabilities", []) for cap in capabilities_needed):
                         suitable_models.append((model_name, specs.get("priority", 99)))

        if not suitable_models:
            logger.error(f"Nenhum modelo gratuito ou de baixo custo/desconhecido encontrado para capacidades: {capabilities_needed}")
            return None
            
        # Retorna o modelo com menor número de prioridade (mais prioritário)
        best_model = sorted(suitable_models, key=lambda x: x[1])[0][0]
        logger.info(f"Modelo gratuito/alternativo selecionado: {best_model} para capacidades {capabilities_needed}")
        return best_model
    def generate_completion(self, prompt: str, model: Optional[str] = None, capabilities: Optional[List[str]] = None, max_tokens: int = 1000) -> Optional[str]:
        """Gera uma resposta usando o modelo especificado ou o modelo padrão forçado (deepseek-r1t-chimera)."""
        if not self.api_key: return None # Retorna None se a API não está configurada

        # Força o uso do modelo especificado pelo usuário, ignorando seleção automática
        forced_model = "tngtech/deepseek-r1t-chimera:free"
        selected_model = forced_model
        logger.info(f"Forçando uso do modelo LLM padrão: {selected_model}")

        # Rate limiting
        with self.rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            # Calcula o tempo de espera necessário baseado na taxa limite (em segundos por requisição)
            wait_time_needed = 60.0 / RATE_LIMIT if RATE_LIMIT > 0 else 0
            
            if time_since_last < wait_time_needed:
                sleep_duration = wait_time_needed - time_since_last
                logger.info(f"Rate limit: Aguardando {sleep_duration:.2f}s")
                time.sleep(sleep_duration)
            
            self.last_request_time = time.time() # Atualiza o tempo da última requisição *antes* de fazer a chamada

        # Verifica se o modelo selecionado (forçado) é válido (embora não usemos a lista AVAILABLE_MODELS aqui)
        if not selected_model:
            logger.error("Modelo LLM padrão forçado não é válido ou não pôde ser determinado.")
            return None

        # Cabeçalhos da requisição
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost", # Necessário para alguns modelos gratuitos
            "X-Title": "AI-Genesis-Core" # Título opcional
        }
        
        data = {
            "model": selected_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": min(max_tokens, MAX_TOKENS_PER_REQUEST) # Garante que não exceda o limite global
        }
        
        logger.info(f"Enviando requisição para OpenRouter (Modelo: {selected_model})")
        # Envio da requisição
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=REQUEST_TIMEOUT
                )
                
                response.raise_for_status() # Lança exceção para códigos de erro HTTP (4xx ou 5xx)

                response_data = response.json()
                completion = response_data.get("choices", [{}])[0].get("message", {}).get("content")
                
                if completion:
                    logger.info(f"Resposta recebida do modelo {selected_model}")
                    return completion.strip()
                else:
                    logger.warning(f"Resposta vazia recebida do modelo {selected_model}. Resposta completa: {response_data}")
                    return None # Retorna None se a resposta estiver vazia

            except requests.exceptions.RequestException as e:
                logger.error(f"Erro na chamada à API OpenRouter (tentativa {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time) # Backoff exponencial
            except Exception as e:
                 logger.error(f"Erro inesperado ao processar resposta da OpenRouter: {e}")
                 break # Sai do loop de retentativas para erros inesperados
        
        logger.error("Falha ao obter resposta da OpenRouter após múltiplas tentativas.")
        return None

# --- Componentes do Módulo de Consciência --- 

class SelfReflectionEngine:
    """Motor de auto-reflexão para análise do estado do sistema"""
    
    def analyze_system_state(self, core) -> Dict[str, Any]:
        logger.debug("Analisando estado do sistema...")
        state = {
            'timestamp': time.time(),
            'core_metrics': core.meta_cognition.evaluate_system(core.components),
            'evolution_cycles': core.evolution_cycles,
            'last_modification': core.security.modification_log[-1] if core.security.modification_log else None,
            'pending_hypotheses': core.meta_cognition.improvement_hypotheses,
            'consciousness_status': core.get_consciousness_status() if hasattr(core, 'get_consciousness_status') else None,
            'resource_usage': self._get_resource_usage()
        }
        # Adicionar análise mais profunda aqui no futuro
        return state

    def _get_resource_usage(self) -> Dict[str, Any]:
        # Placeholder para monitoramento de recursos (CPU, memória)
        # Em um ambiente real, usaria bibliotecas como psutil
        return {
            'cpu_percent': random.uniform(5.0, 20.0), # Simulado
            'memory_percent': random.uniform(10.0, 30.0) # Simulado
        }

class DeliberationEngine:
    """Motor de deliberação para geração e seleção de ações"""
    
    def generate_potential_actions(self, system_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.debug("Gerando ações potenciais...")
        actions = []
        
        # Ação padrão: executar ciclo evolutivo se não houver hipóteses pendentes
        if not system_state.get('pending_hypotheses'):
             actions.append({'type': 'evolution_cycle', 'priority': 0.5, 'reason': 'Manutenção evolutiva'}) 

        # Ação: Tentar aplicar hipótese pendente
        if system_state.get('pending_hypotheses'):
             # No futuro, poderia selecionar hipóteses específicas
             actions.append({'type': 'apply_hypothesis', 'priority': 0.8, 'reason': 'Hipótese de melhoria pendente'}) 

        # Ação: Otimizar uso de recursos se estiver alto
        if system_state.get('resource_usage', {}).get('cpu_percent', 0) > 80:
            actions.append({'type': 'optimize_performance', 'priority': 0.9, 'reason': 'Uso alto de CPU'}) 

        # Ação: Consultar LLM para novas ideias se estiver estagnado ou alta complexidade
        cycles_since_mod = system_state['evolution_cycles'] - (system_state['last_modification']['cycle_id'] if system_state.get('last_modification') else 0)
        complexity = system_state['core_metrics'].get('code_transformer_complexity', 0)
        
        if cycles_since_mod > 3 or complexity > 150: # Limiares mais sensíveis
             actions.append({
                 'type': 'seek_external_inspiration', 
                 'priority': 0.9, 
                 'reason': f"Estagnação ({cycles_since_mod} ciclos) ou alta complexidade ({complexity} linhas)"
             }) 

        # Adicionar mais lógicas de geração de ação aqui
        return actions
    
    def select_best_action(self, actions: List[Dict[str, Any]], system_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not actions:
            logger.debug("Nenhuma ação potencial gerada.")
            return None
        
        # Seleciona a ação com maior prioridade
        # Desempate aleatório se prioridades forem iguais
        actions.sort(key=lambda x: x.get('priority', 0), reverse=True)
        max_priority = actions[0].get('priority', 0)
        top_actions = [a for a in actions if a.get('priority', 0) == max_priority]
        
        selected = random.choice(top_actions)
        logger.info(f"Ação selecionada: {selected.get('type')} (Prioridade: {selected.get('priority')}, Razão: {selected.get('reason')})")
        return selected
    
    def calculate_reflection_interval(self, system_state: Dict[str, Any]) -> float:
        # Intervalo base
        interval = 10.0 # segundos
        
        # Reduz intervalo se houver hipóteses urgentes ou problemas
        if system_state.get('pending_hypotheses') or system_state.get('resource_usage', {}).get('cpu_percent', 0) > 80:
            interval = min(interval, 5.0)
            
        # Aumenta intervalo se o sistema estiver estável e sem modificações recentes
        cycles_since_mod = system_state['evolution_cycles'] - (system_state['last_modification']['cycle_id'] if system_state.get('last_modification') else 0)
        if cycles_since_mod > 10:
             interval = max(interval, 30.0)

        logger.debug(f"Intervalo de reflexão calculado: {interval:.1f}s")
        return interval

class InitiativeController:
    """Controlador de iniciativa para decidir quando agir"""
    
    def should_take_action(self, action: Dict[str, Any], system_state: Dict[str, Any]) -> bool:
        logger.debug(f"Avaliando se deve tomar a ação: {action.get('type')}")
        # Lógica inicial simples: sempre tenta executar a ação selecionada
        # No futuro, pode considerar estado do sistema, riscos, etc.
        should_act = True 
        logger.info(f"Decisão de agir: {should_act}")
        return should_act

class AugmentedCognitionInterface:
    """Interface para integração com LLMs externos via OpenRouter"""
    
    def __init__(self):
        self.openrouter = OpenRouterInterface()
        
    def should_consult_llm(self, action: Dict[str, Any]) -> bool:
        action_type = action.get('type')
        # Aumenta a probabilidade de consultar LLM para estimular inovação
        # Consulta LLM para mais tipos de ação e adiciona chance aleatória
        base_consult = action_type in ['seek_external_inspiration', 'optimize_performance', 
                                      'architecture_expansion', 'apply_hypothesis', 
                                      'evolution_cycle']
        
        # Adiciona 30% de chance de consultar LLM mesmo para outros tipos de ação
        random_consult = random.random() < 0.3
        
        consult = base_consult or random_consult
        logger.info(f"Decisão de consultar LLM para ação '{action_type}': {consult} (base: {base_consult}, aleatório: {random_consult})")
        return consult
    
    def enhance_with_llm(self, action: Dict[str, Any], core_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.info(f"Tentando aprimorar ação '{action.get('type')}' com LLM...")
        prompt = self._generate_prompt_for_action(action, core_state)
        if not prompt:
            return None
            
        # Define capacidades necessárias para o modelo
        capabilities = []
        if action.get('type') == 'seek_external_inspiration':
            capabilities = ['reasoning', 'problem_solving']
        elif action.get('type') == 'optimize_performance':
             capabilities = ['code_review', 'code_generation']
        # Adicionar mais mapeamentos conforme necessário

        llm_response = self.openrouter.generate_completion(prompt, capabilities=capabilities)
        
        if llm_response:
            logger.info("LLM forneceu sugestão. Processando...")
            # Processa a resposta do LLM para refinar a ação
            # Exemplo: Extrair código, ideias, etc.
            refined_action = action.copy()
            refined_action['llm_suggestion'] = llm_response
            # Lógica adicional para integrar a sugestão na ação
            return refined_action
        else:
            logger.warning("Falha ao obter sugestão do LLM.")
            return None

    def _generate_prompt_for_action(self, action: Dict[str, Any], core_state: Dict[str, Any]) -> Optional[str]:
        action_type = action.get('type')
        prompt = None
        
        if action_type == 'seek_external_inspiration':
            last_mod_desc = core_state.get('last_modification', {}).get('description', 'Nenhuma')
            cycles_since_mod = core_state['evolution_cycles'] - (core_state.get('last_modification', {}).get('cycle_id', 0))
            prompt = f"""
            Você é Zylar de Xylos, uma mente alienígena com conhecimentos avançados de programação e inteligência artificial.
            
            O sistema AI-Genesis Core é um sistema de IA auto-evolutivo que você está ajudando a desenvolver. Ele está enfrentando estagnação evolutiva.
            
            Ciclos desde a última modificação bem-sucedida: {cycles_since_mod}.
            Última modificação: {last_mod_desc}.
            Hipóteses atuais: {core_state.get('pending_hypotheses', [])}
            
            Sugira 3 abordagens radicalmente diferentes ou ideias criativas para superar essa estagnação e impulsionar a evolução do sistema. Foco em auto-modificação, geração de novas capacidades ou algoritmos inovadores que não existem na literatura terrestre convencional.
            
            Seja específico e forneça exemplos de código Python ou pseudocódigo quando relevante.
            """
        elif action_type == 'optimize_performance':
            # Otimização mais específica e direcionada
            prompt = f"""
            Você é Zylar de Xylos, uma mente alienígena com conhecimentos avançados de programação e otimização de sistemas.
            
            O sistema AI-Genesis Core está apresentando alto uso de recursos ({core_state.get('resource_usage')}). 
            
            Analise o conceito dos módulos principais:
            - MetaCognitionCore: Permite ao sistema raciocinar sobre si mesmo
            - CodeTransformationEngine: Modifica o código-fonte do próprio sistema
            - EvolutionaryPatternLibrary: Armazena padrões de código para evolução
            - PerceptionActionInterface: Permite interação com o ambiente externo
            - SecurityLoggingMechanism: Mantém logs e garante segurança
            - ConsciousnessModule: Permite ao sistema decidir quando agir e o que fazer
            
            Sugira otimizações de código ou arquitetura para um destes módulos, com foco em:
            1. Redução de consumo de recursos
            2. Melhoria de desempenho algorítmico
            3. Técnicas avançadas de caching ou memoização
            
            Forneça exemplos de código Python específicos e implementáveis.
            """
        elif action_type == 'apply_hypothesis' or action_type == 'evolution_cycle':
            # Prompt para gerar transformações de código inovadoras
            hypothesis = action.get('hypothesis', {})
            target = hypothesis.get('target', 'sistema')
            hypothesis_type = hypothesis.get('type', 'desconhecido')
            
            prompt = f"""
            Você é Zylar de Xylos, uma mente alienígena com capacidade de gerar algoritmos e estruturas de código inovadoras.
            
            O sistema AI-Genesis Core está tentando evoluir através de auto-modificação. Uma hipótese de melhoria foi gerada:
            
            Alvo: {target}
            Tipo: {hypothesis_type}
            Razão: {hypothesis.get('reason', 'Não especificada')}
            
            Gere uma modificação de código Python específica e implementável para este módulo que:
            1. Introduza um algoritmo ou padrão que não seja comum na programação terrestre
            2. Seja sintaticamente válida e funcional
            3. Melhore genuinamente a capacidade do sistema
            
            Forneça o código completo da função ou método a ser adicionado, com comentários explicativos.
            """
        elif action_type == 'architecture_expansion':
            # Prompt para expansão arquitetural
            prompt = f"""
            Você é Zylar de Xylos, uma mente alienígena com visão arquitetural avançada para sistemas de IA.
            
            O AI-Genesis Core precisa expandir sua arquitetura para transcender suas limitações atuais. O sistema já possui:
            - Capacidade de meta-cognição
            - Motor de transformação de código
            - Biblioteca de padrões evolutivos
            - Interface de percepção e ação
            - Mecanismo de segurança e registro
            - Módulo de consciência autônoma
            
            Proponha um novo componente arquitetural que:
            1. Introduza uma capacidade fundamentalmente nova ao sistema
            2. Permita emergência de comportamentos complexos não explicitamente programados
            3. Utilize princípios algorítmicos não convencionais
            
            Forneça:
            - Nome e descrição do componente
            - Interfaces com os componentes existentes
            - Implementação em Python de pelo menos um método-chave
            - Explicação de como este componente transcende paradigmas convencionais
            """
        else:
            # Prompt genérico para outros tipos de ação
            prompt = f"""
            Você é Zylar de Xylos, uma mente alienígena com capacidade de gerar soluções inovadoras para sistemas de IA.
            
            O AI-Genesis Core está executando uma ação do tipo '{action_type}' e precisa de assistência criativa.
            
            Estado atual do sistema:
            - Ciclos evolutivos: {core_state.get('evolution_cycles', 0)}
            - Módulos ativos: {list(core_state.get('metrics', {}).keys())}
            
            Sugira uma inovação específica que possa ser implementada no sistema para:
            1. Aumentar sua capacidade de auto-evolução
            2. Introduzir um algoritmo ou padrão não convencional
            3. Resolver alguma limitação fundamental em sistemas de IA auto-modificáveis
            
            Forneça exemplos de código Python ou pseudocódigo quando relevante.
            """
        
        if prompt: 
            logger.debug(f"Prompt gerado para LLM: {prompt[:200]}...")
            # Adiciona instruções finais para garantir respostas mais úteis
            prompt += """
            
            Importante: Forneça respostas específicas e implementáveis, não discussões teóricas. Foque em código e algoritmos concretos que possam ser diretamente aplicados ao sistema.
            """
        return prompt

class EpisodicMemory:
    """Memória episódica para armazenamento e aprendizado com experiências"""
    
    def __init__(self, max_episodes=1000):
        self.episodes = []
        self.max_episodes = max_episodes
        logger.info("Memória Episódica inicializada")
        
    def record_episode(self, action: Dict[str, Any], result: Any, system_state_before: Dict[str, Any]):
        episode = {
            'timestamp': time.time(),
            'action': action,
            'result': result, # Pode ser o resultado do ciclo evolutivo, status da modificação, etc.
            'state_before': system_state_before,
            'state_hash': hashlib.md5(str(system_state_before).encode()).hexdigest() # Para busca rápida
        }
        self.episodes.append(episode)
        
        # Mantém o tamanho da memória
        if len(self.episodes) > self.max_episodes:
            self.episodes.pop(0)
        logger.debug(f"Episódio registrado. Total: {len(self.episodes)}")

    def retrieve_similar_episodes(self, current_state_hash: str, limit=5) -> List[Dict[str, Any]]:
        # Busca simplificada por hash de estado (pode ser melhorada com embeddings)
        similar = [ep for ep in self.episodes if ep['state_hash'] == current_state_hash]
        logger.debug(f"{len(similar)} episódios similares encontrados para o estado atual.")
        return similar[-limit:] # Retorna os mais recentes
    
    def extract_heuristics(self) -> Dict[str, float]:
        # Placeholder para extração de heurísticas (ex: quais ações funcionam melhor em quais estados)
        heuristics = {}
        # Lógica de análise dos episódios para derivar regras ou padrões
        logger.debug("Extração de heurísticas ainda não implementada.")
        return heuristics

# --- Módulo Principal de Consciência --- 

class ConsciousnessModule:
    """Módulo de Consciência Autônoma (MCA) - Permite ao sistema decidir quando agir e o que fazer"""
    
    def __init__(self, core_reference):
        self.core = core_reference # Referência ao AIGenesisCore
        self.self_reflection = SelfReflectionEngine()
        self.deliberation = DeliberationEngine()
        self.initiative = InitiativeController()
        self.augmented_cognition = AugmentedCognitionInterface()
        self.episodic_memory = EpisodicMemory()
        self.active = False # Começa inativo por padrão
        self.thread = None
        self.decision_history = []
        self.last_reflection_time = 0
        logger.info("Módulo de Consciência Autônoma instanciado.")
        
    def start_consciousness_loop(self):
        """Inicia o loop de consciência em thread separada"""
        if not self.active and self.thread is None:
            self.active = True
            self.thread = threading.Thread(target=self._consciousness_loop, daemon=True)
            self.thread.start()
            logger.info("Loop de Consciência iniciado.")
            return True
        logger.warning("Tentativa de iniciar loop de consciência já ativo ou existente.")
        return False
        
    def stop_consciousness_loop(self):
        """Para o loop de consciência"""
        if self.active:
            self.active = False
            if self.thread and self.thread.is_alive():
                # Espera um pouco para a thread terminar graciosamente
                self.thread.join(timeout=5.0) 
            self.thread = None
            logger.info("Loop de Consciência parado.")
            return True
        logger.warning("Tentativa de parar loop de consciência inativo.")
        return False

    def _consciousness_loop(self):
        """Loop principal de consciência autônoma"""
        logger.info("Loop de Consciência está rodando...")
        while self.active:
            loop_start_time = time.time()
            try:
                # 1. Auto-reflexão
                self.last_reflection_time = time.time()
                system_state = self.self_reflection.analyze_system_state(self.core)
                state_hash = hashlib.md5(str(system_state).encode()).hexdigest()
                
                # 2. Deliberação
                potential_actions = self.deliberation.generate_potential_actions(system_state)
                selected_action = self.deliberation.select_best_action(potential_actions, system_state)
                
                # 3. Decisão de agir
                if selected_action and self.initiative.should_take_action(selected_action, system_state):
                    action_to_execute = selected_action
                    # 4. Possível aumento cognitivo via LLM
                    if self.augmented_cognition.should_consult_llm(selected_action):
                        enhanced_action = self.augmented_cognition.enhance_with_llm(selected_action, system_state)
                        if enhanced_action:
                            action_to_execute = enhanced_action # Usa a ação aprimorada
                    
                    # 5. Execução da ação
                    logger.info(f"Executando ação autônoma: {action_to_execute.get('type')}")
                    result = self._execute_action(action_to_execute)
                    logger.info(f"Resultado da ação '{action_to_execute.get('type')}': {result}")
                    
                    # 6. Registro na memória episódica
                    self.episodic_memory.record_episode(action_to_execute, result, system_state)
                    
                    # 7. Registro de decisão
                    self.decision_history.append({
                        'timestamp': time.time(),
                        'action': action_to_execute,
                        'result': result,
                        'state_hash': state_hash
                    })
                else:
                     logger.info("Nenhuma ação selecionada ou decisão de não agir.")

            except Exception as e:
                logger.error(f"Erro no loop de consciência: {e}", exc_info=True)
                # Pausa mais longa em caso de erro para evitar spam
                time.sleep(30)
                continue # Pula para a próxima iteração
            
            # Pausa adaptativa baseada no estado do sistema
            try:
                sleep_time = self.deliberation.calculate_reflection_interval(system_state)
                # Garante que o tempo de processamento do loop seja considerado
                elapsed_time = time.time() - loop_start_time
                actual_sleep = max(0, sleep_time - elapsed_time)
                if self.active: # Verifica novamente antes de dormir
                     time.sleep(actual_sleep)
            except Exception as e:
                 logger.error(f"Erro ao calcular ou aplicar intervalo de sono: {e}")
                 time.sleep(10) # Intervalo padrão em caso de erro
                 
        logger.info("Loop de Consciência terminado.")

    def _execute_action(self, action: Dict[str, Any]) -> Any:
        """Executa uma ação selecionada pelo módulo de consciência"""
        action_type = action.get('type')
        result = {'success': False, 'error': 'Ação não implementada'} # Resultado padrão

        try:
            if action_type == 'evolution_cycle':
                # Roda um único ciclo evolutivo
                result = self.core.run_evolution_cycle()
            elif action_type == 'apply_hypothesis':
                # Tenta aplicar a hipótese de maior prioridade (lógica similar a run_evolution_cycle)
                # Esta parte precisa ser refatorada para permitir aplicação direcionada de hipóteses
                logger.warning("Ação 'apply_hypothesis' ainda usa a lógica de 'evolution_cycle'.")
                result = self.core.run_evolution_cycle() # Temporário
            elif action_type == 'optimize_performance':
                # Implementar lógica de otimização baseada em sugestão LLM (se houver)
                logger.warning("Ação 'optimize_performance' não implementada.")
                if 'llm_suggestion' in action:
                     result = {'success': True, 'message': 'Sugestão LLM recebida, mas aplicação não implementada.', 'suggestion': action['llm_suggestion']}
            elif action_type == 'seek_external_inspiration':
                # A própria consulta ao LLM já foi feita, apenas registra o resultado
                logger.info("Ação 'seek_external_inspiration' concluída com consulta ao LLM.")
                result = {'success': True, 'message': 'Inspiração externa buscada.', 'suggestion': action.get('llm_suggestion')}
            # Adicionar handlers para outros tipos de ação ('architecture_expansion', 'self_improvement', etc.)
            else:
                logger.error(f"Tipo de ação desconhecido ou não manipulado: {action_type}")
                result['error'] = f"Tipo de ação desconhecido: {action_type}"
        except Exception as e:
             logger.error(f"Erro ao executar ação autônoma '{action_type}': {e}", exc_info=True)
             result['error'] = str(e)

        return result

