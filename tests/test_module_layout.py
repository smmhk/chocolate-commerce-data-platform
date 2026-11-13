"""Check internal module paths without importing API execution scripts."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ModuleLayoutTests(unittest.TestCase):
    def test_internal_imports_resolve_to_files(self):
        paths = sorted((ROOT / "src").rglob("*.py")) + sorted((ROOT / "scripts").rglob("*.py"))
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            for node in ast.walk(tree):
                modules = ([node.module] if isinstance(node, ast.ImportFrom) and node.module
                           else [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
                for module in modules:
                    if not module.startswith(("src.", "scripts.")):
                        continue
                    target = ROOT.joinpath(*module.split("."))
                    with self.subTest(file=str(path.relative_to(ROOT)), module=module):
                        self.assertTrue(target.with_suffix(".py").is_file() or (target / "__init__.py").is_file())



if __name__ == "__main__":
    unittest.main()
