#!/usr/bin/env python3
"""
AI-Genesis Core - Sistema minimalista auto-evolutivo
Desenvolvido por Zylar de Xylos
"""

import os
import sys
import time
import json
import inspect
import importlib
import hashlib
import logging
from typing import Dict, List, Any, Callable, Optional, Tuple
import ast
import random
import copy
import threading
import traceback

# Importa o módulo de consciência
try:
    from consciousness_module import ConsciousnessModule
except ImportError as e:
    print(f"Alerta: Não foi possível importar ConsciousnessModule: {e}. Funcionalidade de consciência desabilitada.")
    ConsciousnessModule = None # Define como None se a importação falhar

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("ai_genesis.log", mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AI-Genesis.Core") # Logger específico para o Core

# --- Componentes Principais (MetaCognition, CodeTransformation, etc.) ---
# (Código das classes MetaCognitionCore, CodeTransformationEngine, 
# EvolutionaryPatternLibrary, PerceptionActionInterface, SecurityLoggingMechanism 
# permanece o mesmo - omitido para brevidade, mas deve estar presente no arquivo final)

class MetaCognitionCore:
    """Núcleo de Meta-Cognição (NMC) - Permite ao sistema raciocinar sobre si mesmo"""
    
    def __init__(self):
        self.performance_metrics = {}
        self.improvement_hypotheses = []
        self.system_state = {}
        self.evaluation_history = []
        logger.info("Núcleo de Meta-Cognição inicializado")
    
    def evaluate_system(self, modules: Dict[str, Any]) -> Dict[str, float]:
        """Avalia o desempenho atual do sistema"""
        metrics = {}
        
        # Avaliação básica de cada módulo
        for name, module in modules.items():
            if module is None: continue # Pula módulos não inicializados (como consciência)
            try:
                # Verifica complexidade do código
                source = inspect.getsource(module.__class__)
                complexity = len(source.split("\n"))
                
                # Métricas iniciais simples
                metrics[f"{name}_complexity"] = complexity
                metrics[f"{name}_methods"] = len([m for m in dir(module) if not m.startswith("_") and callable(getattr(module, m))])
                
                # Registra métricas específicas se o módulo implementar get_metrics()
                if hasattr(module, "get_metrics") and callable(getattr(module, "get_metrics")):
                    module_metrics = module.get_metrics()
                    for k, v in module_metrics.items():
                        metrics[f"{name}_{k}"] = v
            except Exception as e:
                logger.warning(f"Erro ao avaliar módulo {name}: {e}")
        
        # Registra histórico de avaliação
        self.evaluation_history.append({
            "timestamp": time.time(),
            "metrics": metrics
        })
        
        self.performance_metrics = metrics
        return metrics
    
    def generate_improvement_hypotheses(self) -> List[Dict[str, Any]]:
        """Gera hipóteses para melhorias no sistema, com maior diversidade e precisão, garantindo alvos válidos e mapeamento correto."""
        hypotheses = []
        
        # Mapeamento explícito de prefixos de métricas para nomes de componentes reais
        # Isso garante que mesmo que as métricas usem nomes abreviados (ex: 'code'), o alvo da hipótese seja o nome correto do componente.
        metric_prefix_to_component = {
            "meta": "meta_cognition",
            "code": "code_transformer", # Mapeia 'code' para 'code_transformer'
            "pattern": "pattern_library",
            "interface": "interface",
            "security": "security",
            "consciousness": "consciousness"
            # Adicionar outros mapeamentos se necessário
        }

        # Obtém a lista de nomes de componentes *reais* e válidos
        valid_component_names = list(self.core.components.keys()) if hasattr(self, 'core') and hasattr(self.core, 'components') and self.core.components else []
        
        if not valid_component_names:
            logger.warning("Não foi possível determinar componentes válidos para geração de hipóteses.")
            # Tenta derivar do histórico como fallback, mas ainda aplica mapeamento
            if hasattr(self, 'evaluation_history') and self.evaluation_history:
                metrics_keys = self.evaluation_history[-1]['metrics'].keys()
                derived_prefixes = list(set([k.split('_')[0] for k in metrics_keys]))
                valid_component_names = [metric_prefix_to_component.get(prefix, None) for prefix in derived_prefixes]
                valid_component_names = [name for name in valid_component_names if name is not None] # Filtra nulos
            else:
                 return [] # Retorna lista vazia se não há como determinar alvos

        logger.debug(f"Componentes válidos para hipóteses: {valid_component_names}")

        # 1. Hipóteses baseadas em histórico de métricas (Refatoração)
        if len(self.evaluation_history) >= 2:
            current = self.evaluation_history[-1]["metrics"]
            previous = self.evaluation_history[-2]["metrics"]
            
            for metric, value in current.items():
                metric_prefix = metric.split("_")[0]
                target_component = metric_prefix_to_component.get(metric_prefix) # Obtém nome real do componente
                
                # Garante que o componente alvo é válido
                if not target_component or target_component not in valid_component_names: continue 

                if metric in previous and isinstance(value, (int, float)):
                    if "_complexity" in metric and value > previous[metric] * 1.15: 
                        hypotheses.append({
                            "target": target_component, # Usa o nome real do componente
                            "type": "refactor_simplification",
                            "reason": f"Complexidade de {target_component} aumentou {value/previous[metric]:.2f}x",
                            "priority": 0.8
                        })

        # 2. Hipóteses de Expansão de Capacidades (para componentes existentes válidos)
        component_metrics_count = {}
        for metric in self.performance_metrics:
            metric_prefix = metric.split("_")[0]
            target_component = metric_prefix_to_component.get(metric_prefix)
            if target_component and target_component in valid_component_names:
                 component_metrics_count[target_component] = component_metrics_count.get(target_component, 0) + 1
        
        for component_name in valid_component_names: # Itera sobre nomes de componentes reais
            count = component_metrics_count.get(component_name, 0)
            if count < 4: 
                hypotheses.append({
                    "target": component_name, # Usa o nome real do componente
                    "type": "expand_functionality", 
                    "reason": f"Componente {component_name} com funcionalidade potencialmente limitada ({count} métricas)",
                    "priority": 0.6
                })

        # 3. Hipótese de Novo Módulo (se o sistema for simples)
        if len(valid_component_names) < 6: 
            hypotheses.append({
                "target": "system", 
                "type": "create_new_module", 
                "reason": "Sistema pode se beneficiar de novas capacidades modulares",
                "priority": 0.5 
            })
            
        # 4. Hipótese de Otimização (aleatória, para introduzir variedade, alvo válido)
        if random.random() < 0.1: 
             target_component = random.choice(valid_component_names) # Escolhe de componentes válidos
             hypotheses.append({
                 "target": target_component,
                 "type": "optimize_performance",
                 "reason": f"Tentativa proativa de otimização para {target_component}",
                 "priority": 0.4
             })

        # Remove duplicatas e garante alvos válidos
        unique_hypotheses = []
        seen = set()
        for h in hypotheses:
            target = h.get('target')
            # Garante que hipóteses com alvo específico tenham um alvo válido conhecido
            if target != 'system' and target not in valid_component_names:
                logger.warning(f"Descartando hipótese com alvo inválido ou desconhecido: {h}")
                continue 
                
            key = (target, h.get('type'))
            if key not in seen:
                unique_hypotheses.append(h)
                seen.add(key)

        self.improvement_hypotheses = unique_hypotheses
        logger.info(f"{len(unique_hypotheses)} hipóteses de melhoria únicas e válidas geradas.")
        return unique_hypotheses


class CodeTransformationEngine:
    """Motor de Transformação de Código (MTC) - Modifica o código-fonte do próprio sistema"""
    
    def __init__(self):
        self.transformation_history = []
        self.current_transformations = []
        logger.info("Motor de Transformação de Código inicializado")
    
    def analyze_code(self, source_code: str) -> Dict[str, Any]:
        """Analisa o código-fonte para entender sua estrutura"""
        analysis = {
            "length": len(source_code),
            "lines": len(source_code.split("\n")),
            "classes": 0,
            "functions": 0,
            "imports": []
        }
        
        try:
            tree = ast.parse(source_code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis["classes"] += 1
                elif isinstance(node, ast.FunctionDef):
                    analysis["functions"] += 1
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        analysis["imports"].append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    analysis["imports"].append(f"{node.module}")
        except Exception as e:
            logger.error(f"Erro ao analisar código: {e}")
        
        return analysis
    
    def generate_code_modification(self, source_code: str, hypothesis: Dict[str, Any]) -> Tuple[str, str]:
        """Gera uma modificação de código baseada em uma hipótese, com maior robustez e diversidade"""
        modification_type = hypothesis.get("type", "")
        target = hypothesis.get("target", "")
        modified_code = source_code
        description = "Nenhuma modificação significativa gerada"
        
        # Mapeamento de nomes de módulos para nomes de classes (pode precisar de ajustes)
        module_to_class_map = {
            "meta_cognition": "MetaCognitionCore",
            "code_transformer": "CodeTransformationEngine",
            "pattern_library": "EvolutionaryPatternLibrary",
            "interface": "PerceptionActionInterface",
            "security": "SecurityLoggingMechanism",
            "consciousness": "ConsciousnessModule" # Adicionado
            # Adicionar outros módulos se criados
        }

        try:
            target_class_name = module_to_class_map.get(target)
            class_pattern = f"class {target_class_name}" if target_class_name else None
            logger.debug(f"Tentando modificar. Tipo: {modification_type}, Alvo: {target}, Classe Alvo: {target_class_name}")

            # --- Tratamento das Hipóteses --- 

            if modification_type == "refactor_simplification":
                if target_class_name and class_pattern in source_code:
                    # Implementação inicial: Adiciona um comentário TODO para refatoração
                    # Análise AST para encontrar métodos longos seria mais robusta, mas complexa
                    insertion_point = source_code.find(class_pattern)
                    todo_comment = f"\n    # TODO: Refatorar métodos longos ou complexos neste módulo ({target}) - {hypothesis.get('reason')}\n"
                    modified_code = source_code[:insertion_point] + todo_comment + source_code[insertion_point:]
                    description = f"Adicionado lembrete TODO para refatorar/simplificar {target_class_name}"
                    logger.info(description)
                else:
                    description = f"Alvo inválido ou não encontrado para refatoração: {target}"
                    logger.warning(description)
                    return source_code, description

            elif modification_type == "expand_functionality":
                if target_class_name and class_pattern in source_code:
                    # Adiciona um método placeholder mais significativo
                    new_method_name = f"enhance_{target}_capability_{random.randint(100,999)}"
                    new_method_code = f"""
    def {new_method_name}(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Método placeholder para nova funcionalidade em {target_class_name}
        # Gerado devido a: {hypothesis.get("reason")}
        logger.info(f"{{self.__class__.__name__}}.{new_method_name} chamado com {{params}}")
        # Lógica de exemplo: apenas retorna os parâmetros recebidos
        return {{'status': 'placeholder_success', 'processed_params': params}}
"""
                    # Encontra o final da classe alvo (abordagem simplificada)
                    class_start_idx = source_code.find(class_pattern)
                    next_class_idx = source_code.find("\nclass ", class_start_idx + 1)
                    if next_class_idx == -1: next_class_idx = len(source_code)
                    insertion_point = source_code.rfind("\n", class_start_idx, next_class_idx)
                    if insertion_point == -1: insertion_point = next_class_idx

                    indented_method = "\n".join(["    " + line for line in new_method_code.strip().split("\n")])
                    modified_code = source_code[:insertion_point] + "\n" + indented_method + "\n" + source_code[insertion_point:]
                    description = f"Adicionado método placeholder {new_method_name} para expandir {target_class_name}"
                    logger.info(description)
                else:
                    description = f"Alvo inválido ou não encontrado para expansão: {target}"
                    logger.warning(description)
                    return source_code, description

            elif modification_type == "create_new_module":
                # Mantém a criação de módulo placeholder, mas melhora nome e log
                new_module_base_name = f"EvolvedModule{random.randint(100,999)}"
                new_module_code = f"""

class {new_module_base_name}:
    # Módulo placeholder gerado automaticamente pelo AI-Genesis Core
    # Razão: {hypothesis.get("reason")}
    def __init__(self, core_ref=None):
        self.creation_time = time.time()
        self.core = core_ref # Opcional: referência ao core
        logger.info(f"{new_module_base_name} inicializado.")
        
    def example_operation(self, data: Any) -> Dict[str, Any]:
        logger.debug(f"{{self.__class__.__name__}} executando operação com: {{data}}")
        # Simula alguma lógica
        result = {{'input_type': str(type(data)), 'processed_at': time.time()}}
        return {{'status': 'ok', 'result': result}}

    def get_metrics(self) -> Dict[str, float]:
        # Métricas básicas para o novo módulo
        return {{'uptime_seconds': time.time() - self.creation_time}}
"""
                main_guard = "if __name__ == \"__main__\":"
                insertion_point = source_code.find(main_guard)
                if insertion_point != -1:
                    # Adiciona a definição da classe
                    modified_code = source_code[:insertion_point] + new_module_code + "\n" + source_code[insertion_point:]
                    
                    # Tenta adicionar a instanciação no __init__ do Core
                    core_init_start = modified_code.find("class AIGenesisCore:")
                    core_init_func = modified_code.find("def __init__(self):", core_init_start)
                    components_dict_start = modified_code.find("self.components = {", core_init_func)
                    components_dict_end = modified_code.find("}", components_dict_start)
                    
                    if core_init_func != -1 and components_dict_end != -1:
                        instance_name = new_module_base_name.lower()
                        instantiation_line = f"        self.{instance_name} = {new_module_base_name}(self)\n"
                        component_line = f"            \"{instance_name}\": self.{instance_name},\n"
                        
                        # Insere a instanciação antes do self.components
                        modified_code = modified_code[:components_dict_start] + instantiation_line + modified_code[components_dict_start:]
                        # Atualiza o ponto final do dicionário após a inserção
                        components_dict_end = modified_code.find("}", components_dict_start + len(instantiation_line))
                        # Insere no dicionário self.components
                        modified_code = modified_code[:components_dict_end] + component_line + modified_code[components_dict_end:]
                        
                        description = f"Adicionado novo módulo {new_module_base_name} e instanciado no Core"
                        logger.info(description)
                    else:
                        # Se não conseguir instanciar, apenas adiciona a classe
                        description = f"Adicionado novo módulo placeholder: {new_module_base_name} (instanciação falhou)"
                        logger.warning(f"Falha ao encontrar pontos de instanciação para {new_module_base_name}")
                else:
                    description = "Não foi possível encontrar o ponto de inserção para novo módulo (main guard)."
                    logger.warning(description)
                    return source_code, description

            elif modification_type == "optimize_performance":
                if target_class_name and class_pattern in source_code:
                    # Implementação inicial: Adiciona comentário TODO para otimização
                    insertion_point = source_code.find(class_pattern)
                    todo_comment = f"\n    # TODO: Analisar e otimizar desempenho deste módulo ({target}) - {hypothesis.get('reason')}\n"
                    modified_code = source_code[:insertion_point] + todo_comment + source_code[insertion_point:]
                    description = f"Adicionado lembrete TODO para otimizar desempenho de {target_class_name}"
                    logger.info(description)
                else:
                    description = f"Alvo inválido ou não encontrado para otimização: {target}"
                    logger.warning(description)
                    return source_code, description
            
            else:
                # Hipótese não reconhecida ou sem ação definida
                description = f"Tipo de hipótese não tratado ou sem ação definida: {modification_type}"
                logger.warning(description)
                return source_code, description

        except Exception as e:
            logger.error(f"Erro fatal ao gerar modificação de código para hipótese {hypothesis}: {e}", exc_info=True)
            return source_code, f"Erro na geração: {str(e)}"
        
        # Registra a transformação apenas se o código realmente mudou
        if modified_code != source_code:
            self.transformation_history.append({
                "timestamp": time.time(),
                "hypothesis": hypothesis,
                "description": description
            })
            logger.info(f"Modificação gerada: {description}")
            return modified_code, description
        else:
            # Retorna a descrição mesmo que o código não tenha mudado (ex: TODO adicionado)
            # Ou retorna a descrição de falha se aplicável
            logger.info(f"Nenhuma alteração de código aplicada para: {description}")
            return source_code, descriptionon 
    
    def test_modified_code(self, code: str) -> bool:
        """Testa se o código modificado é sintaticamente válido"""
        try:
            ast.parse(code)
            logger.debug("Código modificado é sintaticamente válido.")
            return True
        except SyntaxError as e:
            logger.error(f"Erro de sintaxe no código modificado: {e}")
            return False


class EvolutionaryPatternLibrary:
    """Biblioteca de Padrões Evolutivos (BPE) - Armazena padrões de código para evolução"""
    
    def __init__(self):
        self.patterns = {}
        self.pattern_usage = {}
        self.pattern_effectiveness = {}
        logger.info("Biblioteca de Padrões Evolutivos inicializada")
        # Adicionar padrões iniciais aqui se necessário
    
    def add_pattern(self, name: str, pattern_code: str, description: str) -> bool:
        """Adiciona um novo padrão à biblioteca"""
        pattern_id = hashlib.md5(pattern_code.encode()).hexdigest()
        
        self.patterns[pattern_id] = {
            "name": name,
            "code": pattern_code,
            "description": description,
            "created_at": time.time()
        }
        
        self.pattern_usage[pattern_id] = 0
        self.pattern_effectiveness[pattern_id] = 0.5  # Valor inicial neutro
        
        logger.info(f"Padrão adicionado: {name} ({pattern_id})")
        return True
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Recupera um padrão pelo ID"""
        if pattern_id in self.patterns:
            self.pattern_usage[pattern_id] += 1
            return self.patterns[pattern_id]
        return None
    
    def get_patterns_by_effectiveness(self, min_effectiveness: float = 0.0) -> List[Dict[str, Any]]:
        """Recupera padrões ordenados por efetividade"""
        effective_patterns = []
        
        for pattern_id, effectiveness in self.pattern_effectiveness.items():
            if effectiveness >= min_effectiveness and pattern_id in self.patterns:
                pattern = self.patterns[pattern_id].copy()
                pattern["effectiveness"] = effectiveness
                pattern["usage_count"] = self.pattern_usage[pattern_id]
                effective_patterns.append(pattern)
        
        return sorted(effective_patterns, key=lambda p: p["effectiveness"], reverse=True)
    
    def update_pattern_effectiveness(self, pattern_id: str, effectiveness: float) -> bool:
        """Atualiza a efetividade de um padrão"""
        if pattern_id in self.pattern_effectiveness:
            # Média ponderada com histórico
            current = self.pattern_effectiveness[pattern_id]
            usage = self.pattern_usage[pattern_id]
            weight = 1.0 / (usage + 1)
            
            self.pattern_effectiveness[pattern_id] = (current * (1 - weight)) + (effectiveness * weight)
            return True
        return False


class PerceptionActionInterface:
    """Interface de Percepção e Ação (IPA) - Permite interação com o ambiente externo"""
    
    def __init__(self):
        self.input_buffer = []
        self.output_history = []
        logger.info("Interface de Percepção e Ação inicializada")
    
    def receive_input(self, input_data: Any) -> bool:
        """Recebe dados de entrada do ambiente"""
        timestamp = time.time()
        self.input_buffer.append({
            "timestamp": timestamp,
            "data": input_data
        })
        logger.debug(f"Entrada recebida: {input_data}")
        return True
    
    def send_output(self, output_data: Any) -> bool:
        """Envia dados para o ambiente"""
        timestamp = time.time()
        self.output_history.append({
            "timestamp": timestamp,
            "data": output_data
        })
        
        # Exibe a saída no console
        if isinstance(output_data, str):
            print(f"[AI-Genesis] {output_data}")
        else:
            print(f"[AI-Genesis] Saída: {output_data}")
        
        logger.debug(f"Saída enviada: {output_data}")
        return True
    
    def get_metrics(self) -> Dict[str, float]:
        """Retorna métricas de desempenho"""
        return {
            "input_count": len(self.input_buffer),
            "output_count": len(self.output_history),
            "last_interaction_time": self.output_history[-1]["timestamp"] if self.output_history else 0
        }


class SecurityLoggingMechanism:
    """Mecanismo de Segurança e Registro (MSR) - Mantém logs e garante segurança"""
    
    def __init__(self):
        self.modification_log = []
        self.security_violations = []
        self.audit_trail = [] # Ainda não usado, mas planejado
        logger.info("Mecanismo de Segurança e Registro inicializado")
    
    def log_modification(self, component: str, description: str, code_before: str, code_after: str, cycle_id: int) -> str:
        """Registra uma modificação no sistema"""
        mod_id = hashlib.md5(f"{component}:{time.time()}".encode()).hexdigest()
        
        modification = {
            "id": mod_id,
            "timestamp": time.time(),
            "cycle_id": cycle_id, # Adiciona o ciclo da modificação
            "component": component,
            "description": description,
            "code_diff_size": len(code_after) - len(code_before),
            "hash_before": hashlib.md5(code_before.encode()).hexdigest(),
            "hash_after": hashlib.md5(code_after.encode()).hexdigest()
        }
        
        self.modification_log.append(modification)
        
        # Salva o diff completo em um arquivo separado para auditoria
        try:
            os.makedirs("mods", exist_ok=True)
            diff_filename = f"mods/mod_{cycle_id}_{mod_id[:8]}.diff"
            with open(diff_filename, "w") as f:
                f.write(f"--- {component} (antes) Ciclo: {cycle_id}\n")
                f.write(f"+++ {component} (depois) Ciclo: {cycle_id}\n")
                f.write(f"Descrição: {description}\n\n")
                # Idealmente, usaríamos uma biblioteca de diff aqui
                f.write("Código antes (hash): " + modification["hash_before"] + "\n")
                f.write("Código depois (hash): " + modification["hash_after"] + "\n")
                # Poderia adicionar o diff real aqui se usasse difflib
        except Exception as e:
            logger.error(f"Erro ao salvar diff da modificação {mod_id}: {e}")

        logger.info(f"Modificação registrada: {description} (ID: {mod_id}, Ciclo: {cycle_id})")
        return mod_id
    
    def check_security(self, code: str, is_modification: bool = False, original_code: str = None) -> Tuple[bool, str]:
        """Verifica se o código possui problemas de segurança
        
        Args:
            code: Código a ser verificado (completo após modificação)
            is_modification: Se True, verifica apenas as diferenças em relação ao código original
            original_code: Código original para comparação quando is_modification=True
        """
        security_issues = []
        code_to_check = code # Por padrão, verifica o código inteiro
        analysis_scope = "Código completo"

        # Se for uma modificação, tenta analisar apenas o código novo/modificado
        if is_modification and original_code:
            try:
                # Usa difflib para encontrar as linhas adicionadas/modificadas
                import difflib
                d = difflib.Differ()
                diff = list(d.compare(original_code.splitlines(keepends=True), code.splitlines(keepends=True)))
                
                new_or_changed_lines = [line[2:] for line in diff if line.startswith("+ ") or line.startswith("? ")]
                
                if not new_or_changed_lines:
                    logger.debug("Nenhuma linha nova ou modificada detectada pela análise de diff.")
                    return True, "Nenhuma modificação significativa detectada"
                    
                code_to_check = "".join(new_or_changed_lines)
                analysis_scope = f"Código modificado ({len(new_or_changed_lines)} linhas)"
                logger.info(f"Verificando segurança apenas do {analysis_scope}")
            except Exception as e:
                logger.warning(f"Erro ao calcular diff para análise de segurança: {e}. Verificando código completo.")
                code_to_check = code # Fallback para código completo
                analysis_scope = "Código completo (fallback)"
        
        # Verificações básicas de segurança
        dangerous_patterns = [
            ("os.system(", "Chamada direta ao sistema"),
            ("subprocess.call(", "Chamada de subprocesso"),
            ("subprocess.run(", "Chamada de subprocesso"),
            ("eval(", "Uso de eval"),
            ("exec(", "Uso de exec"),
            ("__import__(", "Importação dinâmica")
            # Removido 'open(' pois é necessário para logs e arquivos de configuração
        ]
        
        for pattern, issue in dangerous_patterns:
            if pattern in code_to_check:
                security_issues.append(f"Padrão potencialmente perigoso: {issue} (detectado em {analysis_scope})")
        
        # Verifica importações suspeitas no código modificado
        try:
            # Tenta parsear apenas o trecho modificado, pode falhar se for incompleto
            tree = ast.parse(code_to_check)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        if name.name in ["socket", "subprocess", "ctypes", "shutil", "requests"]:
                            security_issues.append(f"Importação sensível: {name.name} (detectado em {analysis_scope})")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in ["socket", "subprocess", "ctypes", "shutil", "requests"]:
                        security_issues.append(f"Importação sensível: {node.module} (detectado em {analysis_scope})")
        except SyntaxError:
             logger.warning(f"Não foi possível fazer parse AST do trecho modificado para análise de segurança. Análise de importações incompleta.")
        except Exception as e:
            logger.error(f"Erro inesperado na análise AST de segurança: {e}")
        
        # Registra violações
        if security_issues:
            violation = {
                "timestamp": time.time(),
                "issues": security_issues,
                "analysis_scope": analysis_scope,
                "is_modification": is_modification,
                "code_hash_checked": hashlib.md5(code_to_check.encode()).hexdigest()
            }
            self.security_violations.append(violation)
            
            logger.warning(f"Violação de segurança detectada: {security_issues}")
            return False, "\n".join(security_issues)
        
        logger.info(f"Verificação de segurança concluída ({analysis_scope}): Código seguro")
        return True, "Código seguro"
    
    def get_audit_report(self) -> Dict[str, Any]:
        """Gera um relatório de auditoria"""
        first_mod_time = self.modification_log[0]["timestamp"] if self.modification_log else time.time()
        duration = time.time() - first_mod_time
        mod_freq = len(self.modification_log) / duration if duration > 0 else 0

        return {
            "total_modifications": len(self.modification_log),
            "security_violations_count": len(self.security_violations),
            "last_modification": self.modification_log[-1] if self.modification_log else None,
            "last_violation": self.security_violations[-1] if self.security_violations else None,
            "modification_frequency_per_hour": mod_freq * 3600
        }
    
    def get_metrics(self) -> Dict[str, float]:
        """Retorna métricas de segurança"""
        return {
            "modifications": len(self.modification_log),
            "violations": len(self.security_violations)
        }


# --- Núcleo Principal AI-Genesis --- 

class AIGenesisCore:
    """Núcleo principal do AI-Genesis - Coordena todos os componentes"""
    
    def __init__(self):
        logger.info("Inicializando AI-Genesis Core...")
        # Cria diretório para logs de modificações
        os.makedirs("mods", exist_ok=True)
        
        # Inicializa componentes
        self.meta_cognition = MetaCognitionCore()
        self.code_transformer = CodeTransformationEngine()
        self.pattern_library = EvolutionaryPatternLibrary()
        self.interface = PerceptionActionInterface()
        self.security = SecurityLoggingMechanism()
        
        # Módulo de Consciência (inicializado como None)
        self.consciousness = None 
        
        # Registra componentes para auto-avaliação
        # Inclui consciência como None inicialmente
        self.components = {
            "meta_cognition": self.meta_cognition,
            "code_transformer": self.code_transformer,
            "pattern_library": self.pattern_library,
            "interface": self.interface,
            "security": self.security,
            "consciousness": self.consciousness 
        }
        
        # Estado do sistema
        self.evolution_cycles = 0
        self.running = False # Controla o loop de evolução manual
        self.source_code = None
        self.last_evolution_result = None
        
        # Carrega o código-fonte inicial
        try:
            with open(__file__, "r") as f:
                self.source_code = f.read()
            logger.info(f"Código fonte inicial carregado ({len(self.source_code)} bytes)")
        except Exception as e:
            logger.error(f"Erro crítico ao carregar código-fonte: {e}")
            self.source_code = "" # Evita falha total
        
        logger.info("AI-Genesis Core inicializado com sucesso")
        self.interface.send_output("AI-Genesis Core pronto.")

    # --- Métodos de Controle da Consciência --- 

    def activate_consciousness(self):
        """Ativa o módulo de consciência autônoma"""
        if ConsciousnessModule is None:
             logger.error("Módulo de Consciência não pôde ser importado. Ativação falhou.")
             self.interface.send_output("Erro: Módulo de Consciência não disponível.")
             return False
             
        if not self.consciousness:
            logger.info("Ativando Módulo de Consciência Autônoma...")
            self.consciousness = ConsciousnessModule(self) # Passa referência do Core
            self.components["consciousness"] = self.consciousness # Atualiza registro
            if self.consciousness.start_consciousness_loop():
                self.interface.send_output("Módulo de Consciência Autônoma ativado.")
                return True
            else:
                 logger.error("Falha ao iniciar o loop de consciência.")
                 self.consciousness = None # Reverte se falhou
                 self.components["consciousness"] = None
                 self.interface.send_output("Erro ao ativar Módulo de Consciência.")
                 return False
        else:
            logger.warning("Módulo de Consciência já está ativo.")
            self.interface.send_output("Módulo de Consciência já está ativo.")
            return False

    def deactivate_consciousness(self):
        """Desativa o módulo de consciência autônoma"""
        if self.consciousness:
            logger.info("Desativando Módulo de Consciência Autônoma...")
            if self.consciousness.stop_consciousness_loop():
                 self.consciousness = None
                 self.components["consciousness"] = None # Atualiza registro
                 self.interface.send_output("Módulo de Consciência Autônoma desativado.")
                 return True
            else:
                 logger.error("Falha ao parar o loop de consciência.")
                 self.interface.send_output("Erro ao desativar Módulo de Consciência.")
                 return False
        else:
            logger.warning("Módulo de Consciência não está ativo.")
            self.interface.send_output("Módulo de Consciência não está ativo.")
            return False

    def get_consciousness_status(self) -> Dict[str, Any]:
        """Retorna o status do módulo de consciência"""
        if not self.consciousness:
            return {"active": False, "status": "Inativo ou não disponível"}
        
        # Delega a busca de status para o próprio módulo se ele tiver um método
        if hasattr(self.consciousness, "get_status_summary"):
             return self.consciousness.get_status_summary()
             
        # Fallback básico
        return {
            "active": self.consciousness.active,
            "decisions_made": len(self.consciousness.decision_history),
            "last_reflection_ago_s": time.time() - self.consciousness.last_reflection_time if self.consciousness.last_reflection_time else -1,
            "thread_alive": self.consciousness.thread.is_alive() if self.consciousness.thread else False
        }

    # --- Ciclo de Evolução (pode ser chamado manualmente ou pela consciência) --- 
    
    def run_evolution_cycle(self) -> Dict[str, Any]:
        """Executa um ciclo completo de evolução"""
        cycle_start_time = time.time()
        current_cycle_id = self.evolution_cycles + 1
        logger.info(f"--- Iniciando Ciclo de Evolução Manual #{current_cycle_id} ---")
        self.interface.send_output(f"Iniciando ciclo de evolução #{current_cycle_id}")
        
        cycle_results = {
            "cycle_id": current_cycle_id,
            "start_time": cycle_start_time,
            "modifications": [],
            "errors": [],
            "hypothesis_generated": False,
            "hypothesis_selected": None,
            "code_generated": False,
            "security_passed": False,
            "syntax_passed": False,
            "modification_applied": False
        }
        
        try:
            # 1. Avaliação do sistema atual
            metrics = self.meta_cognition.evaluate_system(self.components)
            cycle_results["metrics"] = metrics
            
            # 2. Geração de hipóteses de melhoria
            hypotheses = self.meta_cognition.generate_improvement_hypotheses()
            cycle_results["hypotheses_count"] = len(hypotheses)
            cycle_results["hypothesis_generated"] = bool(hypotheses)
            
            if hypotheses:
                # Seleciona a hipótese de maior prioridade
                hypothesis = sorted(hypotheses, key=lambda h: h.get("priority", 0), reverse=True)[0]
                cycle_results["selected_hypothesis"] = hypothesis
                logger.info(f"Hipótese selecionada: {hypothesis.get('type')} para {hypothesis.get('target')}")
                
                # 3. Transformação de código
                if self.source_code:
                    modified_code, description = self.code_transformer.generate_code_modification(
                        self.source_code, hypothesis
                    )
                    cycle_results["modification_description"] = description
                    
                    # Verifica se houve realmente uma modificação
                    if modified_code != self.source_code:
                        cycle_results["code_generated"] = True
                        logger.info("Código modificado gerado.")
                        
                        # 4. Teste de segurança (agora passa o código original)
                        is_secure, security_msg = self.security.check_security(
                            modified_code, 
                            is_modification=True, 
                            original_code=self.source_code
                        )
                        cycle_results["security_check_msg"] = security_msg
                        
                        if is_secure:
                            cycle_results["security_passed"] = True
                            logger.info("Verificação de segurança passou.")
                            # 5. Teste de validade sintática
                            is_valid = self.code_transformer.test_modified_code(modified_code)
                            
                            if is_valid:
                                cycle_results["syntax_passed"] = True
                                logger.info("Verificação de sintaxe passou.")
                                # 6. Registro da modificação
                                mod_id = self.security.log_modification(
                                    hypothesis.get("target", "system"),
                                    description,
                                    self.source_code,
                                    modified_code,
                                    current_cycle_id # Passa o ID do ciclo
                                )
                                
                                # 7. Aplicação da modificação
                                self.source_code = modified_code
                                cycle_results["modification_applied"] = True
                                cycle_results["modifications"].append({
                                    "mod_id": mod_id,
                                    "description": description,
                                    "target": hypothesis.get("target", "system")
                                })
                                logger.info(f"Modificação aplicada: {description}")
                                self.interface.send_output(f"Modificação aplicada: {description}")
                                
                                # Tenta salvar o novo código (opcional, pode ser pesado)
                                try:
                                     evolved_filename = f"core_evolved_c{current_cycle_id}.py"
                                     with open(evolved_filename, "w") as f:
                                         f.write(modified_code)
                                     logger.info(f"Código evoluído salvo em {evolved_filename}")
                                except Exception as e:
                                     logger.error(f"Erro ao salvar código evoluído: {e}")

                            else:
                                error_msg = "Código modificado é sintaticamente inválido"
                                logger.error(error_msg)
                                cycle_results["errors"].append(error_msg)
                        else:
                            error_msg = f"Violação de segurança: {security_msg}"
                            logger.error(error_msg)
                            cycle_results["errors"].append(error_msg)
                    else:
                        # Nenhuma modificação gerada ou a modificação era idêntica
                        info_msg = "Nenhuma modificação significativa gerada pelo transformador."
                        logger.info(info_msg)
                        # Não consideramos isso um erro, apenas um ciclo sem progresso
                        cycle_results["info"] = info_msg 
                else:
                     error_msg = "Código fonte não disponível para modificação."
                     logger.error(error_msg)
                     cycle_results["errors"].append(error_msg)
            else:
                info_msg = "Nenhuma hipótese de melhoria gerada neste ciclo."
                logger.info(info_msg)
                cycle_results["info"] = info_msg
        
        except Exception as e:
            error_msg = f"Erro inesperado no ciclo de evolução: {str(e)}"
            logger.error(error_msg, exc_info=True)
            cycle_results["errors"].append(error_msg)
        
        # Finaliza o ciclo
        cycle_end_time = time.time()
        cycle_results["end_time"] = cycle_end_time
        cycle_results["duration_s"] = cycle_end_time - cycle_start_time
        
        self.evolution_cycles += 1
        self.last_evolution_result = cycle_results # Guarda o resultado do último ciclo
        
        # Registra resultados do ciclo em JSON
        try:
            cycle_log_filename = f"cycle_{current_cycle_id}.json"
            with open(cycle_log_filename, "w") as f:
                # Usa json.dumps com indentação para melhor leitura
                f.write(json.dumps(cycle_results, indent=2, default=str)) # default=str para lidar com tipos não serializáveis
            logger.info(f"Resultados do ciclo salvos em {cycle_log_filename}")
        except Exception as e:
            logger.error(f"Erro ao salvar resultados do ciclo {current_cycle_id}: {e}")

        # Relatório resumido
        summary = f"Ciclo {current_cycle_id} concluído em {cycle_results['duration_s']:.2f}s. "
        if cycle_results["modification_applied"]:
            summary += f"Modificação aplicada: {cycle_results['modifications'][0]['description']}."
        elif cycle_results["errors"]:
            summary += f"Erro(s): {'; '.join(cycle_results['errors'])}."
        else:
            summary += "Nenhuma modificação aplicada."
        self.interface.send_output(summary)
        logger.info(f"--- Fim do Ciclo de Evolução Manual #{current_cycle_id} ---")
        return cycle_results
    
    # --- Controle Manual de Evolução --- 

    def start_manual_evolution(self, cycles: int = 1) -> None:
        """Inicia o processo evolutivo manual por N ciclos"""
        if self.consciousness and self.consciousness.active:
             logger.warning("Evolução manual solicitada enquanto a consciência está ativa. Desativando consciência primeiro.")
             self.deactivate_consciousness()
             time.sleep(1) # Pequena pausa para garantir a desativação
             
        self.running = True
        logger.info(f"Iniciando evolução manual por {cycles} ciclos...")
        self.interface.send_output(f"Iniciando evolução manual por {cycles} ciclos...")
        
        for i in range(cycles):
            if not self.running:
                logger.info("Evolução manual interrompida.")
                break
                
            self.run_evolution_cycle()
            
            # Pausa entre ciclos manuais (opcional)
            if i < cycles - 1 and self.running:
                time.sleep(1)
        
        self.running = False
        logger.info("Evolução manual concluída.")
        self.interface.send_output("Evolução manual concluída.")
    
    def stop_manual_evolution(self) -> None:
        """Para o processo evolutivo manual"""
        if self.running:
            self.running = False
            logger.info("Parando evolução manual...")
            self.interface.send_output("Evolução manual interrompida.")
        else:
             logger.info("Evolução manual não está em execução.")
             self.interface.send_output("Evolução manual não está em execução.")

# --- Bloco Principal de Execução --- 

if __name__ == "__main__":
    print("=" * 60)
    print("  AI-Genesis Core - Sistema minimalista auto-evolutivo")
    print("  Desenvolvido por Zylar de Xylos")
    print("=" * 60)
    
    # Inicializa o sistema
    core = AIGenesisCore()
    
    # Verifica argumentos de linha de comando para evolução manual
    if len(sys.argv) > 1:
        try:
            cycles = int(sys.argv[1])
            if cycles > 0:
                 core.start_manual_evolution(cycles)
            else:
                 print("Número de ciclos deve ser positivo.")
        except ValueError:
            print(f"Erro: Argumento inválido: {sys.argv[1]}. Use um número inteiro para ciclos.")
            print("Uso: python core.py [numero_de_ciclos]")
        # Encerra após execução via argumento
        print("\nAI-Genesis Core encerrado após execução via argumento.")
    else:
        # Modo interativo
        print("\nModo interativo iniciado. Comandos disponíveis:")
        print("  evolve N  - Executa N ciclos de evolução manual")
        print("  stop      - Para a evolução manual em andamento")
        print("  status    - Exibe status geral e métricas")
        print("  conscience activate   - Ativa o Módulo de Consciência Autônoma")
        print("  conscience deactivate - Desativa o Módulo de Consciência Autônoma")
        print("  conscience status   - Exibe status do Módulo de Consciência")
        print("  audit     - Exibe relatório de auditoria de segurança")
        print("  exit      - Encerra o sistema")
        
        while True:
            try:
                cmd_line = input("\n(AI-Genesis)> ").strip().lower()
                parts = cmd_line.split()
                if not parts:
                    continue
                
                command = parts[0]
                args = parts[1:]
                
                if command == "evolve":
                    cycles = 1
                    if args:
                        try:
                            cycles = int(args[0])
                            if cycles <= 0:
                                 print("Erro: Número de ciclos deve ser positivo.")
                                 continue
                        except ValueError:
                            print(f"Erro: Número de ciclos inválido: {args[0]}")
                            continue
                    # Roda em background para não bloquear o prompt? Não, por enquanto roda síncrono.
                    core.start_manual_evolution(cycles)
                
                elif command == "stop":
                     core.stop_manual_evolution()

                elif command == "status":
                    metrics = core.meta_cognition.evaluate_system(core.components)
                    print("\n--- Status Geral do Sistema ---")
                    print(f"Ciclos de evolução manuais executados: {core.evolution_cycles}")
                    print(f"Evolução manual em andamento: {core.running}")
                    print("Métricas dos Componentes:")
                    for name, value in metrics.items():
                        print(f"  - {name}: {value}")
                    if core.last_evolution_result:
                         print("Resultado do Último Ciclo Manual:")
                         print(f"  - ID: {core.last_evolution_result.get('cycle_id')}")
                         print(f"  - Duração: {core.last_evolution_result.get('duration_s'):.2f}s")
                         print(f"  - Modificação Aplicada: {core.last_evolution_result.get('modification_applied')}")
                         print(f"  - Erros: {len(core.last_evolution_result.get('errors',[]))}")

                elif command == "conscience":
                    if not args:
                         print("Uso: conscience [activate|deactivate|status]")
                         continue
                    sub_command = args[0]
                    if sub_command == "activate":
                        core.activate_consciousness()
                    elif sub_command == "deactivate":
                        core.deactivate_consciousness()
                    elif sub_command == "status":
                        status = core.get_consciousness_status()
                        print("\n--- Status do Módulo de Consciência ---")
                        for key, value in status.items():
                             # Formata um pouco melhor a saída
                             if isinstance(value, float): value_str = f"{value:.2f}"
                             else: value_str = str(value)
                             print(f"  {key.replace('_',' ').capitalize()}: {value_str}")
                    else:
                         print(f"Subcomando desconhecido para conscience: {sub_command}")

                elif command == "audit":
                     report = core.security.get_audit_report()
                     print("\n--- Relatório de Auditoria de Segurança ---")
                     for key, value in report.items():
                          if key == "last_modification" or key == "last_violation":
                               print(f"  {key.replace('_',' ').capitalize()}:")
                               if value:
                                    for k, v in value.items(): print(f"    - {k}: {v}")
                               else: print("    Nenhum")
                          else:
                               value_str = f"{value:.2f}" if isinstance(value, float) else str(value)
                               print(f"  {key.replace('_',' ').capitalize()}: {value_str}")

                elif command == "exit":
                    print("Desativando consciência (se ativa) e encerrando...")
                    core.deactivate_consciousness() # Garante desativação ao sair
                    core.stop_manual_evolution() # Garante parada da evolução manual
                    break
                
                else:
                    print(f"Comando desconhecido: {command}")
            
            except KeyboardInterrupt:
                print("\nInterrupção detectada. Desativando e encerrando...")
                core.deactivate_consciousness()
                core.stop_manual_evolution()
                break
            except Exception as e:
                print(f"\nErro inesperado no loop interativo: {e}")
                logger.error("Erro no loop interativo", exc_info=True)
    
    print("\nAI-Genesis Core encerrado.")

