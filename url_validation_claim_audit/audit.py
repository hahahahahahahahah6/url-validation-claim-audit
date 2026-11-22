"""Static documentation and Python source analysis."""
import ast
import os
import re
from pathlib import Path
from .phrases import URLVALIDATION, NOURLVALIDATION, GENERIC_NAMES


def _pattern(phrases):
    return re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(x) for x in sorted(phrases, key=lambda x: (-len(x), x))) + r')(?!\w)')

YES, NO = _pattern(URLVALIDATION), _pattern(NOURLVALIDATION)


def claims(text):
    lines = []
    fence = None
    for line in text.splitlines():
        m = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
                fence = None
            continue
        if m:
            fence = m.group(1)
            lines.append('')
        else:
            lines.append(line)
    yes, no = [], []
    for paragraph in re.split(r'\n\s*\n', '\n'.join(lines)):
        paragraph = re.sub(r'\s+', ' ', paragraph.lower().replace("n't", ' not').replace('-', ' '))
        no.extend(m.group() for m in NO.finditer(paragraph))
        paragraph = NO.sub(' ', paragraph)
        yes.extend(m.group() for m in YES.finditer(paragraph))
    return yes, no


def evidence(source):
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return False
    imports, definitions, bound = {}, set(), set()
    nodes = list(ast.walk(tree))
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.add(node.name)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name.split('.')[0]] = alias.name if alias.asname else alias.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                imports[alias.asname or alias.name] = node.module + '.' + alias.name
        targets = []
        if isinstance(node, ast.Assign): targets = node.targets
        elif isinstance(node, ast.AnnAssign): targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)): targets = [i.optional_vars for i in node.items if i.optional_vars]
        for target in targets:
            bound.update(x.id for x in ast.walk(target) if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store))
    def usable(name):
        return name in imports and name not in bound and name not in definitions
    def root(node):
        while isinstance(node, ast.Attribute): node = node.value
        return node.id if isinstance(node, ast.Name) else None
    def route(func, names, paths, libraries):
        if isinstance(func, ast.Name):
            return usable(func.id) and imports[func.id] in paths
        if isinstance(func, ast.Attribute) and func.attr in names and func.attr not in definitions:
            base = root(func)
            return usable(base) and any(imports[base] == lib or imports[base].startswith(lib + '.') for lib in libraries)
        return False
    def construction(call):
        return isinstance(call, ast.Call) and route(call.func, {'URLValidator'}, {'django.core.validators.URLValidator'}, {'django'})
    instances = set()
    for node in nodes:
        pairs = []
        if isinstance(node, ast.Assign): pairs = [(target, node.value) for target in node.targets]
        elif isinstance(node, ast.AnnAssign): pairs = [(node.target, node.value)]
        elif isinstance(node, (ast.With, ast.AsyncWith)): pairs = [(i.optional_vars, i.context_expr) for i in node.items]
        for target, value in pairs:
            if isinstance(target, ast.Name) and construction(value): instances.add(target.id)
    for node in nodes:
        if not isinstance(node, ast.Call): continue
        f = node.func
        if route(f, {'url'}, {'validators.url'}, {'validators'}): return True
        if route(f, {'AnyUrl', 'HttpUrl', 'AnyHttpUrl'}, {p + '.' + n for p in ('pydantic', 'pydantic.networks') for n in ('AnyUrl', 'HttpUrl', 'AnyHttpUrl')}, {'pydantic'}): return True
        if route(f, {'parse', 'match'}, {'rfc3987.parse', 'rfc3987.match'}, {'rfc3987'}): return True
        if construction(f): return True
        if isinstance(f, ast.Name):
            if f.id in instances and f.id not in definitions: return True
            if usable(f.id) and imports[f.id].split('.')[-1] in GENERIC_NAMES and imports[f.id].split('.')[-1] not in definitions: return True
        elif isinstance(f, ast.Attribute) and f.attr in GENERIC_NAMES and f.attr not in definitions:
            base = root(f)
            if base not in imports or usable(base): return True
    return False


def audit(root, ignore=()):
    root = Path(root)
    if not root.is_dir() or not os.access(root, os.R_OK | os.X_OK): raise OSError('root is not a readable directory')
    ignored = [Path(x).as_posix().strip('/') for x in ignore]
    docs, production, tests = [], [], []
    def skip(rel):
        s = rel.as_posix()
        return any(s == x or s.startswith(x + '/') for x in ignored if x)
    def onerror(err): raise err
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
        d = Path(directory)
        dirs[:] = sorted(x for x in dirs if not (d/x).is_symlink() and not skip((d/x).relative_to(root)))
        for name in sorted(files):
            path = d/name
            rel = path.relative_to(root)
            if path.is_symlink() or skip(rel): continue
            if (rel == Path('README.md') or ('docs' in rel.parts and path.suffix == '.md')):
                docs.append((rel.as_posix(), path.read_text(encoding='utf-8')))
            elif path.suffix == '.py':
                if any(x in rel.parts for x in ('fixtures', 'docs', 'examples')): continue
                target = tests if 'tests' in rel.parts or name.startswith('test_') or name.endswith('_test.py') else production
                if evidence(path.read_text(encoding='utf-8')): target.append(rel.as_posix())
    yes, no = [], []
    for path, content in docs:
        a, b = claims(content)
        yes.extend({'path': path, 'phrase': x} for x in a)
        no.extend({'path': path, 'phrase': x} for x in b)
    findings = []
    if yes and not production:
        findings.append({'id': 'documented-url-validation-claim-false', 'severity': 'MEDIUM' if tests else 'HIGH', 'claims': yes, 'evidence': tests})
    if no and production:
        findings.append({'id': 'documented-no-url-validation-claim-false', 'severity': 'HIGH', 'claims': no, 'evidence': production})
    return {'findings': findings, 'production_evidence': production, 'test_evidence': tests, 'claims': yes, 'denials': no}
