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
import re # Importado para regex na extração de código LLM
import shutil # Importado para backup

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

class CodeFileUtils:
    @staticmethod
    def create_module_file(filepath: str, code_content: str, overwrite: bool = False) -> Tuple[bool, str]:
        """
        Creates a Python module file at the given filepath with the provided code content.

        Args:
            filepath: The full path (including filename) where the module should be created.
            code_content: A string containing the Python code for the module.
            overwrite: If True, overwrite the file if it exists. 
                       If False and the file exists, the operation will fail.

        Returns:
            A tuple (success: bool, message: str).
        """
        logger.debug(f"Attempting to create module file at: {filepath}")
        try:
            directory_path = os.path.dirname(filepath)
            if directory_path: # Only create if directory_path is not empty (i.e., not current dir)
                os.makedirs(directory_path, exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory_path}")

            if os.path.exists(filepath) and not overwrite:
                message = f"File {filepath} already exists and overwrite is False."
                logger.warning(message)
                return False, message

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code_content)
            
            message = f"Module {filepath} created/overwritten successfully."
            logger.info(message)
            return True, message
        except IOError as e:
            message = f"IOError writing to {filepath}: {e}"
            logger.error(message)
            return False, message
        except Exception as e:
            message = f"Unexpected error creating module file {filepath}: {e}"
            logger.error(message, exc_info=True) # Log traceback for unexpected errors
            return False, message

# --- Componentes Principais (MetaCognition, CodeTransformation, etc.) ---

class MetaCognitionCore:
    """Núcleo de Meta-Cognição (NMC) - Permite ao sistema raciocinar sobre si mesmo"""
    
    def __init__(self):
        self.performance_metrics = {}
        self.improvement_hypotheses = []
        self.system_state = {}
        self.evaluation_history = []
        self.core = None # Será vinculado pelo AIGenesisCore
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
        metric_prefix_to_component = {
            "meta": "meta_cognition",
            "code": "code_transformer",
            "pattern": "pattern_library",
            "interface": "interface",
            "security": "security",
            "consciousness": "consciousness"
        }

        # Obtém a lista de nomes de componentes *reais* e válidos
        valid_component_names = list(self.core.components.keys()) if self.core and hasattr(self.core, 'components') and self.core.components else []
        
        if not valid_component_names:
            logger.warning("Não foi possível determinar componentes válidos para geração de hipóteses.")
            if hasattr(self, 'evaluation_history') and self.evaluation_history:
                metrics_keys = self.evaluation_history[-1]['metrics'].keys()
                derived_prefixes = list(set([k.split('_')[0] for k in metrics_keys]))
                valid_component_names = [metric_prefix_to_component.get(prefix, None) for prefix in derived_prefixes]
                valid_component_names = [name for name in valid_component_names if name is not None]
            else:
                 return []

        logger.debug(f"Componentes válidos para hipóteses: {valid_component_names}")

        # 1. Hipóteses baseadas em histórico de métricas (Refatoração)
        if len(self.evaluation_history) >= 2:
            current = self.evaluation_history[-1]["metrics"]
            previous = self.evaluation_history[-2]["metrics"]
            
            for metric, value in current.items():
                metric_prefix = metric.split("_")[0]
                target_component = metric_prefix_to_component.get(metric_prefix)
                
                if not target_component or target_component not in valid_component_names: continue 

                if metric in previous and isinstance(value, (int, float)):
                    if "_complexity" in metric and value > previous[metric] * 1.15: 
                        hypotheses.append({
                            "target": target_component,
                            "type": "refactor_simplification",
                            "reason": f"Complexidade de {target_component} aumentou {value/previous[metric]:.2f}x",
                            "priority": 0.8
                        })
                    elif "_performance" in metric and value < previous[metric] * 0.85:
                        hypotheses.append({
                            "target": target_component,
                            "type": "optimize_performance",
                            "reason": f"Desempenho de {target_component} caiu para {value/previous[metric]:.2f}x do valor anterior",
                            "priority": 0.75
                        })

        # 2. Hipóteses de Expansão de Capacidades (para componentes existentes válidos)
        component_metrics_count = {}
        for metric in self.performance_metrics:
            metric_prefix = metric.split("_")[0]
            target_component = metric_prefix_to_component.get(metric_prefix)
            if target_component and target_component in valid_component_names:
                 component_metrics_count[target_component] = component_metrics_count.get(target_component, 0) + 1
        
        cycle_count = len(self.evaluation_history) if hasattr(self, 'evaluation_history') else 0
        if not valid_component_names: # Adiciona verificação caso valid_component_names esteja vazio
             logger.warning("Lista de componentes válidos está vazia, pulando hipóteses de expansão.")
        else:
            rotated_components = valid_component_names[cycle_count % len(valid_component_names):] + valid_component_names[:cycle_count % len(valid_component_names)]
            
            for i, component_name in enumerate(rotated_components):
                count = component_metrics_count.get(component_name, 0)
                priority_boost = 0.2 if i == 0 else 0
                
                hypotheses.append({
                    "target": component_name,
                    "type": "expand_functionality", 
                    "reason": f"Componente {component_name} pode receber novas capacidades (ciclo de diversificação)",
                    "priority": 0.6 + priority_boost
                })
                
                hypotheses.append({
                    "target": component_name,
                    "type": "optimize_performance",
                    "reason": f"Otimização proativa de {component_name} para melhorar desempenho geral",
                    "priority": 0.5 + priority_boost
                })

        # 3. Hipótese de Novo Módulo (se o sistema for simples)
        if len(valid_component_names) < 6: 
            hypotheses.append({
                "target": "system", 
                "type": "create_new_module", 
                "reason": "Sistema pode se beneficiar de novas capacidades modulares",
                "priority": 0.5 + (0.1 * (cycle_count % 3))
            })

        # 4. Hipótese de integração entre módulos (nova)
        if len(valid_component_names) >= 2:
            components_to_integrate = random.sample(valid_component_names, 2)
            hypotheses.append({
                "target": components_to_integrate[0],
                "type": "expand_functionality",
                "reason": f"Integração entre {components_to_integrate[0]} e {components_to_integrate[1]} para funcionalidade emergente",
                "priority": 0.65,
                "integration_target": components_to_integrate[1]
            })

        # Garante diversidade limitando hipóteses do mesmo tipo/alvo
        unique_hypotheses = []
        type_target_pairs = set()
        
        hypotheses.sort(key=lambda h: h.get("priority", 0), reverse=True)
        
        for h in hypotheses:
            pair = (h.get("type"), h.get("target"))
            if pair not in type_target_pairs:
                unique_hypotheses.append(h)
                type_target_pairs.add(pair)
                # Limita a 2 hipóteses por tipo para garantir diversidade
                # type_counts = [t[0] for t in type_target_pairs].count(h.get("type"))
                # if type_counts >= 2:
                #     continue # Comentado para permitir mais exploração inicialmente
        
        self.improvement_hypotheses = unique_hypotheses # Armazena as hipóteses únicas geradas
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
                    module_name = node.module if node.module else ""
                    analysis["imports"].append(f"{module_name}")
        except Exception as e:
            logger.error(f"Erro ao analisar código: {e}")
        
        return analysis

    def _extract_llm_code(self, llm_suggestion: str) -> Optional[str]:
        """Tenta extrair blocos de código Python de uma sugestão LLM."""
        logger.debug("Tentando extrair código da sugestão LLM.")
        # 1. Procura por blocos ```python ... ```
        code_pattern = re.compile(r'```python(.*?)```', re.DOTALL)
        code_blocks = code_pattern.findall(llm_suggestion)
        if code_blocks:
            extracted_code = code_blocks[0].strip()
            # CORRIGIDO: String f fechada corretamente
            logger.info(f"Código extraído do bloco ```python:\n{extracted_code[:200]}...")
            return extracted_code

        # 2. Se não encontrar, procura por blocos ``` ... ``` genéricos
        code_pattern_generic = re.compile(r'```(.*?)```', re.DOTALL)
        code_blocks_generic = code_pattern_generic.findall(llm_suggestion)
        if code_blocks_generic:
            # Tenta validar se o conteúdo parece Python
            potential_code = code_blocks_generic[0].strip()
            try:
                ast.parse(potential_code)
                # CORRIGIDO: String f fechada corretamente
                logger.info(f"Código extraído do bloco ``` genérico (validado com AST):\n{potential_code[:200]}...")
                return potential_code
            except SyntaxError:
                logger.debug("Bloco ``` genérico encontrado, mas não parece ser código Python válido.")

        # 3. Heurística: Procura por linhas indentadas que começam com 'def' ou 'class'
        lines = llm_suggestion.splitlines()
        potential_code_lines = []
        in_code_block = False
        for line in lines:
            stripped_line = line.strip()
            # Heurística mais simples: começa com def ou class OU tem indentação significativa
            if stripped_line.startswith(('def ', 'class ')) or (line.startswith('    ') and stripped_line):
                in_code_block = True
            
            if in_code_block:
                 if stripped_line: # Adiciona linhas não vazias
                     potential_code_lines.append(line)
                 elif not stripped_line and potential_code_lines: # Para se encontrar linha vazia após código
                     # Verifica se a próxima linha também é vazia ou menos indentada para confirmar fim do bloco
                     next_line_index = lines.index(line) + 1
                     if next_line_index >= len(lines) or not lines[next_line_index].strip() or not lines[next_line_index].startswith('    '):
                         in_code_block = False
                         break # Assume fim do bloco
                     else: # Linha vazia dentro do bloco, continua
                         potential_code_lines.append(line)
        
        if potential_code_lines:
            potential_code = "\n".join(potential_code_lines)
            # Remove indentação comum do bloco extraído
            try:
                first_line_indent = len(potential_code_lines[0]) - len(potential_code_lines[0].lstrip(' '))
                potential_code = "\n".join([line[first_line_indent:] for line in potential_code_lines])
            except IndexError:
                pass # Ignora se não houver linhas
                
            try:
                ast.parse(potential_code)
                # CORRIGIDO: String f fechada corretamente
                logger.info(f"Código extraído por heurística de indentação (validado com AST):\n{potential_code[:200]}...")
                return potential_code
            except SyntaxError:
                 logger.debug("Código encontrado por heurística de indentação, mas falhou na validação AST.")

        logger.warning("Não foi possível extrair código Python funcional da sugestão LLM.")
        return None

    def _get_class_end_index(self, source_code: str, target_class_name: str) -> int:
        """Encontra o índice final de uma classe no código fonte usando AST ou fallback."""
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == target_class_name:
                    # end_lineno é 1-based, precisamos do índice do caractere
                    class_end_line_num = node.end_lineno
                    lines = source_code.splitlines()
                    # Calcula o índice do início da última linha da classe
                    # +1 para incluir o newline
                    if class_end_line_num <= len(lines):
                        # Encontra o início da linha final
                        start_of_last_line = sum(len(l) + 1 for l in lines[:class_end_line_num-1])
                        # Encontra o fim da linha final (sem o newline)
                        end_of_last_line = start_of_last_line + len(lines[class_end_line_num-1])
                        return end_of_last_line
                    else: # Classe termina no fim do arquivo
                        return len(source_code)
            logger.warning(f"AST não encontrou a classe {target_class_name} para determinar o fim.")
        except Exception as e:
            logger.warning(f"Falha ao usar AST para encontrar fim da classe {target_class_name}: {e}")

        # Fallback: Busca por string (menos preciso)
        class_pattern = f"class {target_class_name}"
        start_index = source_code.find(class_pattern)
        if start_index != -1:
            # Procura a próxima definição de classe ou função no mesmo nível de indentação (aproximação)
            # Ou simplesmente o fim do arquivo
            # Regex para encontrar 'def' ou 'class' no início da linha (nível 0 de indentação)
            next_def_match = re.search(r"^def ", source_code[start_index:], re.MULTILINE)
            next_class_match = re.search(r"^class ", source_code[start_index:], re.MULTILINE)
            
            end_indices = []
            if next_def_match:
                end_indices.append(start_index + next_def_match.start())
            if next_class_match:
                 end_indices.append(start_index + next_class_match.start())

            if end_indices:
                return min(end_indices)
            else:
                return len(source_code) # Assume fim do arquivo
        
        logger.error(f"Não foi possível encontrar o fim da classe {target_class_name} por AST ou fallback.")
        return -1 # Indica falha

    def _indent_code(self, code_block: str, indent_level: int = 1) -> str:
        """Indenta um bloco de código Python."""
        indent = "    " * indent_level
        lines = code_block.strip().splitlines()
        if not lines: return ""
        # Remove indentação comum inicial, se houver
        first_line_indent = len(lines[0]) - len(lines[0].lstrip(' '))
        unindented_lines = [line[first_line_indent:] if len(line) >= first_line_indent else '' for line in lines]
        indented_lines = [indent + line for line in unindented_lines]
        return "\n".join(indented_lines)

    def generate_code_modification(self, source_code: str, hypothesis: Dict[str, Any], llm_suggestion: Optional[str] = None) -> Tuple[str, str]:
        """Gera uma modificação de código baseada em uma hipótese, integrando código funcional do LLM."""
        modification_type = hypothesis.get("type", "")
        target = hypothesis.get("target", "")
        reason = hypothesis.get("reason", "N/A")
        modified_code = source_code
        description = "Nenhuma modificação significativa gerada"
        extracted_llm_code = None
        imports_to_add = set() # Para coletar imports necessários

        # Mapeamento de nomes de módulos para nomes de classes
        module_to_class_map = {
            "meta_cognition": "MetaCognitionCore",
            "code_transformer": "CodeTransformationEngine",
            "pattern_library": "EvolutionaryPatternLibrary",
            "interface": "PerceptionActionInterface",
            "security": "SecurityLoggingMechanism",
            "consciousness": "ConsciousnessModule"
        }

        try:
            target_class_name = module_to_class_map.get(target)
            class_pattern = f"class {target_class_name}" if target_class_name else None
            logger.debug(f"Tentando modificar. Tipo: {modification_type}, Alvo: {target}, Classe Alvo: {target_class_name}, Razão: {reason}")

            # 1. Processa sugestão LLM, se houver
            if llm_suggestion:
                logger.info("Processando sugestão do LLM...")
                extracted_llm_code = self._extract_llm_code(llm_suggestion)
                if extracted_llm_code:
                    # Validação sintática preliminar do código extraído
                    try:
                        ast.parse(extracted_llm_code)
                        logger.info("Código LLM extraído é sintaticamente válido.")
                        # Tenta identificar imports no código LLM
                        tree = ast.parse(extracted_llm_code)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports_to_add.add(f"import {alias.name}")
                            elif isinstance(node, ast.ImportFrom):
                                module = node.module or ''
                                names = ", ".join(alias.name for alias in node.names)
                                # Lida com 'from . import ...' ou 'from .. import ...'
                                level = node.level
                                module_prefix = '.' * level
                                imports_to_add.add(f"from {module_prefix}{module} import {names}")
                        if imports_to_add:
                             logger.info(f"Imports identificados na sugestão LLM: {imports_to_add}")
                    except SyntaxError as e:
                        logger.warning(f"Código LLM extraído contém erro de sintaxe: {e}. Usando como comentário.")
                        extracted_llm_code = None # Descarta se inválido
                else:
                    logger.warning("Não foi possível extrair código funcional da sugestão LLM. Usando como comentário se aplicável.")

            # --- Tratamento das Hipóteses --- 

            if modification_type == "refactor_simplification":
                # TODO: Implementar substituição de método/função com código LLM
                if target_class_name and class_pattern in source_code:
                    insertion_point = source_code.find(class_pattern)
                    # Encontra o início da classe para inserir o TODO antes dela
                    class_start_line_index = source_code.rfind('\n', 0, insertion_point) + 1
                    todo_comment = f"# TODO: [Refatoração] {reason}. Analisar e simplificar métodos em {target_class_name}.\n"
                    # Se houver código LLM, adiciona como referência
                    if extracted_llm_code:
                        indented_llm_code = self._indent_code(extracted_llm_code, 1) # Indenta 1 nível para comentário
                        todo_comment += f"# Sugestão LLM para refatoração:\n# ```python\n{indented_llm_code}\n# ```\n"
                    modified_code = source_code[:class_start_line_index] + todo_comment + source_code[class_start_line_index:]
                    description = f"Adicionado lembrete TODO para refatorar/simplificar {target_class_name} (Razão: {reason})"
                    logger.info(description)
                else:
                    description = f"Alvo inválido ou não encontrado para refatoração: {target}"
                    logger.warning(description)
                    return source_code, description 
            
            elif modification_type == "expand_functionality":
                if target_class_name and class_pattern in source_code:
                    class_end_index = self._get_class_end_index(source_code, target_class_name)
                    
                    if class_end_index != -1:
                        func_name = f"enhance_{target}_capability_{random.randint(100, 999)}"
                        method_body = "" # Inicializa vazio
                        
                        if extracted_llm_code:
                            logger.info(f"Integrando código funcional LLM no novo método {func_name}.")
                            # Assume que o código LLM é o corpo da função/método
                            indented_body = self._indent_code(extracted_llm_code, 2) # Indenta para corpo do método
                            method_body = indented_body
                            description = f"Adicionado método {func_name} com código funcional LLM para expandir {target_class_name} (Razão: {reason})"
                        else:
                            logger.info(f"Gerando método placeholder {func_name} (sem código LLM funcional).")
                            # Fallback: Gera placeholder mais estruturado
                            placeholder_body = (
                                f"        logger.info(f\"Executando {func_name} com argumentos {{args}} e {{kwargs}}\")\n"
                                f"        # TODO: Implementar funcionalidade real aqui para: {reason}\n"
                            )
                            # Adiciona comentário da sugestão LLM se não foi possível extrair código
                            if llm_suggestion:
                                # Limita o tamanho da sugestão no comentário
                                suggestion_snippet = llm_suggestion[:500] + ('...' if len(llm_suggestion) > 500 else '')
                                processed_suggestion = suggestion_snippet.replace("\n", "\n        # ")
                                placeholder_body += f"        # Sugestão LLM original (snippet):\n        # {processed_suggestion}\n"
                            placeholder_body += "        return {'status': 'success', 'message': f'Método {func_name} placeholder executado'}"
                            method_body = placeholder_body
                            description = f"Adicionado método placeholder {func_name} para expandir {target_class_name} (Razão: {reason})"
                        
                        # Monta o novo método completo (usando aspas simples para docstring interna)
                        new_method = (
                            f"\n\n    def {func_name}(self, *args, **kwargs):\n"
                            f"        '''Nova capacidade para {target_class_name} baseada na hipótese: {reason}.'''\n"
                            f"{method_body}\n"
                        )
                        
                        # Insere o novo método antes do final da classe
                        modified_code = source_code[:class_end_index] + new_method + source_code[class_end_index:]
                        logger.info(description)
                    else:
                        description = f"Não foi possível encontrar ponto de inserção para novo método em {target_class_name}"
                        logger.warning(description)
                else:
                    description = f"Alvo inválido ou não encontrado para expansão: {target}"
                    logger.warning(description)
                    return source_code, description

            elif modification_type == "optimize_performance":
                # TODO: Implementar substituição de método/função com código LLM
                 if target_class_name and class_pattern in source_code:
                    insertion_point = source_code.find(class_pattern)
                    class_start_line_index = source_code.rfind('\n', 0, insertion_point) + 1
                    todo_comment = f"# TODO: [Otimização] {reason}. Analisar e otimizar desempenho em {target_class_name}.\n"
                    if extracted_llm_code:
                        indented_llm_code = self._indent_code(extracted_llm_code, 1)
                        todo_comment += f"# Sugestão LLM para otimização:\n# ```python\n{indented_llm_code}\n# ```\n"
                    modified_code = source_code[:class_start_line_index] + todo_comment + source_code[class_start_line_index:]
                    description = f"Adicionado lembrete TODO para otimizar {target_class_name} (Razão: {reason})"
                    logger.info(description)
                 else:
                    description = f"Alvo inválido ou não encontrado para otimização: {target}"
                    logger.warning(description)
                    return source_code, description
            
            elif modification_type == "create_new_module":
                # TODO: Implementar geração de nova classe/módulo com código LLM
                description = "Geração de novo módulo ainda não implementada."
                logger.info(description)

            else:
                description = f"Tipo de modificação desconhecido ou não suportado: {modification_type}"
                logger.warning(description)

            # 2. Adiciona imports necessários (se houver e código foi modificado)
            if imports_to_add and modified_code != source_code:
                logger.info(f"Tentando adicionar imports necessários: {imports_to_add}")
                # Encontra local para adicionar imports (ex: após docstring do módulo ou imports existentes)
                import_insertion_point = -1
                # Tenta encontrar o último import existente
                last_import_match = None
                for match in re.finditer(r"^(?:import|from) .+", modified_code, re.MULTILINE):
                    last_import_match = match
                
                if last_import_match:
                    import_insertion_point = last_import_match.end()
                else:
                    # Se não houver imports, tenta após a docstring do módulo
                    docstring_match = re.match(r'"""(.*?)"""', modified_code, re.DOTALL)
                    if docstring_match:
                        import_insertion_point = docstring_match.end()
                    else:
                        # Fallback: insere no início do arquivo
                        import_insertion_point = 0
                
                # Garante uma linha em branco antes dos novos imports se inserido após outros
                if import_insertion_point > 0 and modified_code[import_insertion_point-1] != '\n':
                     new_imports_prefix = "\n"
                else:
                     new_imports_prefix = ""
                # Garante uma linha em branco após os novos imports
                new_imports_suffix = "\n"

                existing_imports_lines = set(re.findall(r"^(?:import|from) .+", modified_code, re.MULTILINE))
                new_imports_str = ""
                for imp in imports_to_add:
                    # Verifica se o import exato já existe
                    if imp not in existing_imports_lines:
                        new_imports_str += imp + "\n"
                        existing_imports_lines.add(imp) # Evita adicionar o mesmo import duas vezes na mesma rodada
                
                if new_imports_str:
                    modified_code = modified_code[:import_insertion_point] + new_imports_prefix + new_imports_str.strip() + new_imports_suffix + modified_code[import_insertion_point:]
                    # CORRIGIDO: String f fechada corretamente e log simplificado
                    logger.info(f"Imports adicionados ao início do arquivo: {len(new_imports_str.strip().splitlines())} linha(s)")
                else:
                    logger.info("Nenhum import novo precisou ser adicionado (já existiam).")

        except Exception as e:
            logger.error(f"Erro fatal ao gerar modificação de código: {e}", exc_info=True)
            modified_code = source_code # Reverte para o código original em caso de erro
            description = f"Erro durante a geração da modificação: {e}"

        # Garante que sempre retorna uma tupla válida
        if modified_code == source_code and description == "Nenhuma modificação significativa gerada":
             description = "Nenhuma modificação significativa gerada ou erro ocorreu."
             
        # Registra a transformação apenas se o código realmente mudou
        if modified_code != source_code:
            self.transformation_history.append({
                "timestamp": time.time(),
                "hypothesis": hypothesis,
                "description": description
            })
            logger.info(f"Modificação gerada: {description}")
        else:
            logger.info(f"Nenhuma alteração de código aplicada para: {description}")
            
        return modified_code, description
    
    def test_modified_code(self, code: str) -> bool:
        """Testa se o código modificado é sintaticamente válido e passa nos testes unitários."""
        try:
            ast.parse(code)
            logger.debug("Código modificado é sintaticamente válido.")
        except SyntaxError as e:
            logger.error(f"Erro de sintaxe no código modificado: {e}")
            return False

        temp_filename = "temp_evolved_code.py"
        unit_tests_passed = True  # Assume True initially
        modified_module = None
        # Lista de módulos de teste (pode ser configurável no futuro)
        test_modules_to_run = ["tests.test_core_logic", "tests.test_consciousness_module", "tests.test_core_utils"]
        all_tests_summary = []
        original_sys_path = list(sys.path)
        tests_dir = os.path.abspath("tests")

        try:
            # Write the modified code to a temporary file
            success, msg = CodeFileUtils.create_module_file(temp_filename, code, overwrite=True)
            if not success:
                logger.error(f"Falha ao criar arquivo temporário para teste: {msg}")
                return False

            # Add tests directory to path if not already there
            if tests_dir not in sys.path and os.path.isdir(tests_dir):
                sys.path.insert(0, tests_dir)
                logger.debug(f"Adicionado diretório de testes ao sys.path: {tests_dir}")

            # Dynamically load the modified code from the temporary file
            spec = importlib.util.spec_from_file_location("temp_evolved_code", temp_filename)
            if spec is None or spec.loader is None:
                logger.error(f"Não foi possível criar spec/loader para o módulo modificado em {temp_filename}")
                return False
            
            modified_module = importlib.util.module_from_spec(spec)
            if modified_module is None:
                logger.error(f"Não foi possível criar o módulo a partir da spec para {temp_filename}")
                return False
            
            # Add to sys.modules BEFORE executing, so it can be imported by test modules
            sys.modules['temp_evolved_code'] = modified_module
            spec.loader.exec_module(modified_module)
            logger.debug(f"Módulo modificado '{temp_filename}' carregado como 'temp_evolved_code'.")

            # Run tests from all specified test modules
            total_tests_run = 0
            total_tests_failed = 0

            for test_module_name in test_modules_to_run:
                test_module = None
                try:
                    # Reload if already imported, import otherwise
                    if test_module_name in sys.modules:
                        test_module = importlib.reload(sys.modules[test_module_name])
                        logger.debug(f"Reloaded existing test module: {test_module_name}")
                    else:
                        test_module = importlib.import_module(test_module_name)
                        logger.debug(f"Imported test module: {test_module_name}")
                except ImportError as e:
                    logger.warning(f"Não foi possível importar/recarregar o módulo de teste {test_module_name}: {e}. Testes deste módulo serão pulados.")
                    all_tests_summary.append(f"{test_module_name}: SKIPPED (Import Error)")
                    continue # Skip to next test module
                except Exception as e:
                    logger.error(f"Erro inesperado ao carregar/recarregar {test_module_name}: {e}", exc_info=True)
                    all_tests_summary.append(f"{test_module_name}: ERROR (Loading Error)")
                    unit_tests_passed = False # Consider loading error as failure
                    continue

                test_functions_found_in_module = 0
                # Usa unittest para descobrir e rodar testes (mais robusto)
                import unittest
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromModule(test_module)
                runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'), verbosity=0) # Suprime output padrão
                result = runner.run(suite)

                test_functions_found_in_module = result.testsRun
                total_tests_run += result.testsRun
                failures = len(result.failures)
                errors = len(result.errors)
                total_tests_failed += failures + errors

                if failures > 0 or errors > 0:
                    unit_tests_passed = False
                    logger.warning(f"Testes em {test_module_name} FALHARAM: {failures} falhas, {errors} erros.")
                    # Log detalhes das falhas/erros
                    for test, traceback_str in result.failures + result.errors:
                        logger.debug(f"Falha/Erro em {test}:\n{traceback_str}")
                        all_tests_summary.append(f"{test_module_name}.{test}: FAIL/ERROR")
                elif result.testsRun > 0:
                     logger.info(f"Testes em {test_module_name} PASSARAM ({result.testsRun} testes).")
                     # Adiciona PASS para cada teste rodado (simplificado)
                     for i in range(result.testsRun):
                          all_tests_summary.append(f"{test_module_name}.test_{i+1}: PASS")
                
                if test_functions_found_in_module == 0:
                    logger.info(f"Nenhum teste encontrado ou executado em {test_module_name}.")
                    all_tests_summary.append(f"{test_module_name}: No tests found/run")

            logger.info(f"Resumo dos testes: {total_tests_run} testes executados, {total_tests_failed} falhas/erros.")
            # logger.debug("\n".join(all_tests_summary)) # Log detalhado pode ser muito verboso

        except Exception as e:
            logger.error(f"Erro fatal durante a execução dos testes unitários: {e}", exc_info=True)
            unit_tests_passed = False # Any error during test setup/execution is a failure
        finally:
            # Cleanup: remove module from sys.modules and delete temporary file
            if 'temp_evolved_code' in sys.modules:
                del sys.modules['temp_evolved_code']
                logger.debug("Módulo 'temp_evolved_code' removido de sys.modules.")
            
            if os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                    logger.debug(f"Arquivo temporário '{temp_filename}' removido.")
                except Exception as e:
                    logger.error(f"Erro ao remover arquivo temporário '{temp_filename}': {e}")
            
            # Restaura sys.path original
            sys.path = original_sys_path
            logger.debug("sys.path restaurado para o original.")
        
        if unit_tests_passed:
            logger.info("Código modificado é sintaticamente válido e passou em todos os testes unitários executados.")
            return True
        else:
            logger.warning("Código modificado é sintaticamente válido, mas falhou em um ou mais testes unitários ou ocorreu erro na execução.")
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
            usage = self.pattern_usage.get(pattern_id, 0) # Usa get com default
            weight = 1.0 / (usage + 1) # Evita divisão por zero se usage for -1?
            
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
    
    def log_modification(self, component: str, description: str, code_before: str, code_after: str, cycle_id: int, tests_passed: bool) -> str:
        """Registra uma modificação no sistema"""
        mod_id = hashlib.md5(f"{component}:{time.time()}:{random.random()}".encode()).hexdigest()
        
        modification = {
            "id": mod_id,
            "timestamp": time.time(),
            "cycle_id": cycle_id, # Adiciona o ciclo da modificação
            "component": component,
            "description": description,
            "code_diff_size": len(code_after) - len(code_before),
            "hash_before": hashlib.md5(code_before.encode()).hexdigest(),
            "hash_after": hashlib.md5(code_after.encode()).hexdigest(),
            "tests_passed": tests_passed,
        }
        
        self.modification_log.append(modification)
        
        # Salva o diff completo em um arquivo separado para auditoria
        try:
            os.makedirs("mods", exist_ok=True)
            diff_filename = f"mods/mod_{cycle_id}_{mod_id[:8]}.diff"
            # Usa difflib para gerar diff real
            import difflib
            diff = difflib.unified_diff(
                code_before.splitlines(keepends=True),
                code_after.splitlines(keepends=True),
                fromfile=f"{component}_before_cycle_{cycle_id}",
                tofile=f"{component}_after_cycle_{cycle_id}",
            )
            with open(diff_filename, "w", encoding='utf-8') as f:
                f.write(f"# Modification ID: {mod_id}\n")
                f.write(f"# Cycle ID: {cycle_id}\n")
                f.write(f"# Timestamp: {modification['timestamp']}\n")
                f.write(f"# Description: {description}\n")
                f.write(f"# Tests Passed: {tests_passed}\n")
                f.write("\n")
                f.writelines(diff)
        except Exception as e:
            logger.error(f"Erro ao salvar diff da modificação {mod_id}: {e}")

        logger.info(f"Modificação registrada: {description} (ID: {mod_id}, Ciclo: {cycle_id}, Testes: {'PASS' if tests_passed else 'FAIL'})")
        return mod_id

    def check_security(self, code_snippet: str) -> List[str]:
        """Verifica um trecho de código contra padrões de segurança básicos (exemplo)."""
        violations = []
        # Padrões perigosos simplificados (apenas para demonstração)
        dangerous_patterns = [
            r"os\.system\(", r"subprocess\.call\(", r"subprocess\.run\(", r"eval\(", r"exec\(", 
            r"open\(.*,\s*[\"']w[b+]?[\"']\)", # Escrita de arquivos (simplista)
            r"socket\.socket\(", # Criação de sockets
            r"requests\.post\(", r"requests\.put\(", r"urllib\.request\.urlopen\(" # Requisições de escrita
        ]
        
        # Verifica apenas o snippet fornecido
        for pattern in dangerous_patterns:
            if re.search(pattern, code_snippet):
                violations.append(f"Padrão potencialmente perigoso detectado no snippet: {pattern}")
        
        # Verifica imports perigosos no snippet
        try:
            tree = ast.parse(code_snippet)
            for node in ast.walk(tree):
                module_name = None
                if isinstance(node, ast.Import):
                    if node.names:
                         module_name = node.names[0].name
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module
                
                if module_name in ["os", "subprocess", "socket", "shutil", "requests", "urllib", "pickle"]:
                    violations.append(f"Import potencialmente perigoso detectado no snippet: {module_name}")
        except SyntaxError:
            violations.append("Erro de sintaxe no snippet impede análise de imports.")
            
        if violations:
            logger.warning(f"Violações de segurança detectadas no snippet: {list(set(violations))}") # Remove duplicatas
        else:
            logger.debug("Nenhuma violação de segurança óbvia detectada no snippet.")
            
        return list(set(violations))

    def get_metrics(self) -> Dict[str, float]:
        """Retorna métricas de segurança"""
        return {
            "total_modifications_logged": len(self.modification_log),
            "total_security_violations": len(self.security_violations)
        }

# --- Núcleo Principal --- 

class AIGenesisCore:
    """Núcleo principal do sistema AI-Genesis"""
    
    def __init__(self, initial_code_path="core.py"):
        self.core_code_path = os.path.abspath(initial_code_path)
        self.current_code = self._load_initial_code()
        self.cycle_count = 0
        self.last_modification_info = None
        self.stop_requested = False
        self.autonomous_mode = False
        self.autonomous_thread = None
        self.last_error = None
        
        # Instanciação dos componentes
        self.meta_cognition = MetaCognitionCore()
        self.code_transformer = CodeTransformationEngine()
        self.pattern_library = EvolutionaryPatternLibrary()
        self.interface = PerceptionActionInterface()
        self.security = SecurityLoggingMechanism()
        self.consciousness = None
        if ConsciousnessModule:
            try:
                self.consciousness = ConsciousnessModule(self) # Passa a instância do Core
                logger.info("Módulo de Consciência Autônoma inicializado.")
            except Exception as e:
                logger.error(f"Falha ao inicializar ConsciousnessModule: {e}", exc_info=True)
                self.consciousness = None
        else:
            logger.warning("ConsciousnessModule não disponível. Operando sem consciência autônoma.")

        # Mapeamento de nomes para instâncias (incluindo consciência se existir)
        self.components = {
            "meta_cognition": self.meta_cognition,
            "code_transformer": self.code_transformer,
            "pattern_library": self.pattern_library,
            "interface": self.interface,
            "security": self.security,
        }
        if self.consciousness:
            self.components["consciousness"] = self.consciousness
            
        # Vincula a instância do Core aos componentes que precisam dela
        self.meta_cognition.core = self 

        logger.info("AI-Genesis Core inicializado.")

    def _load_initial_code(self) -> str:
        """Carrega o código-fonte inicial do próprio Core"""
        try:
            with open(self.core_code_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Erro crítico: Arquivo do Core não encontrado em {self.core_code_path}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Erro ao carregar código inicial: {e}")
            sys.exit(1)

    def _save_code(self, code: str) -> bool:
        """Salva o código-fonte atualizado"""
        try:
            # Cria backup antes de sobrescrever
            backup_path = f"{self.core_code_path}.bak_{int(time.time())}"
            if os.path.exists(self.core_code_path):
                 shutil.copy(self.core_code_path, backup_path)
                 logger.info(f"Backup do código criado em: {backup_path}")
            else:
                 logger.warning(f"Arquivo original {self.core_code_path} não encontrado para backup.")
            
            with open(self.core_code_path, "w", encoding="utf-8") as f:
                f.write(code)
            logger.info(f"Código principal atualizado em: {self.core_code_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar código: {e}")
            return False

    def _get_system_state(self) -> Dict[str, Any]:
        """Coleta o estado atual do sistema para a consciência."""
        state = {
            "cycle_count": self.cycle_count,
            "last_modification_info": self.last_modification_info,
            "pending_hypotheses": self.meta_cognition.improvement_hypotheses,
            "performance_metrics": self.meta_cognition.performance_metrics,
            "security_violations_count": len(self.security.security_violations),
            "last_error": self.last_error,
            "autonomous_mode": self.autonomous_mode,
            "core_code_hash": hashlib.md5(self.current_code.encode()).hexdigest(),
            # Adicionar outras métricas relevantes (uso de recursos, etc.)
        }
        return state

    def evolve(self, num_cycles: int = 1):
        """Executa um ou mais ciclos de evolução"""
        logger.info(f"Iniciando {num_cycles} ciclo(s) de evolução...")
        
        cycles_completed = 0
        for i in range(num_cycles):
            if self.stop_requested:
                logger.info("Parada solicitada. Interrompendo ciclos de evolução.")
                self.stop_requested = False
                break
                
            self.cycle_count += 1
            cycle_id = self.cycle_count
            logger.info(f"--- Ciclo Evolutivo {cycle_id} --- ")
            self.last_error = None # Reseta último erro no início do ciclo
            cycle_log = {
                "cycle_id": cycle_id,
                "timestamp_start": time.time(),
                "actions": [],
                "modification_applied": False,
                "error": None
            }

            try:
                # 1. Avaliação e Geração de Hipóteses (NMC)
                logger.debug("Fase 1: Avaliação e Geração de Hipóteses")
                current_metrics = self.meta_cognition.evaluate_system(self.components)
                hypotheses = self.meta_cognition.generate_improvement_hypotheses()
                cycle_log["metrics"] = current_metrics
                cycle_log["hypotheses_generated"] = hypotheses
                cycle_log["actions"].append({"component": "meta_cognition", "action": "evaluate_system, generate_hypotheses"})

                if not hypotheses:
                    logger.warning("Nenhuma hipótese de melhoria gerada neste ciclo.")
                    # continue # Pula para o próximo ciclo se não houver hipóteses

                # 2. Seleção da Melhor Hipótese (Pode ser movido para Consciência)
                best_hypothesis = None
                if hypotheses:
                    # Ordena por prioridade (maior primeiro)
                    hypotheses.sort(key=lambda h: h.get("priority", 0), reverse=True)
                    best_hypothesis = hypotheses[0]
                    logger.info(f"Hipótese selecionada: {best_hypothesis}")
                    cycle_log["hypothesis_selected"] = best_hypothesis
                    cycle_log["actions"].append({"component": "meta_cognition", "action": "select_hypothesis"})
                else:
                    logger.info("Nenhuma hipótese para selecionar.")

                # --- Integração com Consciência (se ativa) ---
                llm_suggestion = None
                if self.consciousness and self.autonomous_mode:
                    logger.debug("Consultando Módulo de Consciência...")
                    system_state = self._get_system_state()
                    # A consciência pode decidir buscar inspiração externa
                    action_decision = self.consciousness.decide_action(system_state)
                    cycle_log["consciousness_decision"] = action_decision
                    
                    if action_decision and action_decision.get("type") == "seek_external_inspiration":
                        logger.info("Consciência decidiu buscar inspiração externa.")
                        # Passa a melhor hipótese como contexto para o LLM
                        context_for_llm = {
                            "current_goal": "Improve system based on hypothesis",
                            "hypothesis": best_hypothesis,
                            "reason": best_hypothesis.get("reason") if best_hypothesis else "General improvement",
                            "target_component": best_hypothesis.get("target") if best_hypothesis else "system"
                        }
                        llm_suggestion = self.consciousness.seek_external_inspiration(context_for_llm)
                        cycle_log["llm_suggestion_raw"] = llm_suggestion
                        if llm_suggestion:
                            logger.info("Sugestão recebida do LLM.")
                        else:
                            logger.warning("Não foi possível obter sugestão do LLM.")
                    cycle_log["actions"].append({"component": "consciousness", "action": "decide_action, seek_inspiration"})
                # --- Fim Integração Consciência ---
                
                # 3. Geração da Modificação (MTC)
                logger.debug("Fase 3: Geração da Modificação")
                modified_code = self.current_code
                description = "Nenhuma hipótese selecionada para gerar modificação."
                if best_hypothesis:
                    modified_code, description = self.code_transformer.generate_code_modification(
                        self.current_code, best_hypothesis, llm_suggestion
                    )
                    cycle_log["modification_generated"] = {"description": description}
                    cycle_log["actions"].append({"component": "code_transformer", "action": "generate_code_modification"})
                else:
                    logger.info(description)
                    cycle_log["modification_generated"] = {"description": description}

                # 4. Teste da Modificação (MTC)
                tests_passed = False
                if modified_code != self.current_code:
                    logger.debug("Fase 4: Teste da Modificação")
                    # Verifica segurança do *snippet* modificado (ainda experimental)
                    # Idealmente, faríamos um diff e analisaríamos apenas as linhas alteradas
                    # import difflib
                    # code_diff_lines = list(difflib.unified_diff(self.current_code.splitlines(), modified_code.splitlines()))
                    # # Extrai apenas as linhas adicionadas/modificadas para análise de segurança
                    # changed_code_snippet = "\n".join([line[1:] for line in code_diff_lines if line.startswith('+') and not line.startswith('+++')])
                    # security_violations = self.security.check_security(changed_code_snippet)
                    # if security_violations:
                    #    logger.warning(f"Violações de segurança detectadas na modificação proposta: {security_violations}. Modificação rejeitada.")
                    #    cycle_log["security_check"] = {"status": "failed", "violations": security_violations}
                    #    modified_code = self.current_code # Rejeita a modificação
                    # else:
                    #    cycle_log["security_check"] = {"status": "passed"}
                    #    tests_passed = self.code_transformer.test_modified_code(modified_code)
                    
                    # Executa testes unitários completos no código modificado
                    tests_passed = self.code_transformer.test_modified_code(modified_code)
                    cycle_log["tests_passed"] = tests_passed
                    cycle_log["actions"].append({"component": "code_transformer", "action": "test_modified_code"})
                    
                    if not tests_passed:
                        logger.warning("Modificação reprovada nos testes. Revertendo.")
                        # Não reverte aqui, apenas registra a falha. A não aplicação acontece abaixo.
                    else:
                        logger.info("Modificação aprovada nos testes.")
                else:
                    logger.info("Nenhuma modificação de código gerada para testar.")
                    # Se não houve modificação, considera que os "testes" passaram (estado inalterado)
                    tests_passed = True 
                    cycle_log["tests_passed"] = tests_passed 

                # 5. Aplicação da Modificação e Registro (MSR)
                if modified_code != self.current_code and tests_passed:
                    logger.debug("Fase 5: Aplicação da Modificação e Registro")
                    # Salva o novo código
                    if self._save_code(modified_code):
                        mod_id = self.security.log_modification(
                            best_hypothesis.get("target", "system"), 
                            description, 
                            self.current_code, 
                            modified_code, 
                            cycle_id,
                            tests_passed
                        )
                        code_before_apply = self.current_code # Guarda para caso precise recarregar
                        self.current_code = modified_code
                        self.last_modification_info = {"cycle_id": cycle_id, "mod_id": mod_id, "description": description}
                        cycle_log["modification_applied"] = True
                        cycle_log["modification_details"] = self.last_modification_info
                        cycle_log["actions"].append({"component": "security", "action": "log_modification"})
                        cycle_log["actions"].append({"component": "core", "action": "save_code"})
                        logger.info(f"Modificação aplicada com sucesso (ID: {mod_id}). O sistema tentará recarregar dinamicamente.")
                        # Tenta recarregar módulos afetados (EXPERIMENTAL)
                        # self._reload_affected_modules(best_hypothesis.get("target"))
                    else:
                        logger.error("Falha ao salvar o código modificado. Modificação não aplicada.")
                        cycle_log["error"] = "Falha ao salvar código"
                        # Não reverte self.current_code aqui, pois não foi atualizado
                elif modified_code != self.current_code and not tests_passed:
                     # Registra a tentativa falha
                     self.security.log_modification(
                            best_hypothesis.get("target", "system") if best_hypothesis else "unknown", 
                            f"[FALHA TESTE] {description}", 
                            self.current_code, 
                            modified_code, # Loga o código que falhou
                            cycle_id,
                            tests_passed
                        )
                     logger.info("Modificação não aplicada devido à falha nos testes.")
                else:
                    logger.info("Nenhuma modificação aplicada neste ciclo.")

                # 6. Avaliação de Impacto (Pós-modificação, se houve)
                if cycle_log["modification_applied"]:
                    logger.debug("Fase 6: Avaliação de Impacto (Pós-Modificação)")
                    # Reavaliar métricas após modificação pode ser útil
                    # post_metrics = self.meta_cognition.evaluate_system(self.components) 
                    # cycle_log["post_modification_metrics"] = post_metrics
                    # Poderia usar um módulo dedicado de avaliação de impacto aqui
                    # impact_assessment = self.impact_evaluator.assess(self.current_code, pre_metrics, post_metrics)
                    # cycle_log["impact_assessment"] = impact_assessment
                    pass # Placeholder para avaliação de impacto futura
                    cycle_log["actions"].append({"component": "meta_cognition", "action": "assess_impact (placeholder)"})

                cycles_completed += 1

            except Exception as e:
                logger.error(f"Erro inesperado durante o ciclo evolutivo {cycle_id}: {e}", exc_info=True)
                cycle_log["error"] = str(e)
                self.last_error = traceback.format_exc() # Armazena traceback do último erro
                # Tenta continuar para o próximo ciclo se possível
            finally:
                cycle_log["timestamp_end"] = time.time()
                cycle_log["duration_seconds"] = cycle_log["timestamp_end"] - cycle_log["timestamp_start"]
                self._save_cycle_log(cycle_log)
                logger.info(f"--- Fim do Ciclo Evolutivo {cycle_id} (Duração: {cycle_log['duration_seconds']:.2f}s) ---")

        logger.info(f"Evolução concluída após {cycles_completed} ciclo(s) executado(s). ({num_cycles} solicitado(s))")

    def _save_cycle_log(self, cycle_log: Dict[str, Any]):
        """Salva o log do ciclo em um arquivo JSON."""
        log_filename = f"cycle_{cycle_log['cycle_id']}.json"
        try:
            with open(log_filename, "w", encoding="utf-8") as f:
                json.dump(cycle_log, f, indent=4, default=str) # Usa default=str para lidar com tipos não serializáveis
            logger.debug(f"Log do ciclo salvo em: {log_filename}")
        except Exception as e:
            logger.error(f"Erro ao salvar log do ciclo {cycle_log['cycle_id']}: {e}")

    def _autonomous_loop(self):
        """Loop principal para operação autônoma."""
        logger.info("Iniciando loop autônomo...")
        while self.autonomous_mode and not self.stop_requested:
            try:
                if self.consciousness:
                    # Deixa a consciência decidir o próximo passo
                    system_state = self._get_system_state()
                    action = self.consciousness.decide_action(system_state)
                    logger.info(f"[Autônomo] Ação decidida pela consciência: {action}")
                    
                    # Executa a ação decidida (simplificado)
                    if action and action.get("type") == "evolution_cycle":
                        self.evolve(1)
                    elif action and action.get("type") == "seek_external_inspiration":
                         # A busca já pode ter ocorrido na fase de decisão
                         logger.info("Ação 'seek_external_inspiration' será tratada dentro do ciclo 'evolve'.")
                         self.evolve(1) # O ciclo evolve agora lida com a sugestão
                    elif action and action.get("type") == "apply_hypothesis":
                         logger.info("Ação 'apply_hypothesis' será tratada dentro do ciclo 'evolve'.")
                         # Força a evolução com a hipótese pendente (se houver)
                         self.evolve(1)
                    else:
                        # Ação padrão ou não reconhecida: executa um ciclo normal
                        logger.info("Ação não especificada ou padrão: executando ciclo evolutivo normal.")
                        self.evolve(1)
                else:
                    # Sem consciência, apenas executa ciclos evolutivos
                    self.evolve(1)
                
                # Pausa entre ciclos autônomos para evitar uso excessivo de CPU
                time.sleep(5) # Pausa de 5 segundos (ajustável)
                
            except Exception as e:
                logger.error(f"Erro no loop autônomo: {e}", exc_info=True)
                self.last_error = traceback.format_exc()
                time.sleep(15) # Pausa maior em caso de erro

        logger.info("Loop autônomo finalizado.")
        self.autonomous_thread = None # Limpa a referência da thread

    def start_autonomous_mode(self):
        """Inicia a operação autônoma em uma thread separada."""
        if not self.autonomous_mode:
            if not self.consciousness:
                logger.error("Não é possível iniciar modo autônomo: Módulo de Consciência não está ativo.")
                self.interface.send_output("Erro: Módulo de Consciência não ativo. Modo autônomo indisponível.")
                return
                
            self.autonomous_mode = True
            self.stop_requested = False
            self.autonomous_thread = threading.Thread(target=self._autonomous_loop, daemon=True)
            self.autonomous_thread.start()
            logger.info("Modo autônomo iniciado.")
            self.interface.send_output("Modo autônomo ativado. O sistema evoluirá por conta própria.")
        else:
            logger.warning("Modo autônomo já está ativo.")
            self.interface.send_output("Modo autônomo já está ativo.")

    def stop_autonomous_mode(self):
        """Solicita a parada do modo autônomo."""
        if self.autonomous_mode:
            self.stop_requested = True
            self.autonomous_mode = False # Define imediatamente para evitar novos ciclos
            logger.info("Solicitação de parada do modo autônomo enviada.")
            self.interface.send_output("Solicitação de parada do modo autônomo enviada. Aguardando finalização do ciclo atual...")
            # O loop _autonomous_loop verificará self.stop_requested e sairá
            # Espera um pouco para a thread terminar
            if self.autonomous_thread and self.autonomous_thread.is_alive():
                 self.autonomous_thread.join(timeout=10) # Espera até 10s
                 if self.autonomous_thread.is_alive():
                      logger.warning("Thread autônoma não finalizou no tempo esperado.")
                 else:
                      logger.info("Modo autônomo finalizado com sucesso.")
                      self.interface.send_output("Modo autônomo finalizado.")
            else:
                 logger.info("Modo autônomo já havia sido finalizado ou não estava em execução.")
                 # self.interface.send_output("Modo autônomo finalizado.") # Evita duplicar msg
        else:
            logger.warning("Modo autônomo não está ativo.")
            self.interface.send_output("Modo autônomo não está ativo.")

    def run_interactive_mode(self):
        """Inicia o modo interativo para controle humano."""
        logger.info("Iniciando modo interativo...")
        print("\n--- AI-Genesis Core - Modo Interativo ---")
        print("Comandos disponíveis: evolve [N], status, auto_on, auto_off, exit")
        
        while True:
            try:
                command = input("> ").strip().lower()
                
                if command.startswith("evolve"):
                    parts = command.split()
                    num_cycles = 1
                    if len(parts) > 1 and parts[1].isdigit():
                        num_cycles = int(parts[1])
                    self.evolve(num_cycles)
                elif command == "status":
                    state = self._get_system_state()
                    print("--- Status do Sistema ---")
                    print(f"Ciclos Completos: {state['cycle_count']}")
                    print(f"Modo Autônomo: {'Ativo' if state['autonomous_mode'] else 'Inativo'}")
                    print(f"Última Modificação: {state['last_modification_info']}")
                    print(f"Hipóteses Pendentes: {len(state['pending_hypotheses'])}")
                    print(f"Violações de Segurança: {state['security_violations_count']}")
                    print(f"Último Erro: {'Sim' if state['last_error'] else 'Não'}")
                    # print(f"Métricas Atuais: {state['performance_metrics']}")
                elif command == "auto_on":
                    self.start_autonomous_mode()
                elif command == "auto_off":
                    self.stop_autonomous_mode()
                elif command == "exit":
                    logger.info("Saindo do modo interativo.")
                    if self.autonomous_mode:
                        self.stop_autonomous_mode()
                    break
                else:
                    print("Comando inválido.")
            except KeyboardInterrupt:
                logger.info("Interrupção de teclado recebida. Saindo...")
                if self.autonomous_mode:
                    self.stop_autonomous_mode()
                break
            except EOFError: # Lida com fim de entrada (ex: pipe)
                 logger.info("EOF recebido. Saindo...")
                 if self.autonomous_mode:
                     self.stop_autonomous_mode()
                 break
            except Exception as e:
                logger.error(f"Erro no loop interativo: {e}", exc_info=True)
                print(f"Ocorreu um erro: {e}")

# --- Ponto de Entrada --- 

if __name__ == "__main__":
    core = AIGenesisCore()
    # Verifica se algum argumento foi passado para rodar em modo não interativo
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command.startswith("evolve"):
             num_cycles = 1
             if len(sys.argv) > 2 and sys.argv[2].isdigit():
                 num_cycles = int(sys.argv[2])
             core.evolve(num_cycles)
        elif command == "auto_on":
             core.start_autonomous_mode()
             # Mantém o script rodando enquanto autônomo
             if core.autonomous_thread:
                 core.autonomous_thread.join()
        else:
             print(f"Comando não reconhecido: {command}")
             print("Use 'evolve [N]' ou 'auto_on'")
    else:
        core.run_interactive_mode()

