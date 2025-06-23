import os
import sys
import tempfile
import unittest
import io
from contextlib import redirect_stdout
from pathlib import Path

# ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sample_env.main import find_env_vars_in_file, find_all_env_vars, write_sample, main


class TestMakeEnvSample(unittest.TestCase):
    def setUp(self):
        # create temporary directory and switch to it
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        self.original_cwd = os.getcwd()
        os.chdir(self.tmp_dir.name)

    def tearDown(self):
        # restore working directory
        os.chdir(self.original_cwd)

    def create_file(self, relative_path, content):
        path = os.path.join(self.tmp_dir.name, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_find_env_vars_in_file(self):
        code = """
import os
from os import environ

# getenv usage
val1 = os.getenv("FOO")
# environ.get usage
val2 = os.environ.get('BAR', 'default')
# direct environ.get
val3 = environ.get("BAZ")
# subscript os.environ
val4 = os.environ["QUX"]
# subscript environ
val5 = environ['QUUX']
# dynamic key should not be captured
key = 'DYN'
val6 = os.getenv(key)
"""
        sample_path = self.create_file("sample.py", code)
        found = find_env_vars_in_file(Path(sample_path))
        self.assertEqual(found, {"FOO", "BAR", "BAZ", "QUX", "QUUX"})

    def test_find_all_env_vars(self):
        code1 = 'import os; x = os.getenv("ONE")'
        code2 = 'from os import environ; y = environ.get("TWO")'
        self.create_file("a.py", code1)
        dir2 = os.path.join(self.tmp_dir.name, "dir2")
        os.makedirs(dir2, exist_ok=True)
        with open(os.path.join(dir2, "b.py"), "w", encoding="utf-8") as f:
            f.write(code2)
        all_found = find_all_env_vars(self.tmp_dir.name)
        self.assertEqual(all_found, {"ONE", "TWO"})

    def test_gitignore_exclusion(self):
        # Create a .gitignore file
        gitignore_content = "ignored_dir/\nignored_file.py\n.venv\nbuild/\n"
        self.create_file('.gitignore', gitignore_content)

        # Create files that should be ignored
        self.create_file('ignored_dir/ignored.py', 'import os; x = os.getenv("SHOULD_NOT_BE_FOUND")')
        self.create_file('ignored_dir/nested/inner.py', 'import os; y = os.getenv("NESTED_NOT_FOUND")')
        self.create_file('ignored_file.py', 'import os; y = os.getenv("ALSO_NOT_FOUND")')
        self.create_file('.venv/venv_file.py', 'import os; y = os.getenv("VENV_VAR")')
        self.create_file('sub/.venv/nested.py', 'import os; y = os.getenv("SUB_VENV")')
        self.create_file('sub/build/skip.py', 'import os; y = os.getenv("BUILD_VAR")')

        # Create a file that should be included
        self.create_file("included.py", 'import os; z = os.getenv("SHOULD_BE_FOUND")')

        all_found = find_all_env_vars(self.tmp_dir.name)
        self.assertEqual(all_found, {"SHOULD_BE_FOUND"})
        vars_set = {"ZED", "ALPHA", "MIDDLE"}
        outfile = os.path.join(self.tmp_dir.name, "out.env")
        buf = io.StringIO()
        with redirect_stdout(buf):
            write_sample(vars_set, outfile)
        output = buf.getvalue()
        self.assertIn("Wrote 3 entries to", output)
        with open(outfile, encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertEqual(lines, ["ALPHA=", "MIDDLE=", "ZED="])

    def test_gitignore_recursive_dir(self):
        gitignore_content = "ignored_dir/\n"
        self.create_file(".gitignore", gitignore_content)
        self.create_file(
            "ignored_dir/nested/ignored.py", 'import os; os.getenv("NOPE")'
        )
        self.create_file("included.py", 'import os; os.getenv("YEP")')
        all_found = find_all_env_vars(self.tmp_dir.name)
        self.assertEqual(all_found, {"YEP"})

    def test_main_no_vars(self):
        # no .py files => no env vars
        buf = io.StringIO()
        with redirect_stdout(buf):
            main()
        output = buf.getvalue()
        self.assertIn("No environment variables found", output)

    def test_various_patterns(self):
        cases = [
            ('val = os.environ.get("A")', {"A"}),
            ("val = environ['B']", {"B"}),
            ("val = os.getenv(123)", set()),
        ]
        for code, expected in cases:
            file_path = self.create_file(
                "t.py", f"import os\nfrom os import environ\n{code}\n"
            )
            found = find_env_vars_in_file(Path(file_path))
            self.assertEqual(found, expected)


if __name__ == "__main__":
    unittest.main()
