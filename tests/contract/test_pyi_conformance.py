"""Checks every implemented module against library_sim.pyi.

For each `# library_sim/<module>.py` section of the stub, if that module
exists in src/library_sim it must define everything the section declares:
- functions, with the same parameter names, kinds and order
- classes, with the same methods and properties
- dataclass fields in the same order (a default may be ADDED where the
  stub has none, but never removed)
- enum members with the same values
- module-level constants

Modules that don't exist yet are skipped, so this test works for every
owner as their module lands. Run just this file with:
    python3 -m unittest tests.contract.test_pyi_conformance -v
"""

from __future__ import annotations

import ast
import dataclasses
import enum
import importlib
import inspect
import re
import unittest

from tests import REPO_ROOT

STUB = REPO_ROOT / "library_sim.pyi"
SECTION_RE = re.compile(r"^# library_sim/(\w+)\.py\b")


def stub_sections() -> dict[str, list[ast.stmt]]:
    """Module name -> top-level stub statements in that module's section."""
    source = STUB.read_text(encoding="utf-8")
    headers: list[tuple[int, str]] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        m = SECTION_RE.match(line)
        if m:
            headers.append((lineno, m.group(1)))
    sections: dict[str, list[ast.stmt]] = {name: [] for _, name in headers}
    for node in ast.parse(source).body:
        owner = None
        for lineno, name in headers:
            if lineno < node.lineno:
                owner = name
        if owner is not None:
            sections[owner].append(node)
    return sections


def stub_params(fn: ast.FunctionDef) -> list[tuple[str, str, bool]]:
    """(name, kind, has_default) for each parameter of a stub function."""
    a = fn.args
    out: list[tuple[str, str, bool]] = []
    positional = a.posonlyargs + a.args
    first_default = len(positional) - len(a.defaults)
    for i, arg in enumerate(positional):
        kind = "POSITIONAL_ONLY" if i < len(a.posonlyargs) else "POSITIONAL_OR_KEYWORD"
        out.append((arg.arg, kind, i >= first_default))
    if a.vararg:
        out.append((a.vararg.arg, "VAR_POSITIONAL", False))
    for arg, default in zip(a.kwonlyargs, a.kw_defaults):
        out.append((arg.arg, "KEYWORD_ONLY", default is not None))
    if a.kwarg:
        out.append((a.kwarg.arg, "VAR_KEYWORD", False))
    return out


def impl_params(obj: object) -> list[tuple[str, str, bool]]:
    sig = inspect.signature(obj)  # type: ignore[arg-type]
    return [(p.name, p.kind.name, p.default is not inspect.Parameter.empty)
            for p in sig.parameters.values()]


def is_dataclass_stub(cls: ast.ClassDef) -> bool:
    return any(
        (isinstance(d, ast.Name) and d.id == "dataclass")
        or (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass")
        for d in cls.decorator_list
    )


def is_property_stub(fn: ast.FunctionDef) -> bool:
    return any(isinstance(d, ast.Name) and d.id == "property" for d in fn.decorator_list)


class PyiConformance(unittest.TestCase):
    def test_modules_match_stub(self) -> None:
        checked = 0
        for module_name, nodes in stub_sections().items():
            try:
                module = importlib.import_module(f"library_sim.{module_name}")
            except ModuleNotFoundError as exc:
                if exc.name == f"library_sim.{module_name}":
                    continue  # not written yet: its owner's job
                raise
            checked += 1
            with self.subTest(module=module_name):
                self.check_module(module_name, module, nodes)
        self.assertGreater(checked, 0, "no library_sim modules found under src/")

    def check_module(self, module_name: str, module: object, nodes: list[ast.stmt]) -> None:
        where = f"library_sim.{module_name}"
        for node in nodes:
            if isinstance(node, ast.FunctionDef):
                self.check_function(where, getattr(module, node.name, None), node)
            elif isinstance(node, ast.ClassDef):
                self.check_class(where, getattr(module, node.name, None), node)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                self.assertTrue(hasattr(module, node.target.id),
                                f"{where}.{node.target.id} is missing")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.assertTrue(hasattr(module, target.id),
                                        f"{where}.{target.id} is missing")

    def check_function(self, where: str, impl: object, node: ast.FunctionDef) -> None:
        name = f"{where}.{node.name}"
        self.assertTrue(callable(impl), f"{name} is missing or not callable")
        expected = stub_params(node)
        actual = impl_params(impl)
        self.assertEqual([p[:2] for p in actual], [p[:2] for p in expected],
                         f"{name}: parameters differ from the stub")
        for (pname, _, stub_default), (_, _, impl_default) in zip(expected, actual):
            if stub_default:
                self.assertTrue(impl_default, f"{name}: parameter {pname!r} needs a default")

    def check_class(self, where: str, impl: object, node: ast.ClassDef) -> None:
        name = f"{where}.{node.name}"
        self.assertTrue(inspect.isclass(impl), f"{name} is missing or not a class")
        assert inspect.isclass(impl)

        base_names = {b.id for b in node.bases if isinstance(b, ast.Name)}
        if "Enum" in base_names:
            self.assertTrue(issubclass(impl, enum.Enum), f"{name} must be an Enum")
        if "Exception" in base_names:
            self.assertTrue(issubclass(impl, Exception), f"{name} must be an Exception")

        if is_dataclass_stub(node):
            self.assertTrue(dataclasses.is_dataclass(impl), f"{name} must be a dataclass")
            impl_fields = [f for f in dataclasses.fields(impl)]
            stub_fields = [s for s in node.body
                           if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)]
            self.assertEqual([f.name for f in impl_fields[:len(stub_fields)]],
                             [s.target.id for s in stub_fields],  # type: ignore[union-attr]
                             f"{name}: fields differ from the stub (names or order)")
            for s, f in zip(stub_fields, impl_fields):
                if s.value is not None:
                    has_default = (f.default is not dataclasses.MISSING
                                   or f.default_factory is not dataclasses.MISSING)
                    self.assertTrue(has_default, f"{name}.{f.name} needs a default")

        for item in node.body:
            if isinstance(item, ast.Assign) and issubclass(impl, enum.Enum):
                for target in item.targets:
                    if isinstance(target, ast.Name) and isinstance(item.value, ast.Constant):
                        self.assertIn(target.id, impl.__members__, f"{name}.{target.id} missing")
                        self.assertEqual(impl[target.id].value, item.value.value,
                                         f"{name}.{target.id} has the wrong value")
            elif isinstance(item, ast.FunctionDef):
                attr = inspect.getattr_static(impl, item.name, None)
                self.assertIsNotNone(attr, f"{name}.{item.name} is missing")
                if is_property_stub(item):
                    self.assertIsInstance(attr, property, f"{name}.{item.name} must be a property")
                    continue
                if item.name == "__init__" and dataclasses.is_dataclass(impl):
                    continue
                if isinstance(attr, (staticmethod, classmethod)):
                    continue
                self.check_function(name, getattr(impl, item.name), item)


if __name__ == "__main__":
    unittest.main()
