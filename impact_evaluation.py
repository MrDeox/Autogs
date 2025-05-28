#!/usr/bin/env python3
"""
Módulo de Avaliação de Impacto e Feedback para o AI-Genesis Core

Este módulo implementa mecanismos para avaliar o impacto das modificações aplicadas
durante os ciclos evolutivos e fornecer feedback para orientar futuras transformações.
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import ast
import re

# Configuração de logging
logger = logging.getLogger("AI-Genesis.ImpactEvaluation")

class ImpactEvaluationEngine:
    """Motor de Avaliação de Impacto e Feedback para o AI-Genesis Core"""
    
    def __init__(self, history_dir: str = "mods"):
        """
        Inicializa o motor de avaliação de impacto.
        
        Args:
            history_dir: Diretório onde os registros de ciclos são armazenados
        """
        self.history_dir = history_dir
        self.cycle_history = []
        self.impact_metrics = {}
        self.feedback_history = []
        self._load_cycle_history()
        logger.info("Motor de Avaliação de Impacto inicializado")
    
    def _load_cycle_history(self) -> None:
        """Carrega o histórico de ciclos evolutivos dos arquivos JSON"""
        if not os.path.exists(self.history_dir):
            logger.warning(f"Diretório de histórico {self.history_dir} não encontrado")
            return
        
        cycle_files = sorted([f for f in os.listdir(self.history_dir) if f.startswith("cycle_") and f.endswith(".json")])
        
        for file in cycle_files:
            try:
                with open(os.path.join(self.history_dir, file), 'r') as f:
                    cycle_data = json.load(f)
                    self.cycle_history.append(cycle_data)
            except Exception as e:
                logger.error(f"Erro ao carregar arquivo de ciclo {file}: {e}")
    
    def evaluate_impact(self, cycle_id: int) -> Dict[str, Any]:
        """
        Avalia o impacto das modificações aplicadas em um ciclo específico.
        
        Args:
            cycle_id: ID do ciclo a ser avaliado
            
        Returns:
            Dicionário com métricas de impacto
        """
        # Encontra os dados do ciclo
        cycle_data = None
        for cycle in self.cycle_history:
            if cycle.get("cycle_id") == cycle_id:
                cycle_data = cycle
                break
        
        if not cycle_data:
            logger.warning(f"Ciclo {cycle_id} não encontrado no histórico")
            return {"status": "error", "message": f"Ciclo {cycle_id} não encontrado"}
        
        # Métricas básicas
        metrics = {
            "cycle_id": cycle_id,
            "timestamp": time.time(),
            "modifications_count": len(cycle_data.get("modifications", [])),
            "targets": [mod.get("target") for mod in cycle_data.get("modifications", [])],
            "status": "success"
        }
        
        # Análise de complexidade
        if cycle_id > 1:
            # Compara métricas com o ciclo anterior
            prev_metrics = None
            for cycle in self.cycle_history:
                if cycle.get("cycle_id") == cycle_id - 1:
                    prev_metrics = cycle.get("metrics", {})
                    break
            
            if prev_metrics:
                # Calcula mudanças em métricas chave
                current_metrics = cycle_data.get("metrics", {})
                complexity_changes = {}
                performance_changes = {}
                
                for key, value in current_metrics.items():
                    if key in prev_metrics and isinstance(value, (int, float)) and isinstance(prev_metrics[key], (int, float)):
                        if "_complexity" in key:
                            change = value / prev_metrics[key] if prev_metrics[key] != 0 else float('inf')
                            complexity_changes[key] = change
                        elif "_performance" in key:
                            change = value / prev_metrics[key] if prev_metrics[key] != 0 else float('inf')
                            performance_changes[key] = change
                
                metrics["complexity_changes"] = complexity_changes
                metrics["performance_changes"] = performance_changes
                
                # Avaliação geral de impacto
                avg_complexity_change = sum(complexity_changes.values()) / len(complexity_changes) if complexity_changes else 1.0
                avg_performance_change = sum(performance_changes.values()) / len(performance_changes) if performance_changes else 1.0
                
                metrics["avg_complexity_change"] = avg_complexity_change
                metrics["avg_performance_change"] = avg_performance_change
                
                # Classificação de impacto
                if avg_complexity_change > 1.1 and avg_performance_change < 0.9:
                    metrics["impact_classification"] = "negative"
                    metrics["impact_description"] = "Aumento de complexidade com redução de desempenho"
                elif avg_complexity_change > 1.1 and avg_performance_change >= 0.9:
                    metrics["impact_classification"] = "mixed"
                    metrics["impact_description"] = "Aumento de complexidade com desempenho estável ou melhorado"
                elif avg_complexity_change <= 1.1 and avg_performance_change < 0.9:
                    metrics["impact_classification"] = "concerning"
                    metrics["impact_description"] = "Complexidade estável mas desempenho reduzido"
                elif avg_complexity_change <= 1.1 and avg_performance_change >= 1.1:
                    metrics["impact_classification"] = "positive"
                    metrics["impact_description"] = "Complexidade estável com desempenho melhorado"
                else:
                    metrics["impact_classification"] = "neutral"
                    metrics["impact_description"] = "Mudanças sem impacto significativo"
        
        # Análise de código (se disponível)
        if os.path.exists(f"core_evolved_c{cycle_id}.py") and os.path.exists(f"core_evolved_c{cycle_id-1}.py"):
            try:
                with open(f"core_evolved_c{cycle_id}.py", 'r') as f:
                    current_code = f.read()
                with open(f"core_evolved_c{cycle_id-1}.py", 'r') as f:
                    previous_code = f.read()
                
                # Análise de diferenças
                metrics["code_diff"] = {
                    "lines_added": len(current_code.split('\n')) - len(previous_code.split('\n')),
                    "size_diff_bytes": len(current_code) - len(previous_code),
                    "size_diff_percent": (len(current_code) - len(previous_code)) / len(previous_code) * 100 if previous_code else 0
                }
                
                # Análise de qualidade de código (simplificada)
                try:
                    current_ast = ast.parse(current_code)
                    metrics["code_quality"] = {
                        "syntax_valid": True
                    }
                except SyntaxError:
                    metrics["code_quality"] = {
                        "syntax_valid": False
                    }
            except Exception as e:
                logger.error(f"Erro na análise de código para ciclo {cycle_id}: {e}")
                metrics["code_analysis_error"] = str(e)
        
        # Armazena as métricas de impacto
        self.impact_metrics[cycle_id] = metrics
        
        return metrics
    
    def generate_feedback(self, impact_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera feedback baseado nas métricas de impacto para orientar futuras transformações.
        
        Args:
            impact_metrics: Métricas de impacto de um ciclo
            
        Returns:
            Dicionário com feedback e recomendações
        """
        feedback = {
            "cycle_id": impact_metrics.get("cycle_id"),
            "timestamp": time.time(),
            "recommendations": []
        }
        
        # Análise de classificação de impacto
        impact_class = impact_metrics.get("impact_classification")
        
        if impact_class == "negative":
            feedback["recommendations"].append({
                "type": "refactor",
                "priority": "high",
                "description": "Priorizar refatoração para reduzir complexidade e melhorar desempenho",
                "targets": impact_metrics.get("targets", [])
            })
        
        elif impact_class == "mixed":
            feedback["recommendations"].append({
                "type": "optimize",
                "priority": "medium",
                "description": "Manter expansão funcional, mas focar em otimização de desempenho",
                "targets": impact_metrics.get("targets", [])
            })
        
        elif impact_class == "concerning":
            feedback["recommendations"].append({
                "type": "optimize",
                "priority": "high",
                "description": "Priorizar otimização de desempenho nos componentes afetados",
                "targets": impact_metrics.get("targets", [])
            })
        
        elif impact_class == "positive":
            feedback["recommendations"].append({
                "type": "expand",
                "priority": "medium",
                "description": "Continuar expansão funcional nos componentes bem-sucedidos",
                "targets": impact_metrics.get("targets", [])
            })
        
        # Análise de mudanças específicas em métricas
        if "complexity_changes" in impact_metrics:
            for metric, change in impact_metrics["complexity_changes"].items():
                component = metric.split("_")[0]
                if change > 1.2:  # Aumento significativo de complexidade
                    feedback["recommendations"].append({
                        "type": "refactor",
                        "priority": "medium",
                        "description": f"Refatorar componente {component} para reduzir complexidade",
                        "targets": [component]
                    })
        
        if "performance_changes" in impact_metrics:
            for metric, change in impact_metrics["performance_changes"].items():
                component = metric.split("_")[0]
                if change < 0.8:  # Redução significativa de desempenho
                    feedback["recommendations"].append({
                        "type": "optimize",
                        "priority": "high",
                        "description": f"Otimizar desempenho do componente {component}",
                        "targets": [component]
                    })
        
        # Análise de código
        if "code_quality" in impact_metrics and not impact_metrics["code_quality"].get("syntax_valid", True):
            feedback["recommendations"].append({
                "type": "fix",
                "priority": "critical",
                "description": "Corrigir erros de sintaxe introduzidos no último ciclo",
                "targets": impact_metrics.get("targets", [])
            })
        
        # Diversificação
        if len(set(impact_metrics.get("targets", []))) <= 1:
            feedback["recommendations"].append({
                "type": "diversify",
                "priority": "low",
                "description": "Diversificar alvos de transformação para evolução mais equilibrada",
                "targets": []
            })
        
        # Armazena o feedback gerado
        self.feedback_history.append(feedback)
        
        return feedback
    
    def apply_feedback_to_hypothesis(self, hypothesis: Dict[str, Any], feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica feedback para ajustar uma hipótese de melhoria.
        
        Args:
            hypothesis: Hipótese original
            feedback: Feedback gerado
            
        Returns:
            Hipótese ajustada com base no feedback
        """
        adjusted_hypothesis = hypothesis.copy()
        
        # Ajusta prioridade com base nas recomendações
        for recommendation in feedback.get("recommendations", []):
            if recommendation.get("targets") and hypothesis.get("target") in recommendation.get("targets"):
                # Ajusta tipo de hipótese se necessário
                if recommendation.get("type") == "refactor" and hypothesis.get("type") != "refactor_simplification":
                    adjusted_hypothesis["type"] = "refactor_simplification"
                    adjusted_hypothesis["reason"] = f"{adjusted_hypothesis.get('reason')} (ajustado por feedback: {recommendation.get('description')})"
                
                elif recommendation.get("type") == "optimize" and hypothesis.get("type") != "optimize_performance":
                    adjusted_hypothesis["type"] = "optimize_performance"
                    adjusted_hypothesis["reason"] = f"{adjusted_hypothesis.get('reason')} (ajustado por feedback: {recommendation.get('description')})"
                
                # Ajusta prioridade
                priority_map = {"critical": 0.9, "high": 0.8, "medium": 0.7, "low": 0.6}
                rec_priority = priority_map.get(recommendation.get("priority"), 0.5)
                
                # Aumenta a prioridade se a recomendação tiver prioridade maior
                if rec_priority > adjusted_hypothesis.get("priority", 0.5):
                    adjusted_hypothesis["priority"] = rec_priority
        
        # Marca a hipótese como ajustada por feedback
        adjusted_hypothesis["feedback_adjusted"] = True
        
        return adjusted_hypothesis
    
    def evaluate_all_cycles(self) -> List[Dict[str, Any]]:
        """
        Avalia o impacto de todos os ciclos no histórico.
        
        Returns:
            Lista com métricas de impacto para todos os ciclos
        """
        results = []
        
        for cycle in self.cycle_history:
            cycle_id = cycle.get("cycle_id")
            if cycle_id is not None:
                impact = self.evaluate_impact(cycle_id)
                results.append(impact)
        
        return results
    
    def save_evaluation_results(self, filename: str = "impact_evaluation_results.json") -> None:
        """
        Salva os resultados da avaliação de impacto em um arquivo JSON.
        
        Args:
            filename: Nome do arquivo para salvar os resultados
        """
        results = {
            "timestamp": time.time(),
            "impact_metrics": self.impact_metrics,
            "feedback_history": self.feedback_history
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Resultados de avaliação de impacto salvos em {filename}")
        except Exception as e:
            logger.error(f"Erro ao salvar resultados de avaliação: {e}")
    
    def generate_report(self) -> str:
        """
        Gera um relatório de avaliação de impacto em formato Markdown.
        
        Returns:
            Relatório em formato Markdown
        """
        report = "# Relatório de Avaliação de Impacto - AI-Genesis Core\n\n"
        report += f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "## Resumo de Impacto por Ciclo\n\n"
        report += "| Ciclo | Classificação | Complexidade | Desempenho | Descrição |\n"
        report += "|-------|--------------|--------------|------------|------------|\n"
        
        for cycle_id, metrics in sorted(self.impact_metrics.items()):
            classification = metrics.get("impact_classification", "N/A")
            complexity = f"{metrics.get('avg_complexity_change', 1.0):.2f}x" if "avg_complexity_change" in metrics else "N/A"
            performance = f"{metrics.get('avg_performance_change', 1.0):.2f}x" if "avg_performance_change" in metrics else "N/A"
            description = metrics.get("impact_description", "")
            
            report += f"| {cycle_id} | {classification} | {complexity} | {performance} | {description} |\n"
        
        report += "\n## Recomendações de Feedback\n\n"
        
        for feedback in self.feedback_history:
            cycle_id = feedback.get("cycle_id")
            report += f"### Ciclo {cycle_id}\n\n"
            
            for i, rec in enumerate(feedback.get("recommendations", [])):
                report += f"**Recomendação {i+1}:** {rec.get('description')} (Prioridade: {rec.get('priority')})\n"
                if rec.get("targets"):
                    report += f"- Alvos: {', '.join(rec.get('targets'))}\n"
                report += "\n"
        
        report += "\n## Tendências de Evolução\n\n"
        
        # Análise de tendências (se houver ciclos suficientes)
        if len(self.impact_metrics) >= 3:
            complexity_trend = []
            performance_trend = []
            
            for cycle_id, metrics in sorted(self.impact_metrics.items()):
                if "avg_complexity_change" in metrics:
                    complexity_trend.append(metrics["avg_complexity_change"])
                if "avg_performance_change" in metrics:
                    performance_trend.append(metrics["avg_performance_change"])
            
            if complexity_trend:
                avg_complexity = sum(complexity_trend) / len(complexity_trend)
                report += f"- **Tendência de Complexidade:** {'Crescente' if avg_complexity > 1.05 else 'Estável' if 0.95 <= avg_complexity <= 1.05 else 'Decrescente'} (média: {avg_complexity:.2f}x)\n"
            
            if performance_trend:
                avg_performance = sum(performance_trend) / len(performance_trend)
                report += f"- **Tendência de Desempenho:** {'Crescente' if avg_performance > 1.05 else 'Estável' if 0.95 <= avg_performance <= 1.05 else 'Decrescente'} (média: {avg_performance:.2f}x)\n"
        
        return report

# Função para integrar o motor de avaliação ao ciclo evolutivo
def integrate_with_evolution_cycle(core, cycle_id: int, hypothesis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integra a avaliação de impacto ao ciclo evolutivo.
    
    Args:
        core: Instância do AI-Genesis Core
        cycle_id: ID do ciclo atual
        hypothesis: Hipótese de melhoria selecionada
        
    Returns:
        Hipótese ajustada com base no feedback
    """
    # Inicializa o motor de avaliação
    evaluator = ImpactEvaluationEngine()
    
    # Se não for o primeiro ciclo, avalia o impacto do ciclo anterior
    if cycle_id > 1:
        impact = evaluator.evaluate_impact(cycle_id - 1)
        feedback = evaluator.generate_feedback(impact)
        
        # Ajusta a hipótese com base no feedback
        adjusted_hypothesis = evaluator.apply_feedback_to_hypothesis(hypothesis, feedback)
        
        # Salva os resultados
        evaluator.save_evaluation_results()
        
        return adjusted_hypothesis
    
    return hypothesis

# Função para gerar relatório completo de avaliação
def generate_evaluation_report() -> str:
    """
    Gera um relatório completo de avaliação de impacto.
    
    Returns:
        Relatório em formato Markdown
    """
    evaluator = ImpactEvaluationEngine()
    evaluator.evaluate_all_cycles()
    report = evaluator.generate_report()
    
    # Salva o relatório em um arquivo
    try:
        with open("impact_evaluation_report.md", 'w') as f:
            f.write(report)
        logger.info("Relatório de avaliação de impacto gerado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao salvar relatório de avaliação: {e}")
    
    return report

if __name__ == "__main__":
    # Configuração de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("ai_genesis_impact.log")
        ]
    )
    
    # Executa avaliação de todos os ciclos
    evaluator = ImpactEvaluationEngine()
    results = evaluator.evaluate_all_cycles()
    
    # Gera e salva relatório
    report = evaluator.generate_report()
    with open("impact_evaluation_report.md", 'w') as f:
        f.write(report)
    
    print(f"Avaliação concluída para {len(results)} ciclos. Relatório salvo em impact_evaluation_report.md")
