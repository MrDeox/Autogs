# Unit tests for AI-Genesis Core logic

import importlib # Required to potentially re-import temp_evolved_code if needed by tests
# It's expected that the test execution mechanism in core.py makes 
# the modified code available as 'temp_evolved_code' in sys.modules.

def test_analyze_code_basic_stats():
    """Tests basic code analysis stats from CodeTransformationEngine.analyze_code."""
    try:
        # The module 'temp_evolved_code' is the dynamically loaded modified code from core.py
        import temp_evolved_code 
        
        # Reload module in case of repeated test runs in the same session (optional, but good practice)
        importlib.reload(temp_evolved_code) 
    except ImportError:
        assert False, "Failed to import temp_evolved_code. The test environment may not be set up correctly."

    engine = temp_evolved_code.CodeTransformationEngine()
    
    sample_code = (
        "import os\n"
        "\n"
        "class MyClass:\n"
        "    def my_method(self):\n"
        "        pass\n"
        "\n"
        "def my_function():\n"
        "    pass"
    )
    
    expected_stats = {
        "lines": 8,
        "classes": 1,
        "functions": 2, # my_method and my_function
        "imports": ["os"]
    }
    
    actual_stats = engine.analyze_code(sample_code)
    
    assert actual_stats["lines"] == expected_stats["lines"], f"Expected {expected_stats['lines']} lines, got {actual_stats['lines']}"
    assert actual_stats["classes"] == expected_stats["classes"], f"Expected {expected_stats['classes']} classes, got {actual_stats['classes']}"
    assert actual_stats["functions"] == expected_stats["functions"], f"Expected {expected_stats['functions']} functions, got {actual_stats['functions']}"
    assert sorted(actual_stats["imports"]) == sorted(expected_stats["imports"]), f"Expected imports {expected_stats['imports']}, got {actual_stats['imports']}"
    # Length can be tricky due to OS-specific line endings, so we'll skip asserting exact length for now.

# Add more test functions here in the future, following the 'test_*' naming convention.
