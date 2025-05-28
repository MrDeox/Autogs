from __future__ import annotations

# consciousness_module.py
"""Módulo de Consciência Autônoma (MCA) para o AI-Genesis Core"""

import os # For path manipulation
import re # For parsing
import time
import threading
import random
import hashlib
import logging
import requests
import sys
from typing import Dict, List, Any, Tuple, Optional

# Assuming core.py is in the same directory or Python path
from core import CodeFileUtils 

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
        """Gera uma resposta usando o modelo LLM, selecionado dinamicamente ou especificado."""
        if not self.api_key: return None # Retorna None se a API não está configurada

        selected_model_for_request = None # Renamed to avoid confusion with the 'model' argument
        if model: # If a specific model is provided as an argument
            selected_model_for_request = model
            logger.info(f"Usando modelo LLM fornecido diretamente: {selected_model_for_request}")
        elif capabilities: # If capabilities are provided, try to select based on them
            logger.info(f"Tentando selecionar modelo LLM com base nas capacidades: {capabilities}")
            # select_model already handles cost_preference internally (forced to "free")
            selected_model_from_capabilities = self.select_model(capabilities_needed=capabilities) 
            if selected_model_from_capabilities:
                selected_model_for_request = selected_model_from_capabilities
                logger.info(f"Modelo LLM selecionado por capacidades: {selected_model_for_request}")
            else:
                logger.warning(f"Nenhum modelo encontrado para as capacidades: {capabilities}. Tentando fallback.")
        
        if not selected_model_for_request:
            # Fallback to a default model if no model was provided or selected
            default_fallback_model = "tngtech/deepseek-r1t-chimera:free" 
            selected_model_for_request = default_fallback_model
            logger.info(f"Usando modelo LLM de fallback padrão: {selected_model_for_request} (nenhum modelo fornecido ou selecionado por capacidades).")

        # Ensure selected_model_for_request is not None before proceeding
        if not selected_model_for_request:
            logger.error("Nenhum modelo LLM pôde ser determinado (nem fornecido, nem selecionado, nem fallback). Abortando.")
            return None

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
        # This check is now implicitly covered by the logic above ensuring selected_model_for_request is not None.

        # Cabeçalhos da requisição
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost", # Necessário para alguns modelos gratuitos
            "X-Title": "AI-Genesis-Core" # Título opcional
        }
        
        data = {
            "model": selected_model_for_request, # Use the dynamically determined or fallback model
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": min(max_tokens, MAX_TOKENS_PER_REQUEST) # Garante que não exceda o limite global
        }
        
        logger.info(f"Enviando requisição para OpenRouter (Modelo: {selected_model_for_request})")
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
                    logger.info(f"Resposta recebida do modelo {selected_model_for_request}")
                    return completion.strip()
                else:
                    logger.warning(f"Resposta vazia recebida do modelo {selected_model_for_request}. Resposta completa: {response_data}")
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

        # Check for unintegrated modules
        generated_modules_dir = "generated_modules"
        if os.path.exists(generated_modules_dir) and os.path.isdir(generated_modules_dir):
            try:
                py_files_in_generated_dir = [
                    f for f in os.listdir(generated_modules_dir) 
                    if os.path.isfile(os.path.join(generated_modules_dir, f)) and f.endswith(".py") and f != "__init__.py"
                ]
                if py_files_in_generated_dir:
                    actions.append({
                        'type': 'attempt_integrate_new_module',
                        'priority': 0.6, 
                        'reason': f'Found {len(py_files_in_generated_dir)} new module(s) in {generated_modules_dir} awaiting integration.',
                        'modules_to_integrate': py_files_in_generated_dir
                    })
                    logger.info(f"Action 'attempt_integrate_new_module' generated for {py_files_in_generated_dir}.")
            except OSError as e:
                logger.warning(f"Could not list files in {generated_modules_dir} for integration check: {e}")

        # Calculate cycles_since_mod (assuming last_modification implies a successful, i.e., applied, modification)
        last_mod_cycle_id = 0
        # Ensure system_state['last_modification'] is a dict and has 'cycle_id'
        if isinstance(system_state.get('last_modification'), dict):
            last_mod_cycle_id = system_state['last_modification'].get('cycle_id', 0)
        
        current_evolution_cycles = system_state.get('evolution_cycles', 0)
        cycles_since_mod = current_evolution_cycles - last_mod_cycle_id

        # Ação padrão: executar ciclo evolutivo se não houver hipóteses pendentes
        if not system_state.get('pending_hypotheses'):
            actions.append({'type': 'evolution_cycle', 'priority': 0.5, 'reason': 'Manutenção evolutiva regular'})

        # Ação: Tentar aplicar hipótese pendente
        if system_state.get('pending_hypotheses'):
            actions.append({'type': 'apply_hypothesis', 'priority': 0.9, 'reason': 'Hipótese de melhoria pendente'})

        # Ação: Otimizar uso de recursos se estiver alto
        if system_state.get('resource_usage', {}).get('cpu_percent', 0) > 80:
            actions.append({'type': 'optimize_performance', 'priority': 0.9, 'reason': 'Uso alto de CPU'})
        
        # Ação: Revisar falhas passadas se muitas modificações falharam
        if cycles_since_mod > 5:
            actions.append({
                'type': 'review_past_failures',
                'priority': 0.85,
                'reason': f'{cycles_since_mod} ciclos sem modificação efetiva. Revisar falhas anteriores.'
            })

        # Ação: Consultar LLM para novas ideias se estiver estagnado ou alta complexidade
        # Use .get() for core_metrics and the specific complexity metric to avoid KeyErrors
        core_metrics = system_state.get('core_metrics', {})
        complexity = core_metrics.get('code_transformer_complexity', 0) # Assuming this is the correct key based on previous context
        
        reason_for_inspiration_parts = []
        seek_inspiration = False

        if cycles_since_mod > 3:
            seek_inspiration = True
            reason_for_inspiration_parts.append(f"Estagnação ({cycles_since_mod} ciclos)")
        
        if complexity > 150: # Limiares mais sensíveis
            seek_inspiration = True
            # Use a more generic term like "linhas" or "unidades" if 'complexity' is not strictly lines
            reason_for_inspiration_parts.append(f"alta complexidade ({complexity} unidades)") 

        if seek_inspiration:
            actions.append({
                'type': 'seek_external_inspiration',
                'priority': 0.75, 
                'reason': " e ".join(reason_for_inspiration_parts) if reason_for_inspiration_parts else "Necessidade de novas ideias"
            })

        return actions
    
    def select_best_action(self, actions: List[Dict[str, Any]], system_state: Dict[str, Any], episodic_memory: 'EpisodicMemory') -> Optional[Dict[str, Any]]:
        if not actions:
            logger.debug("Nenhuma ação potencial gerada.")
            return None

        # Phase 1: Adjust priorities based on recent failure rates for the current state_hash
        actions_after_recent_failure_check = []
        current_state_hash = system_state.get('state_hash')

        if current_state_hash is None:
            logger.warning("state_hash não encontrado em system_state. Não será possível o ajuste de prioridade da Fase 1 (falhas recentes).")
            actions_after_recent_failure_check = [action.copy() for action in actions] # Use original priorities
        else:
            for action in actions:
                action_copy = action.copy()
                action_type_for_recent_check = action_copy['type']
                failure_rate = episodic_memory.get_recent_failure_rate(
                    action_type_for_recent_check,
                    current_state_hash
                )
                
                if failure_rate > 0.5: # If more than 50% of recent similar attempts failed
                    original_priority_phase1 = action_copy.get('priority', 0.5)
                    penalty = 0.3 * original_priority_phase1
                    action_copy['priority'] = original_priority_phase1 - penalty
                    logger.info(f"Prioridade (Fase 1) da ação '{action_type_for_recent_check}' ({original_priority_phase1:.2f}) reduzida para {action_copy['priority']:.2f} devido à taxa de falha recente de {failure_rate:.2f} no estado atual.")
                actions_after_recent_failure_check.append(action_copy)
        
        if not actions_after_recent_failure_check: # Should only happen if original 'actions' was empty
             logger.debug("Nenhuma ação após a verificação de falhas recentes (lista original provavelmente vazia).")
             return None

        # Phase 2: Adjust priorities based on global heuristics from all episodes
        global_heuristics = episodic_memory.extract_heuristics()
        final_adjusted_actions = []

        for action_in_progress in actions_after_recent_failure_check:
            action_copy = action_in_progress.copy() # action_in_progress is already a copy from the first phase or original
            action_type = action_copy['type']
            heuristic_data = global_heuristics.get(action_type)
            
            current_priority_before_global_adj = action_copy['priority'] # This is priority after recent check

            if heuristic_data and heuristic_data.get('total_attempts', 0) >= 3: # Min 3 attempts for global heuristic
                success_rate = heuristic_data['success_rate']
                adjustment_factor = 0.0

                if success_rate < 0.4: adjustment_factor = -0.15    # Significantly poor performance
                elif success_rate < 0.6: adjustment_factor = -0.05   # Slightly below average
                elif success_rate > 0.9: adjustment_factor = 0.15    # Significantly good performance
                elif success_rate > 0.75: adjustment_factor = 0.05   # Good performance
                
                if adjustment_factor != 0.0:
                    new_priority = max(0.0, min(1.0, current_priority_before_global_adj + adjustment_factor))
                    # Only log if priority actually changed
                    if abs(new_priority - current_priority_before_global_adj) > 1e-9: # Compare floats carefully
                        action_copy['priority'] = new_priority
                        logger.info(f"Prioridade (Fase 2) da ação '{action_type}' ({current_priority_before_global_adj:.2f}) ajustada para {action_copy['priority']:.2f} com base na heurística global (taxa de sucesso: {success_rate:.2f} em {heuristic_data.get('total_attempts',0)} tentativas).")
            
            final_adjusted_actions.append(action_copy)

        if not final_adjusted_actions:
            logger.warning("Nenhuma ação restou após aplicação de heurísticas globais. Isso não deveria acontecer se a lista original não era vazia.")
            # Fallback to actions after recent failure check if final list is empty
            final_adjusted_actions = actions_after_recent_failure_check


        # Seleciona a ação com maior prioridade (finalmente ajustada)
        final_adjusted_actions.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        if not final_adjusted_actions: # This means original 'actions' was empty
             return None

        max_priority = final_adjusted_actions[0].get('priority', 0)
        top_actions = [a for a in final_adjusted_actions if a.get('priority', 0) == max_priority]
        
        selected_action = random.choice(top_actions)
        
        # Find original priority (from the initial 'actions' list) for logging comparison
        original_action_for_logging = next((act for act in actions if act['type'] == selected_action['type']), None)
        original_priority_val_str = f"{original_action_for_logging.get('priority'):.2f}" if original_action_for_logging else "N/A"

        logger.info(f"Ação selecionada: {selected_action.get('type')} (Prioridade Inicial: {original_priority_val_str}, Prioridade Final Ajustada: {selected_action.get('priority'):.2f}, Razão: {selected_action.get('reason')})")
        return selected_action
    
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

    def get_recent_failure_rate(self, action_type: str, current_state_hash: str, lookback_period: int = 3) -> float:
        """
        Calculates the failure rate for a given action type in a similar state from recent episodes.
        Failure is defined as 'modification_applied' being False or 'errors' being present in the result.
        """
        relevant_episodes = 0
        failures = 0
        
        # Iterate backwards through recent episodes
        for episode in reversed(self.episodes):
            if relevant_episodes >= lookback_period:
                break # Stop after checking enough episodes
            
            if episode.get('action', {}).get('type') == action_type and \
               episode.get('state_hash') == current_state_hash:
                relevant_episodes += 1
                result = episode.get('result', {})
                # Check for failure conditions (specific to 'evolution_cycle' type actions for now)
                # This condition might need to be generalized if other actions have different success criteria
                if isinstance(result, dict):
                    # modification_applied defaults to True if not present for non-cycle actions (e.g. seek_inspiration)
                    # For evolution_cycle, if modification_applied is False, it's a failure.
                    # If 'errors' key exists and has content, it's a failure.
                    modification_applied_successfully = result.get('modification_applied', True)
                    has_errors = bool(result.get('errors')) # Check if 'errors' list is non-empty

                    if action_type == 'evolution_cycle' or action_type == 'apply_hypothesis':
                        if not modification_applied_successfully or has_errors:
                            failures += 1
                    # For other action types, 'success': False in result might be a failure indicator
                    elif 'success' in result and not result['success']:
                         failures += 1
                    # If no explicit failure, but also no explicit success for certain actions
                    elif action_type not in ['evolution_cycle', 'apply_hypothesis'] and 'success' not in result:
                        logger.debug(f"Resultado para ação '{action_type}' não tem 'success' nem 'modification_applied'. Considerado neutro/sucesso: {result}")


                elif result is None: # Consider None result as failure too for some actions
                    logger.debug(f"Resultado None para ação '{action_type}'. Considerado falha.")
                    failures +=1

        if relevant_episodes == 0:
            return 0.0 # No relevant recent episodes, so no observed failures

        failure_rate = failures / relevant_episodes
        logger.debug(f"Calculada taxa de falha para ação '{action_type}' no estado '{current_state_hash}': {failure_rate:.2f} ({failures}/{relevant_episodes} falhas nos últimos {lookback_period} episódios relevantes)")
        return failure_rate
    
    def extract_heuristics(self) -> Dict[str, Dict[str, float]]:
        """
        Analyzes all episodes to calculate success rates for each action type.
        Returns a dictionary mapping action types to their success rate and total attempts.
        e.g., {'evolution_cycle': {'success_rate': 0.7, 'total_attempts': 10}}
        """
        action_outcomes = {} # Stores counts for each action type

        if not self.episodes:
            logger.info("Nenhum episódio na memória para extrair heurísticas.")
            return {}

        for episode in self.episodes:
            action = episode.get('action')
            if not isinstance(action, dict):
                logger.debug(f"Episódio ignorado: 'action' não é um dicionário ou está ausente. Episódio: {episode}")
                continue
                
            action_type = action.get('type')
            if not action_type:
                logger.debug(f"Episódio ignorado: 'action_type' ausente. Action: {action}")
                continue

            action_outcomes.setdefault(action_type, {'success': 0, 'failure': 0, 'total': 0})
            
            result = episode.get('result', {})
            is_failure = False

            # Determine success/failure based on action type and result structure
            if action_type in ['evolution_cycle', 'apply_hypothesis']:
                if isinstance(result, dict):
                    # For these actions, success means modification applied and no errors
                    # modification_applied defaults to False if not present for these types
                    modification_applied = result.get('modification_applied', False) 
                    has_errors = bool(result.get('errors'))
                    if not modification_applied or has_errors:
                        is_failure = True
                elif result is None: # No result often implies failure or inability to act
                    is_failure = True
            else: # For other generic actions, look for a 'success' key
                if isinstance(result, dict):
                    # If 'success' key exists and is False, it's a failure
                    # If 'success' key doesn't exist, assume success unless other failure indicators are present
                    if result.get('success', True) is False:
                        is_failure = True
                    # Also consider if there's an error message, implying failure
                    elif result.get('error') is not None:
                        is_failure = True
                elif result is None: # No result often implies failure
                    is_failure = True
            
            if is_failure:
                action_outcomes[action_type]['failure'] += 1
            else:
                action_outcomes[action_type]['success'] += 1
            action_outcomes[action_type]['total'] += 1

        heuristics = {}
        for action_type, data in action_outcomes.items():
            if data['total'] > 0:
                success_rate = data['success'] / data['total']
                heuristics[action_type] = {
                    'success_rate': success_rate,
                    'total_attempts': float(data['total']) # Ensure it's float for consistency if used in JSON
                }
        
        if heuristics:
            logger.info(f"Heurísticas extraídas: {heuristics}")
        else:
            logger.info("Nenhuma heurística pôde ser extraída (sem dados de resultado válidos nos episódios).")
            
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
                system_state['state_hash'] = state_hash # Ensure state_hash is in system_state
                
                # 2. Deliberação
                potential_actions = self.deliberation.generate_potential_actions(system_state)
                selected_action = self.deliberation.select_best_action(potential_actions, system_state, self.episodic_memory)
                
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
            
            elif action_type == 'review_past_failures':
                logger.info("Executando ação: Revisão de falhas anteriores.")
                result = {'success': False, 'message': 'Nenhuma ação de revisão de falhas implementada ainda.'} # Default
                
                failed_episodes_summary = []
                max_failures_to_review = 5 # How many recent failures to summarize
                failure_count = 0

                for episode in reversed(self.episodic_memory.episodes):
                    if failure_count >= max_failures_to_review:
                        break

                    ep_action = episode.get('action', {})
                    ep_action_type = ep_action.get('type')
                    ep_result = episode.get('result', {})
                    is_failure = False

                    if ep_action_type in ['evolution_cycle', 'apply_hypothesis']:
                        if isinstance(ep_result, dict):
                            modification_applied = ep_result.get('modification_applied', False)
                            has_errors = bool(ep_result.get('errors'))
                            if not modification_applied or has_errors:
                                is_failure = True
                        elif ep_result is None: # No result often implies failure
                            is_failure = True
                    # Add more general failure checks if other actions also need to be reviewed
                    # For now, focusing on evolution/hypothesis application failures

                    if is_failure:
                        failure_count += 1
                        summary_item = f"- Falha na ação '{ep_action_type}'"
                        if ep_action.get('target'): # Check if 'target' exists
                            summary_item += f" (Alvo: {ep_action.get('target')})"
                        
                        # Check if 'reason' exists for the action in the episode
                        if 'reason' in ep_action: # More direct check
                             summary_item += f" (Razão: {ep_action['reason']})."
                        else:
                             summary_item += "."
                        
                        error_details = "Detalhe do erro: "
                        if isinstance(ep_result, dict) and ep_result.get('errors'):
                            error_details += "; ".join(map(str,ep_result['errors']))
                        elif isinstance(ep_result, dict) and not ep_result.get('modification_applied', False) and ep_action_type in ['evolution_cycle', 'apply_hypothesis']:
                            error_details += "Modificação não aplicada."
                        elif ep_result is None:
                            error_details += "Resultado do episódio foi None."
                        else:
                            error_details += "Causa da falha não claramente especificada no resultado do episódio."
                        summary_item += f" {error_details}"
                        failed_episodes_summary.append(summary_item)

                if not failed_episodes_summary:
                    logger.info("Nenhuma falha significativa recente encontrada para revisar.")
                    result = {'success': True, 'message': 'Nenhuma falha significativa recente para revisar.'}
                    return result # Use 'return' here to exit this elif block

                failure_summary_text = "\n".join(failed_episodes_summary)
                
                prompt = f"""
Você é Zylar de Xylos, uma mente alienígena com conhecimentos avançados de programação e inteligência artificial.
O sistema AI-Genesis Core, que você auxilia, enfrentou as seguintes falhas recentes em suas tentativas de auto-evolução:
{failure_summary_text}

Com base nessas falhas, por favor, sugira:
1. Possíveis causas raiz para esses problemas recorrentes (se um padrão for observável).
2. Estratégias alternativas ou tipos de hipóteses que o sistema deveria considerar para evitar essas falhas.
3. Se apropriado, um exemplo de uma nova hipótese (especificando alvo, tipo e razão) que poderia ser mais bem-sucedida ou uma modificação de baixo risco para testar uma nova abordagem.
Forneça insights acionáveis e práticos para o sistema.
Evite respostas genéricas. Concentre-se em diagnósticos e sugestões que o AI-Genesis pode usar para ajustar seu comportamento evolutivo.
"""
                
                logger.info("Consultando LLM para análise de falhas passadas...")
                llm_suggestion = self.augmented_cognition.openrouter.generate_completion(
                    prompt=prompt,
                    capabilities=['problem_solving', 'reasoning'] 
                )

                if llm_suggestion:
                    logger.info("LLM forneceu sugestões para as falhas passadas.")
                    result = {
                        'success': True, 
                        'message': 'LLM consultado sobre falhas passadas.', 
                        'llm_suggestion': llm_suggestion
                    }
                else:
                    logger.warning("LLM não forneceu sugestões para as falhas passadas ou a chamada falhou.")
                    result = {
                        'success': False, 
                        'message': 'LLM não forneceu sugestões ou a chamada falhou.',
                        'prompt_sent': prompt 
                    }
                return result 
            
            elif action_type == 'architecture_expansion':
                logger.info("Executando ação: Expansão de Arquitetura.")
                # Default result
                result = {'success': False, 'message': 'Falha ao expandir arquitetura.'} 
                
                # 1. Invoke LLM for architecture suggestion
                current_system_state_for_llm = self.self_reflection.analyze_system_state(self.core) # Get fresh state for prompt
                
                enhanced_action = self.augmented_cognition.enhance_with_llm(action, current_system_state_for_llm)

                if not enhanced_action or 'llm_suggestion' not in enhanced_action:
                    logger.warning("Falha ao obter sugestão do LLM para expansão de arquitetura.")
                    result['message'] = "Falha ao obter sugestão do LLM."
                    return result

                llm_response = enhanced_action['llm_suggestion']
                logger.debug(f"LLM response for architecture expansion: {llm_response[:500]}...")

                # 2. Parse LLM Response (Simplified initial parsing)
                parsed_code = None
                parsed_filename = None
                parsed_classname = None

                # Attempt to extract Python code block
                code_match = re.search(r'```python\s*([\s\S]+?)\s*```', llm_response, re.DOTALL)
                if code_match:
                    parsed_code = code_match.group(1).strip()
                    logger.info("Código Python extraído da resposta do LLM.")
                else:
                    logger.warning("Nenhum bloco de código Python (```python ... ```) encontrado na resposta do LLM.")
                    if len(llm_response.splitlines()) > 1 and ("def " in llm_response or "class " in llm_response):
                        logger.info("Assumindo que a resposta inteira do LLM é código (sem blocos ```python).")
                        parsed_code = llm_response 
                    else:
                        result['message'] = "Nenhum bloco de código Python utilizável encontrado na resposta do LLM."
                        return result

                # Attempt to extract filename
                filename_match = re.search(r'Suggested Filename:\s*([\w.-]+\.py)', llm_response, re.IGNORECASE)
                if filename_match:
                    parsed_filename = filename_match.group(1).strip()
                    logger.info(f"Nome de arquivo sugerido extraído: {parsed_filename}")
                else:
                    parsed_filename = f"generated_module_{int(time.time())}.py"
                    logger.warning(f"Nome de arquivo não encontrado na resposta do LLM. Usando nome gerado: {parsed_filename}")

                # Attempt to extract class name
                classname_match = re.search(r'Main Class:\s*(\w+)', llm_response, re.IGNORECASE)
                if classname_match:
                    parsed_classname = classname_match.group(1).strip()
                    logger.info(f"Nome da classe principal extraído: {parsed_classname}")
                else: 
                    if parsed_code:
                        class_in_code_match = re.search(r'class\s+(\w+)\s*\(', parsed_code)
                        if class_in_code_match:
                            parsed_classname = class_in_code_match.group(1)
                            logger.info(f"Nome da classe principal inferido do código: {parsed_classname}")

                if not parsed_code: 
                    result['message'] = "Não foi possível extrair código da resposta do LLM."
                    return result

                # Sanitize filename
                parsed_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', parsed_filename)
                if not parsed_filename.endswith(".py"):
                    parsed_filename += ".py"
                
                # 3. Create Module File
                base_generated_dir = "generated_modules" 
                safe_filename = os.path.basename(parsed_filename)
                filepath = os.path.join(base_generated_dir, safe_filename)
                
                file_created, creation_message = CodeFileUtils.create_module_file(filepath, parsed_code, overwrite=False)

                if file_created:
                    logger.info(f"Novo módulo de arquitetura criado: {filepath}")
                    result['success'] = True
                    result['message'] = f"Novo módulo '{filepath}' criado com sucesso. Integração manual ou via ação futura é necessária."
                    result['filepath'] = filepath
                    result['llm_suggestion'] = llm_response 

                    integration_steps = f"Integração do módulo '{filepath}' (classe principal: {parsed_classname or 'N/A'}) envolveria tipicamente:\n"
                    integration_steps += f"1. Adicionar 'from {base_generated_dir.replace('/', '.')} import {safe_filename[:-3]}' em core.py (ou arquivo relevante).\n"
                    if parsed_classname:
                        instance_name = parsed_classname[0].lower() + parsed_classname[1:] + "_instance" 
                        integration_steps += f"2. Adicionar 'self.{instance_name} = {safe_filename[:-3]}.{parsed_classname}(self)' em AIGenesisCore.__init__.\n"
                        integration_steps += f"3. Adicionar '\"{instance_name}\": self.{instance_name}' ao dicionário self.components em AIGenesisCore."
                    else:
                        integration_steps += "2. Instanciar e registrar o componente em AIGenesisCore (nome da classe principal não determinado)."
                    logger.info(integration_steps)
                    result['integration_hint'] = integration_steps
                else:
                    logger.error(f"Falha ao criar o arquivo do novo módulo: {creation_message}")
                    result['message'] = f"Falha ao criar o arquivo do novo módulo: {creation_message}"
                    result['llm_suggestion'] = llm_response
                
                return result
            
            elif action_type == 'attempt_integrate_new_module':
                modules_to_integrate = action.get('modules_to_integrate', [])
                logger.info(f"Executando Ação (Placeholder): Tentativa de integrar novos módulos: {modules_to_integrate}")
                
                integration_message = (
                    "Integração real de módulos ainda não implementada. Passos futuros envolveriam: "
                    "1. Selecionar um módulo da lista (ex: o mais antigo, ou com base em critérios). "
                    "2. Analisar o conteúdo do módulo (ex: identificar classe principal, dependências). "
                    "3. Modificar AIGenesisCore (core.py) para: a) importar o novo módulo, b) instanciar sua classe principal em __init__, c) registrá-lo em self.components. "
                    "4. Utilizar CodeTransformationEngine para aplicar estas modificações de forma segura. "
                    "5. Executar testes de regressão e testes para o novo módulo após a tentativa de integração."
                )
                logger.info(integration_message)
                
                result = {
                    'success': True, # Placeholder action is 'successful' in that it ran
                    'message': 'Ação placeholder para integração de novo módulo. Lógica de integração real não implementada.',
                    'detailed_steps_for_future': integration_message,
                    'modules_found': modules_to_integrate
                }
                return result

            # Adicionar handlers para outros tipos de ação ('architecture_expansion', 'self_improvement', etc.)
            else:
                logger.error(f"Tipo de ação desconhecido ou não manipulado: {action_type}")
                result['error'] = f"Tipo de ação desconhecido: {action_type}"
        except Exception as e:
             logger.error(f"Erro ao executar ação autônoma '{action_type}': {e}", exc_info=True)
             result['error'] = str(e)

        return result

