import unittest
import os
import shutil # For cleaning up created files/dirs
from unittest.mock import patch, mock_open

# Assuming core.py is in the parent directory or PYTHONPATH is set up
try:
    # This path might be used if 'tests' is a package and run with 'python -m unittest tests.test_core_utils' from parent
    from ..core import CodeFileUtils 
    from ..core import logger as core_logger 
except ImportError:
    # Fallback for running script directly or if structure is different (e.g. from workspace root)
    import sys
    # Ensure the parent directory (project root) is in sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from core import CodeFileUtils
    from core import logger as core_logger


class TestCodeFileUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = "temp_test_generated_files"
        # Ensure clean slate for test_dir if it somehow exists
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Mock the logger used in CodeFileUtils (which is core_logger)
        self.logger_patcher = patch('core.logger') 
        self.mock_logger = self.logger_patcher.start()
        self.addCleanup(self.logger_patcher.stop)


    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        # patch.stopall() # Not needed if using self.addCleanup or with statement for patches

    def test_create_module_success_new_file(self):
        filepath = os.path.join(self.test_dir, "new_mod.py")
        code = "print('hello world')"
        
        success, msg = CodeFileUtils.create_module_file(filepath, code)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, code)
        expected_message = f"Module {filepath} created/overwritten successfully."
        self.assertEqual(msg, expected_message)
        self.mock_logger.info.assert_called_with(expected_message)

    def test_create_module_success_overwrite_existing_file(self):
        filepath = os.path.join(self.test_dir, "existing_mod.py")
        initial_code = "# Initial version"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(initial_code)

        new_code = "# Overwritten version"
        success, msg = CodeFileUtils.create_module_file(filepath, new_code, overwrite=True)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, new_code)
        expected_message = f"Module {filepath} created/overwritten successfully."
        self.assertEqual(msg, expected_message)
        self.mock_logger.info.assert_called_with(expected_message)


    def test_create_module_fail_file_exists_no_overwrite(self):
        filepath = os.path.join(self.test_dir, "no_overwrite_mod.py")
        initial_code = "# Original content"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(initial_code)

        new_code = "# Attempted new content"
        success, msg = CodeFileUtils.create_module_file(filepath, new_code, overwrite=False)
        
        self.assertFalse(success)
        expected_message = f"File {filepath} already exists and overwrite is False."
        self.assertEqual(msg, expected_message)
        
        # Assert original content remains
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, initial_code)
        self.mock_logger.warning.assert_called_with(expected_message)

    def test_create_module_path_includes_multiple_new_dirs(self):
        subdir_path = os.path.join(self.test_dir, "subdir1", "subdir2")
        filepath = os.path.join(subdir_path, "nested_mod.py")
        code = "# Nested module"
        
        success, msg = CodeFileUtils.create_module_file(filepath, code)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(os.path.isdir(subdir_path)) # Verify intermediate directory
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, code)

    def test_create_module_empty_content(self):
        filepath = os.path.join(self.test_dir, "empty_mod.py")
        code = ""
        
        success, msg = CodeFileUtils.create_module_file(filepath, code)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, code) # Should be empty

    @patch('os.makedirs')
    def test_create_module_os_makedirs_fails(self, mock_makedirs):
        mock_makedirs.side_effect = OSError("Permission denied for makedirs")
        filepath = os.path.join(self.test_dir, "somedir", "makedirs_fail_mod.py")
        code = "# Test"
        
        # We need to ensure that the directory does not exist for os.makedirs to be called
        # In this test, "somedir" would be the one CodeFileUtils tries to create.
        
        success, msg = CodeFileUtils.create_module_file(filepath, code)
        
        self.assertFalse(success)
        expected_error_message = f"Unexpected error creating module file {filepath}: Permission denied for makedirs"
        self.assertEqual(msg, expected_error_message)
        self.mock_logger.error.assert_called_with(expected_error_message, exc_info=True)

    @patch('builtins.open', new_callable=mock_open)
    def test_create_module_file_write_io_error(self, mock_file_open):
        mock_file_open.return_value.write.side_effect = IOError("Disk full")
        filepath = os.path.join(self.test_dir, "io_error_mod.py")
        code = "# This will fail to write"
        
        success, msg = CodeFileUtils.create_module_file(filepath, code)
        
        self.assertFalse(success)
        expected_error_message = f"IOError writing to {filepath}: Disk full"
        self.assertEqual(msg, expected_error_message)
        self.mock_logger.error.assert_called_with(expected_error_message)

if __name__ == '__main__':
    unittest.main()
