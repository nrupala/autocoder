"""AutoCoder CI/CD Builder
Adds workflows to all repos"""

import subprocess
from pathlib import Path

REPOS = {
    'autocoder': 'D:/autocoder',
    'uis': 'D:/UIS',
    'axiomcode': 'D:/axiomcode',
    'sllm': 'D:/sl/projects/sllm',
}

WORKFLOWS = {
    'tests.yml': '''name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install deps
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest tests/ -v
''',
    'lint.yml': '''name: Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install lint
        run: pip install ruff
      - name: Lint
        run: ruff check .
''',
    'typecheck.yml': '''name: Type Check

on: [push, pull_request]

jobs:
  typecheck:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install mypy
        run: pip install mypy
      - name: Type check
        run: mypy . --ignore-missing-imports
'''
}

def add_workflows(repo_path: str, name: str):
    """Add workflows to a repo."""
    wf_dir = Path(repo_path) / '.github' / 'workflows'
    wf_dir.mkdir(parents=True, exist_ok=True)
    
    for wf_name, wf_content in WORKFLOWS.items():
        wf_path = wf_dir / wf_name
        if not wf_path.exists():
            wf_path.write_text(wf_content)
            print(f'  + {wf_name}')
        else:
            print(f'  = {wf_name}')
    
    # Add README if missing
    readme = Path(repo_path) / 'README.md'
    if not readme.exists():
        readme.write_text(f'''# {name.title()}

**AutoCoder Generated**

Built by AutoCoder - pushed by Nrupal.

## Setup
```bash
pip install -r requirements.txt
```

## Run
```bash
python main.py
```
''')
        print(f'  + README.md')
    
    # Add requirements.txt if missing
    req = Path(repo_path) / 'requirements.txt'
    if not req.exists():
        req.write_text('''flask>=3.0.0
pydantic>=2.0.0
''')
        print(f'  + requirements.txt')

def build_repo(name: str) -> bool:
    """Build a repo."""
    path = REPOS.get(name)
    if not path or not Path(path).exists():
        print(f'{name}: REPO NOT FOUND')
        return False
    
    print(f'Building {name}...')
    
    try:
        # Add workflows
        add_workflows(path, name)
        
        # Git add/commit/push
        subprocess.run(['git', 'add', '.'], cwd=path, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'pushed by Nrupal built with autocoder'], cwd=path, capture_output=True)
        subprocess.run(['git', 'push'], cwd=path, capture_output=True, timeout=30)
        
        print(f'{name}: DONE')
        return True
    except Exception as e:
        print(f'{name}: ERROR - {e}')
        return False

if __name__ == '__main__':
    print('=== AutoCoder CI/CD Builder ===')
    for repo in REPOS:
        build_repo(repo)