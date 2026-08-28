import os
import re

MODULES = [
    'models.py',
    'cli.py',
    'scanner.py',
    'languages.py',
    'metrics.py',
    'todos.py',
    'security.py',
    'duplicates.py',
    'structure.py',
    'git.py',
    'scoring.py',
    'report.py',
    'baseline.py',
    '__main__.py'
]

def build():
    root = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.join(root, 'repodoctor')
    out_file = os.path.join(root, 'repodoctor_single.py')
    
    combined = []
    combined.append("#!/usr/bin/env python3")
    combined.append("# RepoDoctor - Zero Dependency Hackathon Submission")
    combined.append("# Auto-generated single-file version.")
    combined.append("")
    
    imports = set()
    code_blocks = []
    
    for mod in MODULES:
        with open(os.path.join(repo, mod), 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.split('\n')
        filtered_lines = []
        for line in lines:
            # Skip relative imports within the package
            if re.match(r'^\s*from\s+\..+\s+import\s+', line):
                continue
            # Collect standard library imports
            if line.startswith('import ') or line.startswith('from '):
                imports.add(line)
                continue
            
            filtered_lines.append(line)
            
        code_blocks.append(f"\n# --- {mod} ---\n")
        code_blocks.append('\n'.join(filtered_lines))
        
    for imp in sorted(imports):
        combined.append(imp)
        
    combined.extend(code_blocks)
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(combined))
        
    print(f"Successfully built single-file version: {out_file}")

if __name__ == "__main__":
    build()
