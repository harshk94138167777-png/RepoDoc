"""
Repository schema generator using Python standard library only.
Generates JSON schema describing repository structure and metadata.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import datetime


def generate_schema(data: Any, output_path: str) -> bool:
    """
    Generate a JSON schema describing the repository structure.
    
    Args:
        data: ReportData object containing analysis results
        output_path: Path where the schema JSON file should be created
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build the schema
        schema = _build_schema(data)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        # Verify the file was written and contains valid JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            json.load(f)  # Validate JSON
        
        return True
    except Exception as e:
        print(f"Error generating schema: {e}")
        return False


def _build_schema(data: Any) -> Dict[str, Any]:
    """Build the complete schema dictionary."""
    
    # Collect file information
    files_by_type = {}
    files_by_dir = {}
    all_extensions = set()
    
    for file_info in data.files:
        # Group by language/type
        lang = file_info.language if file_info.language else "Unknown"
        if lang not in files_by_type:
            files_by_type[lang] = []
        files_by_type[lang].append({
            "path": file_info.path,
            "size": file_info.size,
            "lines": file_info.lines,
            "binary": file_info.is_binary
        })
        
        # Group by directory
        dir_path = str(Path(file_info.path).parent)
        if dir_path not in files_by_dir:
            files_by_dir[dir_path] = []
        files_by_dir[dir_path].append(Path(file_info.path).name)
        
        # Collect extensions
        ext = Path(file_info.path).suffix
        if ext:
            all_extensions.add(ext)
    
    # Build module relationships (for Python files)
    modules = _extract_python_modules(data.files)
    
    # Compute statistics
    total_files = len(data.files)
    total_size = sum(f.size for f in data.files)
    total_lines = sum(f.lines for f in data.files if not f.is_binary)
    binary_files = sum(1 for f in data.files if f.is_binary)
    
    schema = {
        "schema_version": "1.0",
        "generated_at": datetime.datetime.now().isoformat(),
        "repository": {
            "name": data.name,
            "path": data.path,
            "root_directory": os.path.abspath(data.path)
        },
        "statistics": {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_lines": total_lines,
            "binary_files": binary_files,
            "text_files": total_files - binary_files
        },
        "languages": {
            lang: len(files) for lang, files in files_by_type.items()
        },
        "file_extensions": sorted(list(all_extensions)),
        "directory_structure": {
            dir_path: {
                "file_count": len(files),
                "files": sorted(files)
            }
            for dir_path, files in sorted(files_by_dir.items())
        },
        "files_by_language": files_by_type,
        "modules": modules,
        "metadata": {
            "has_readme": bool(data.structure and data.structure.get('README') == 'PASS'),
            "has_tests": bool(data.structure and data.structure.get('Tests') == 'PASS'),
            "has_gitignore": bool(data.structure and data.structure.get('.gitignore') == 'PASS'),
            "has_license": bool(data.structure and data.structure.get('LICENSE') == 'PASS'),
            "is_git_repo": bool(data.git and (data.git.get('available') if isinstance(data.git, dict) else getattr(data.git, 'available', False))),
            "git_branch": data.git.get('branch') if isinstance(data.git, dict) and data.git.get('available') else (data.git.branch if hasattr(data.git, 'branch') and getattr(data.git, 'available', False) else None)
        }
    }
    
    return schema


def _extract_python_modules(files: List) -> Dict[str, Any]:
    """Extract Python module information."""
    modules = {}
    
    for file_info in files:
        if file_info.language != "Python":
            continue
        
        if file_info.path.endswith('.py'):
            module_name = Path(file_info.path).stem
            
            module_info = {
                "path": file_info.path,
                "functions": file_info.metrics.num_functions if file_info.metrics else 0,
                "classes": file_info.metrics.num_classes if file_info.metrics else 0,
                "lines": file_info.lines,
                "imports": []
            }
            
            # Extract imports if content is available
            try:
                with open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    imports = _extract_imports(content)
                    module_info["imports"] = imports
            except Exception:
                pass
            
            modules[module_name] = module_info
    
    return modules


def _extract_imports(content: str) -> List[str]:
    """Extract import statements from Python code."""
    imports = []
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Match "import x" or "from x import y"
        if line.startswith('import ') or line.startswith('from '):
            # Simple extraction (not perfect but good enough for schema)
            if line.startswith('import '):
                parts = line[7:].split(',')
                for part in parts:
                    module = part.strip().split()[0]
                    if module and not module.startswith('.'):
                        imports.append(module)
            elif line.startswith('from '):
                parts = line[5:].split('import')
                if parts:
                    module = parts[0].strip()
                    if module and not module.startswith('.'):
                        imports.append(module)
    
    return sorted(list(set(imports)))
