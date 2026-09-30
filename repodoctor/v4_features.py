import os
import re

# 1. Dead Code Reaper
def run_dead_code(files):
    # Extremely basic heuristic for Python dead code:
    # 1. Find all `def function_name(`
    # 2. Check if `function_name` appears anywhere else in the codebase
    defined_funcs = {}
    for f in files:
        if f.language == "Python":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                # find def name(
                funcs = re.findall(r'def\s+([a-zA-Z_0-9]+)\s*\(', content)
                for func in funcs:
                    if func not in ["__init__", "__main__", "__str__", "__repr__"]:
                        defined_funcs[func] = f.relative_path
            except:
                pass
                
    if not defined_funcs:
        return "[DEAD CODE] No custom functions found to analyze."
        
    # Now scan all files to see if they are called
    used_funcs = set()
    for f in files:
        try:
            content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
            for func in defined_funcs:
                # regex to find function call or usage (not def)
                # Just string matching is fine for a rough zero-dependency check, but we exclude the def line
                # Count occurrences of the word
                occurrences = len(re.findall(r'\b' + func + r'\b', content))
                # If it appears more than once (the definition), or in a different file
                if occurrences > 0:
                    if f.relative_path != defined_funcs[func] or occurrences > 1:
                        used_funcs.add(func)
        except:
            pass
            
    dead = [func for func in defined_funcs if func not in used_funcs]
    
    if dead:
        out = f"[DEAD CODE] ☠️ Found {len(dead)} potentially unused functions!\n"
        for d in dead[:5]:
            out += f"  - {d}() in {defined_funcs[d]}\n"
        if len(dead) > 5:
            out += f"  ... and {len(dead)-5} more."
        return out
    return "[DEAD CODE] 🎉 All functions seem to be used! No dead code."

# 2. Dockerize
def run_dockerize(files, root_path):
    langs = {f.language for f in files if f.language}
    
    dockerfile = ""
    if "Python" in langs:
        dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
"""
    elif "JavaScript" in langs:
        dockerfile = """FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
CMD ["npm", "start"]
"""
    else:
        dockerfile = """FROM alpine:latest
WORKDIR /app
COPY . .
CMD ["sh"]
"""
    
    with open(os.path.join(root_path, "Dockerfile.repodoctor"), "w", encoding="utf-8") as f:
        f.write(dockerfile)
        
    ignore = "__pycache__/\n*.pyc\nnode_modules/\n.env\n.git/\n"
    with open(os.path.join(root_path, ".dockerignore"), "w", encoding="utf-8") as f:
        f.write(ignore)
        
    return "[DOCKERIZE] 🐳 Generated Dockerfile.repodoctor and .dockerignore for your project!"

# 3. Performance Profiler
def run_performance(files):
    bottlenecks = []
    for f in files:
        if f.language == "Python":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                # Check for string concatenation in loops
                if re.search(r'for\s+.*:[\s\S]*?\+=\s*["\']|while\s+.*:[\s\S]*?\+=\s*["\']', content):
                    bottlenecks.append(f"{f.relative_path}: String concatenation (+=) inside loop detected. Use ''.join() instead for O(n) performance.")
            except:
                pass
        if f.extension == ".sql":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                if "CREATE TABLE" in content and "INDEX" not in content.upper():
                    bottlenecks.append(f"{f.relative_path}: Table created without any INDEX. Could cause slow queries at scale.")
            except:
                pass
                
    if bottlenecks:
        out = "[PERFORMANCE] 🏎️ Performance Anti-Patterns Detected:\n" + "\n".join([f"  - {b}" for b in bottlenecks])
        return out
    return "[PERFORMANCE] 🚀 No classic performance bottlenecks detected."

# 4. Legal / Compliance
def run_legal(files):
    risks = []
    for f in files:
        if f.filename == "requirements.txt":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                if "pyqt5" in content.lower() or "pyqt6" in content.lower():
                    risks.append("PyQt is GPL licensed! If you distribute this app, you must open-source your proprietary code.")
            except:
                pass
        if f.filename == "package.json":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                if "ghostscript" in content.lower():
                    risks.append("Ghostscript uses AGPL! Major legal risk for cloud apps.")
            except:
                pass
                
    if risks:
        return "[LEGAL] ⚖️ WARNING: Copyleft / Viral License Risks Detected!\n" + "\n".join([f"  - {r}" for r in risks])
    return "[LEGAL] 🛡️ No obvious GPL/AGPL dependencies found in requirements/package.json."

# 5. UML Generator
def run_uml(files, root_path):
    uml = ["classDiagram"]
    class_count = 0
    for f in files:
        if f.language == "Python":
            try:
                content = open(f.path, "r", encoding="utf-8", errors="ignore").read()
                # Match class Name(Parent):
                classes = re.findall(r'class\s+([a-zA-Z_0-9]+)(?:\((.*?)\))?:', content)
                for cls_name, parent in classes:
                    class_count += 1
                    uml.append(f"  class {cls_name}")
                    if parent and parent != "object":
                        # Handle multiple inheritance roughly
                        parents = [p.strip() for p in parent.split(",")]
                        for p in parents:
                            if p:
                                uml.append(f"  {p} <|-- {cls_name}")
            except:
                pass
                
    if class_count == 0:
        return "[UML] No Python classes found to map."
        
    with open(os.path.join(root_path, "classes.mmd"), "w", encoding="utf-8") as f:
        f.write("\n".join(uml))
        
    return f"[UML] 🗺️ Parsed {class_count} classes! UML Class Diagram saved to classes.mmd"
