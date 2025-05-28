import unittest
from unittest.mock import MagicMock, patch, mock_open
import hashlib
import time # For timestamping episodes
import os # For path manipulation in new tests
import re # For parsing in new tests


# Attempt to import the classes from consciousness_module.py
try:
    # This path might be used if 'tests' is a package and run with 'python -m unittest tests.test_consciousness_module' from parent
    from ..consciousness_module import EpisodicMemory, DeliberationEngine, ConsciousnessModule
    from ..core import CodeFileUtils # Add CodeFileUtils
except ImportError:
    # Fallback for running script directly or if structure is different (e.g. from workspace root)
    import sys
    # Ensure the parent directory (project root) is in sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from consciousness_module import EpisodicMemory, DeliberationEngine, ConsciousnessModule
    from core import CodeFileUtils # Add CodeFileUtils

class TestEpisodicMemory(unittest.TestCase):

    def setUp(self):
        # Mock logger to prevent console output during tests
        self.patcher = patch('consciousness_module.logger')
        self.mock_logger = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    # --- Tests for get_recent_failure_rate ---

    def test_get_recent_failure_rate_no_episodes(self):
        memory = EpisodicMemory(max_episodes=10)
        rate = memory.get_recent_failure_rate("evolution_cycle", "state1_hash")
        self.assertEqual(rate, 0.0)

    def test_get_recent_failure_rate_no_relevant_episodes(self):
        memory = EpisodicMemory(max_episodes=10)
        action_other = {'type': 'other_action'}
        result_succ = {'success': True}
        memory.episodes = [
            {'action': action_other, 'result': result_succ, 'state_hash': "state2_hash", 'timestamp': 1},
        ]
        rate = memory.get_recent_failure_rate("evolution_cycle", "state1_hash")
        self.assertEqual(rate, 0.0)

    def test_get_recent_failure_rate_all_success(self):
        memory = EpisodicMemory(max_episodes=10)
        state1_hash = "state1_hash"
        action1 = {'type': 'evolution_cycle'}
        result1 = {'modification_applied': True, 'errors': [], 'cycle_id': 1} 
        
        memory.episodes = [
            {'action': action1, 'result': result1, 'state_hash': state1_hash, 'timestamp': time.time()},
            {'action': action1, 'result': result1, 'state_hash': state1_hash, 'timestamp': time.time() + 1},
        ]
        rate = memory.get_recent_failure_rate("evolution_cycle", state1_hash, lookback_period=3)
        self.assertEqual(rate, 0.0)

    def test_get_recent_failure_rate_all_failure_evolution_cycle(self):
        memory = EpisodicMemory(max_episodes=10)
        state1_hash = "state1_hash"
        action_evo = {'type': 'evolution_cycle'}
        res_evo_fail_mod = {'modification_applied': False, 'errors': [], 'cycle_id': 2}
        
        memory.episodes = [
            {'action': action_evo, 'result': res_evo_fail_mod, 'state_hash': state1_hash, 'timestamp': 1},
            {'action': action_evo, 'result': res_evo_fail_mod, 'state_hash': state1_hash, 'timestamp': 2},
        ]
        rate = memory.get_recent_failure_rate("evolution_cycle", state1_hash, lookback_period=3)
        self.assertEqual(rate, 1.0)

    def test_get_recent_failure_rate_all_failure_generic_action(self):
        memory = EpisodicMemory(max_episodes=10)
        state1_hash = "state1_hash"
        action_insp = {'type': 'seek_external_inspiration'}
        res_insp_fail = {'success': False, 'error': 'LLM unavailable'}

        memory.episodes = [
            {'action': action_insp, 'result': res_insp_fail, 'state_hash': state1_hash, 'timestamp': 1},
            {'action': action_insp, 'result': res_insp_fail, 'state_hash': state1_hash, 'timestamp': 2},
        ]
        rate = memory.get_recent_failure_rate("seek_external_inspiration", state1_hash, lookback_period=3)
        self.assertEqual(rate, 1.0)

    def test_get_recent_failure_rate_mixed_outcomes(self):
        memory = EpisodicMemory(max_episodes=10)
        state1_hash = "state1_hash"
        action_evo = {'type': 'evolution_cycle'}
        res_succ = {'modification_applied': True, 'errors': [], 'cycle_id': 1}
        res_fail = {'modification_applied': False, 'errors': [], 'cycle_id': 2}
        
        memory.episodes = [
            {'action': action_evo, 'result': res_succ, 'state_hash': state1_hash, 'timestamp': 1},
            {'action': action_evo, 'result': res_fail, 'state_hash': state1_hash, 'timestamp': 2},
            {'action': action_evo, 'result': res_fail, 'state_hash': state1_hash, 'timestamp': 3},
        ] # 1 success, 2 failures
        rate = memory.get_recent_failure_rate("evolution_cycle", state1_hash, lookback_period=3)
        self.assertEqual(rate, 2.0/3.0)

    def test_get_recent_failure_rate_respects_lookback(self):
        memory = EpisodicMemory(max_episodes=10)
        state1_hash = "state1_hash"
        action_evo = {'type': 'evolution_cycle'}
        res_succ = {'modification_applied': True, 'errors': [], 'cycle_id': 1}
        res_fail = {'modification_applied': False, 'errors': [], 'cycle_id': 2}

        memory.episodes = [
            # This one should be ignored by lookback
            {'action': action_evo, 'result': res_fail, 'state_hash': state1_hash, 'timestamp': 1}, 
            {'action': action_evo, 'result': res_succ, 'state_hash': state1_hash, 'timestamp': 2},
            {'action': action_evo, 'result': res_succ, 'state_hash': state1_hash, 'timestamp': 3},
        ]
        rate = memory.get_recent_failure_rate("evolution_cycle", state1_hash, lookback_period=2)
        self.assertEqual(rate, 0.0) # Only sees the two successes

    def test_get_recent_failure_rate_respects_state_hash(self):
        memory = EpisodicMemory(max_episodes=10)
        action_evo = {'type': 'evolution_cycle'}
        res_fail = {'modification_applied': False, 'errors': [], 'cycle_id': 1}
        
        memory.episodes = [
            {'action': action_evo, 'result': res_fail, 'state_hash': "state1_hash", 'timestamp': 1},
            {'action': action_evo, 'result': res_fail, 'state_hash': "state2_hash", 'timestamp': 2},
        ]
        rate = memory.get_recent_failure_rate("evolution_cycle", "state1_hash", lookback_period=3)
        self.assertEqual(rate, 1.0) # Only one failure for state1_hash

    # --- Tests for extract_heuristics ---

    def test_extract_heuristics_no_episodes(self):
        memory = EpisodicMemory(max_episodes=10)
        heuristics = memory.extract_heuristics()
        self.assertEqual(heuristics, {})

    def test_extract_heuristics_various_actions_and_outcomes(self):
        memory = EpisodicMemory(max_episodes=10)
        action_evo = {'type': 'evolution_cycle'}
        action_insp = {'type': 'seek_external_inspiration'}
        
        res_evo_succ = {'modification_applied': True, 'errors': [], 'cycle_id': 1}
        res_evo_fail_mod = {'modification_applied': False, 'errors': [], 'cycle_id': 2}
        res_evo_fail_err = {'modification_applied': True, 'errors': ['some_error'], 'cycle_id': 3}
        
        res_insp_succ = {'success': True, 'llm_suggestion': 'think'}
        res_insp_fail = {'success': False, 'error': 'LLM unavailable'}
        res_insp_succ_no_explicit_key = {} # Generic action success (success=True is default)

        memory.episodes = [
            {'action': action_evo, 'result': res_evo_succ, 'state_hash': 's1', 'timestamp': 1},
            {'action': action_evo, 'result': res_evo_succ, 'state_hash': 's2', 'timestamp': 2},
            {'action': action_evo, 'result': res_evo_fail_mod, 'state_hash': 's3', 'timestamp': 3},
            {'action': action_evo, 'result': res_evo_fail_err, 'state_hash': 's4', 'timestamp': 4}, 
            {'action': action_insp, 'result': res_insp_succ, 'state_hash': 's5', 'timestamp': 5},
            {'action': action_insp, 'result': res_insp_fail, 'state_hash': 's6', 'timestamp': 6},
            {'action': {'type': 'other_action'}, 'result': {'success': True}, 'state_hash': 's7', 'timestamp': 7},
            {'action': {'type': 'other_generic_succ'}, 'result': res_insp_succ_no_explicit_key, 'state_hash': 's8', 'timestamp': 8}
        ]
        
        heuristics = memory.extract_heuristics()
        
        self.assertIn('evolution_cycle', heuristics)
        self.assertEqual(heuristics['evolution_cycle']['total_attempts'], 4.0)
        self.assertEqual(heuristics['evolution_cycle']['success_rate'], 0.5) # 2/4
        
        self.assertIn('seek_external_inspiration', heuristics)
        self.assertEqual(heuristics['seek_external_inspiration']['total_attempts'], 2.0)
        self.assertEqual(heuristics['seek_external_inspiration']['success_rate'], 0.5) # 1/2

        self.assertIn('other_action', heuristics)
        self.assertEqual(heuristics['other_action']['total_attempts'], 1.0)
        self.assertEqual(heuristics['other_action']['success_rate'], 1.0) # 1/1
        
        self.assertIn('other_generic_succ', heuristics)
        self.assertEqual(heuristics['other_generic_succ']['total_attempts'], 1.0)
        self.assertEqual(heuristics['other_generic_succ']['success_rate'], 1.0) # 1/1 (default success)


    def test_extract_heuristics_handles_invalid_episodes(self):
        memory = EpisodicMemory(max_episodes=10)
        action_evo = {'type': 'evolution_cycle'}
        res_evo_succ = {'modification_applied': True, 'errors': [], 'cycle_id': 1}

        memory.episodes = [
            {'result': res_evo_succ, 'state_hash': 's1', 'timestamp': 1}, # Missing 'action'
            {'action': {}, 'result': res_evo_succ, 'state_hash': 's2', 'timestamp': 2}, # Action missing 'type'
            {'action': "not_a_dict", 'result': res_evo_succ, 'state_hash': 's3', 'timestamp': 3}, # Action not a dict
            {'action': action_evo, 'result': res_evo_succ, 'state_hash': 's4', 'timestamp': 4} # Valid one
        ]
        heuristics = memory.extract_heuristics()
        self.assertIn('evolution_cycle', heuristics)
        self.assertEqual(heuristics['evolution_cycle']['total_attempts'], 1.0)
        self.assertEqual(heuristics['evolution_cycle']['success_rate'], 1.0)
        self.assertEqual(len(heuristics), 1) # Only the valid one should be processed

class TestDeliberationEngine(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('consciousness_module.logger')
        self.mock_logger = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.mock_episodic_memory = MagicMock(spec=EpisodicMemory)
        self.deliberation_engine = DeliberationEngine()

    def test_generate_actions_review_failures_trigger(self):
        system_state = {
            'evolution_cycles': 10,
            'last_modification': {'cycle_id': 3}, # 7 cycles since mod
            'pending_hypotheses': [],
            'resource_usage': {'cpu_percent': 30},
            'core_metrics': {'code_transformer_complexity': 50}
        }
        actions = self.deliberation_engine.generate_potential_actions(system_state)
        review_action = next((a for a in actions if a['type'] == 'review_past_failures'), None)
        self.assertIsNotNone(review_action)
        self.assertEqual(review_action['priority'], 0.85)

    def test_generate_actions_all_priorities(self):
        system_state = {
            'evolution_cycles': 20,
            'last_modification': {'cycle_id': 10}, # 10 cycles since mod -> review_failures (0.85) & seek_external (0.75)
            'pending_hypotheses': [{'type': 'some_hypothesis'}], # -> apply_hypothesis (0.9)
            'resource_usage': {'cpu_percent': 90}, # -> optimize_performance (0.9)
            'core_metrics': {'code_transformer_complexity': 200} # -> also contributes to seek_external_inspiration
        }
        # evolution_cycle (0.5) is NOT added because pending_hypotheses is present

        actions = self.deliberation_engine.generate_potential_actions(system_state)
        
        action_map = {a['type']: a for a in actions}

        self.assertIn('apply_hypothesis', action_map)
        self.assertEqual(action_map['apply_hypothesis']['priority'], 0.9)

        self.assertIn('optimize_performance', action_map)
        self.assertEqual(action_map['optimize_performance']['priority'], 0.9)
        
        self.assertIn('review_past_failures', action_map)
        self.assertEqual(action_map['review_past_failures']['priority'], 0.85)

        self.assertIn('seek_external_inspiration', action_map)
        self.assertEqual(action_map['seek_external_inspiration']['priority'], 0.75)

        self.assertNotIn('evolution_cycle', action_map) # Should not be present due to pending_hypotheses

    def test_select_action_recent_failure_penalty(self):
        actions = [
            {'type': 'action_A', 'priority': 0.8, 'reason': 'Reason A'},
            {'type': 'action_B', 'priority': 0.7, 'reason': 'Reason B'}
        ]
        system_state = {'state_hash': 'test_hash'}
        
        self.mock_episodic_memory.get_recent_failure_rate.return_value = 0.0 # Default
        self.mock_episodic_memory.get_recent_failure_rate.side_effect = lambda type, hash: 0.6 if type == 'action_A' else 0.0
        self.mock_episodic_memory.extract_heuristics.return_value = {}

        selected_action = self.deliberation_engine.select_best_action(actions, system_state, self.mock_episodic_memory)
        
        self.assertEqual(selected_action['type'], 'action_B')
        # Original 0.8 for action_A, penalty 0.3 * 0.8 = 0.24. New priority 0.8 - 0.24 = 0.56
        # action_B priority is 0.7, so action_B should be selected.
        self.assertAlmostEqual(selected_action['priority'], 0.7) 

    def test_select_action_global_heuristic_penalty(self):
        actions = [
            {'type': 'action_A', 'priority': 0.8, 'reason': 'Reason A'},
            {'type': 'action_B', 'priority': 0.7, 'reason': 'Reason B'}
        ]
        system_state = {'state_hash': 'test_hash'}

        self.mock_episodic_memory.get_recent_failure_rate.return_value = 0.0
        self.mock_episodic_memory.extract_heuristics.return_value = {
            'action_A': {'success_rate': 0.3, 'total_attempts': 10.0} # Low success rate
        }
        selected_action = self.deliberation_engine.select_best_action(actions, system_state, self.mock_episodic_memory)
        self.assertEqual(selected_action['type'], 'action_B')
        # action_A (0.8) gets -0.15 -> 0.65. action_B (0.7) is higher.
        self.assertAlmostEqual(selected_action['priority'], 0.7)

    def test_select_action_global_heuristic_bonus(self):
        actions = [
            {'type': 'action_A', 'priority': 0.8, 'reason': 'Reason A'},
            {'type': 'action_B', 'priority': 0.85, 'reason': 'Reason B'}
        ]
        system_state = {'state_hash': 'test_hash'}
        self.mock_episodic_memory.get_recent_failure_rate.return_value = 0.0
        self.mock_episodic_memory.extract_heuristics.return_value = {
            'action_A': {'success_rate': 0.95, 'total_attempts': 10.0} # High success rate
        }
        selected_action = self.deliberation_engine.select_best_action(actions, system_state, self.mock_episodic_memory)
        self.assertEqual(selected_action['type'], 'action_A')
         # action_A (0.8) gets +0.15 -> 0.95. action_B (0.85).
        self.assertAlmostEqual(selected_action['priority'], 0.95)

    def test_select_action_priority_clamping(self):
        actions = [{'type': 'action_A', 'priority': 0.1, 'reason': 'Reason A'}] # Low initial
        system_state = {'state_hash': 'test_hash'}
        self.mock_episodic_memory.get_recent_failure_rate.return_value = 0.8 # High recent failure -> penalty
        self.mock_episodic_memory.extract_heuristics.return_value = {
            'action_A': {'success_rate': 0.1, 'total_attempts': 10.0} # Very low global success -> penalty
        }
        # Phase 1: 0.1 * 0.3 = 0.03 penalty. Priority = 0.1 - 0.03 = 0.07
        # Phase 2: 0.07 - 0.15 (for success_rate < 0.4) = -0.08, clamped to 0.0
        selected_action = self.deliberation_engine.select_best_action(actions, system_state, self.mock_episodic_memory)
        self.assertAlmostEqual(selected_action['priority'], 0.0)

        actions_high = [{'type': 'action_B', 'priority': 0.9, 'reason': 'Reason B'}] # High initial
        self.mock_episodic_memory.get_recent_failure_rate.return_value = 0.0 # No recent failure
        self.mock_episodic_memory.extract_heuristics.return_value = {
            'action_B': {'success_rate': 0.95, 'total_attempts': 10.0} # Very high global success -> bonus
        }
        # Phase 1: No change, priority = 0.9
        # Phase 2: 0.9 + 0.15 (for success_rate > 0.9) = 1.05, clamped to 1.0
        selected_action_high = self.deliberation_engine.select_best_action(actions_high, system_state, self.mock_episodic_memory)
        self.assertAlmostEqual(selected_action_high['priority'], 1.0)


class TestConsciousnessModuleActions(unittest.TestCase):
    def setUp(self):
        self.logger_patcher = patch('consciousness_module.logger')
        self.mock_logger = self.logger_patcher.start()

        self.mock_core_ref = MagicMock(name="CoreRef")
        self.mock_core_ref.meta_cognition = MagicMock()
        self.mock_core_ref.meta_cognition.evaluate_system.return_value = {} 
        self.mock_core_ref.components = {}
        self.mock_core_ref.evolution_cycles = 0
        self.mock_core_ref.security = MagicMock()
        self.mock_core_ref.security.modification_log = []


        self.consciousness = ConsciousnessModule(core_reference=self.mock_core_ref)
        
        self.consciousness.self_reflection = MagicMock() 
        self.consciousness.self_reflection.analyze_system_state.return_value = {'evolution_cycles': 0} 

        self.consciousness.episodic_memory = MagicMock(spec=EpisodicMemory)
        
        self.consciousness.augmented_cognition = MagicMock()
        self.consciousness.augmented_cognition.openrouter = MagicMock()
        self.consciousness.augmented_cognition.openrouter.generate_completion = MagicMock()
        
        # Configurable side_effect for enhance_with_llm
        def mock_enhance_with_llm(action, core_state):
            if hasattr(self.consciousness.augmented_cognition.enhance_with_llm, 'return_value_config'):
                return self.consciousness.augmented_cognition.enhance_with_llm.return_value_config
            # Default behavior if not configured by a specific test
            return {'llm_suggestion': "Default mock suggestion"} if action.get('type') != 'no_suggestion_action' else None
        
        self.consciousness.augmented_cognition.enhance_with_llm.side_effect = mock_enhance_with_llm


    def tearDown(self):
        self.logger_patcher.stop()
        patch.stopall() 


    def test_execute_review_past_failures_no_recent_failures(self):
        self.consciousness.episodic_memory.episodes = []
        action = {'type': 'review_past_failures'}
        result = self.consciousness._execute_action(action)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Nenhuma falha significativa recente para revisar.')
        self.consciousness.augmented_cognition.openrouter.generate_completion.assert_not_called()

    def test_execute_review_past_failures_with_llm_suggestion(self):
        failed_episode = {
            'action': {'type': 'evolution_cycle', 'target': 'test_module', 'reason': 'test_reason'},
            'result': {'modification_applied': False, 'errors': ['Test error']},
            'state_hash': 'hash1',
            'timestamp': time.time()
        }
        self.consciousness.episodic_memory.episodes = [failed_episode]
        self.consciousness.augmented_cognition.openrouter.generate_completion.return_value = "LLM suggestion content"
        
        action = {'type': 'review_past_failures'}
        result = self.consciousness._execute_action(action)

        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'LLM consultado sobre falhas passadas.')
        self.assertEqual(result['llm_suggestion'], "LLM suggestion content")
        self.consciousness.augmented_cognition.openrouter.generate_completion.assert_called_once()
        
        call_args = self.consciousness.augmented_cognition.openrouter.generate_completion.call_args
        prompt_sent = call_args.kwargs['prompt']
        self.assertIn("Falha na ação 'evolution_cycle' (Alvo: test_module) (Razão: test_reason).", prompt_sent)
        self.assertIn("Detalhe do erro: Test error", prompt_sent)


    def test_execute_review_past_failures_llm_fails(self):
        failed_episode = {
            'action': {'type': 'evolution_cycle'},
            'result': {'modification_applied': False, 'errors': ['Another error']},
            'state_hash': 'hash2',
            'timestamp': time.time()
        }
        self.consciousness.episodic_memory.episodes = [failed_episode]
        self.consciousness.augmented_cognition.openrouter.generate_completion.return_value = None 

        action = {'type': 'review_past_failures'}
        result = self.consciousness._execute_action(action)

        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'LLM não forneceu sugestões ou a chamada falhou.')
        self.consciousness.augmented_cognition.openrouter.generate_completion.assert_called_once()
        self.assertIn("Falha na ação 'evolution_cycle'", result['prompt_sent'])
        self.assertIn("Detalhe do erro: Another error", result['prompt_sent'])

    # --- New tests for architecture_expansion ---
    @patch('consciousness_module.CodeFileUtils.create_module_file')
    def test_execute_architecture_expansion_success(self, mock_create_module_file):
        llm_response_text = """
        Suggested Filename: new_component.py
        Main Class: NewComponent
        ```python
        class NewComponent:
            def __init__(self, core_ref):
                self.core = core_ref
                print("NewComponent initialized")
            
            def perform_task(self):
                return "task_done"
        ```
        Some other text.
        """
        self.consciousness.augmented_cognition.enhance_with_llm.return_value_config = {'llm_suggestion': llm_response_text}
        mock_create_module_file.return_value = (True, "File created successfully")
        
        action = {'type': 'architecture_expansion', 'reason': 'Test expansion'}
        result = self.consciousness._execute_action(action)

        self.assertTrue(result['success'])
        expected_filepath = os.path.join("generated_modules", "new_component.py")
        self.assertEqual(result['filepath'], expected_filepath)
        
        expected_parsed_code = 'class NewComponent:\n            def __init__(self, core_ref):\n                self.core = core_ref\n                print("NewComponent initialized")\n            \n            def perform_task(self):\n                return "task_done"'
        mock_create_module_file.assert_called_once_with(expected_filepath, expected_parsed_code, overwrite=False)
        
        self.assertIn("Integração do módulo", result['integration_hint'])
        self.assertIn("new_component.NewComponent(self)", result['integration_hint'])

    def test_execute_architecture_expansion_llm_fails(self):
        self.consciousness.augmented_cognition.enhance_with_llm.return_value_config = None # Simulate LLM failure
        
        action = {'type': 'architecture_expansion', 'reason': 'Test LLM fail'}
        result = self.consciousness._execute_action(action)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], "Falha ao obter sugestão do LLM.")

    @patch('consciousness_module.CodeFileUtils.create_module_file')
    def test_execute_architecture_expansion_parsing_fails_no_code(self, mock_create_module_file):
        llm_response_text = "No code block here. Just text. Suggested Filename: test.py"
        self.consciousness.augmented_cognition.enhance_with_llm.return_value_config = {'llm_suggestion': llm_response_text}
        
        action = {'type': 'architecture_expansion', 'reason': 'Test no code'}
        result = self.consciousness._execute_action(action)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], "Nenhum bloco de código Python utilizável encontrado na resposta do LLM.")
        mock_create_module_file.assert_not_called()

    @patch('consciousness_module.CodeFileUtils.create_module_file')
    @patch('time.time', MagicMock(return_value=12345)) # Mock time for predictable fallback filename
    def test_execute_architecture_expansion_parsing_fallback_filename_classname(self, mock_create_module_file):
        llm_response_text = """
        ```python
        class MyFallbackComponent:
            def __init__(self):
                pass
        ```
        """
        self.consciousness.augmented_cognition.enhance_with_llm.return_value_config = {'llm_suggestion': llm_response_text}
        mock_create_module_file.return_value = (True, "File created successfully")
        
        action = {'type': 'architecture_expansion', 'reason': 'Test fallbacks'}
        result = self.consciousness._execute_action(action)

        self.assertTrue(result['success'])
        expected_filename = "generated_module_12345.py"
        expected_filepath = os.path.join("generated_modules", expected_filename)
        self.assertEqual(result['filepath'], expected_filepath)
        
        expected_parsed_code = 'class MyFallbackComponent:\n            def __init__(self):\n                pass'
        mock_create_module_file.assert_called_once_with(expected_filepath, expected_parsed_code, overwrite=False)
        self.assertIn("MyFallbackComponent(self)", result['integration_hint']) # Class name inferred
        self.assertIn(f"from generated_modules import {expected_filename[:-3]}", result['integration_hint'])


    @patch('consciousness_module.CodeFileUtils.create_module_file')
    def test_execute_architecture_expansion_file_creation_fails(self, mock_create_module_file):
        llm_response_text = "```python\nclass Test: pass\n```"
        self.consciousness.augmented_cognition.enhance_with_llm.return_value_config = {'llm_suggestion': llm_response_text}
        mock_create_module_file.return_value = (False, "Disk full error from mock")
        
        action = {'type': 'architecture_expansion', 'reason': 'Test file fail'}
        result = self.consciousness._execute_action(action)
        
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], "Falha ao criar o arquivo do novo módulo: Disk full error from mock")

if __name__ == '__main__':
    unittest.main()
