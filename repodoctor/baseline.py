import json
import os
from typing import Dict, Optional
from .models import ReportData

def compare_baseline(current_data: ReportData, baseline_path: str) -> Optional[Dict[str, int]]:
    if not os.path.exists(baseline_path):
        return None
        
    try:
        with open(baseline_path, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
            
        deltas = {}
        
        # Current values
        c_score = current_data.score.score if current_data.score else 0
        c_files = len(current_data.files)
        c_lines = sum(f.lines for f in current_data.files)
        c_todos = len(current_data.todos)
        c_dups = len(current_data.duplicates)
        c_secrets = len(current_data.security)
        
        # Baseline values
        b_score = baseline.get("summary", {}).get("health_score", 0)
        b_files = baseline.get("summary", {}).get("files", 0)
        b_lines = baseline.get("summary", {}).get("lines", 0)
        b_todos = baseline.get("maintainability", {}).get("todos", 0)
        b_dups = baseline.get("maintainability", {}).get("duplicates", 0)
        b_secrets = baseline.get("security", {}).get("potential_secrets", 0)
        
        deltas["score"] = c_score - (b_score or 0)
        deltas["files"] = c_files - b_files
        deltas["lines"] = c_lines - b_lines
        deltas["todos"] = c_todos - b_todos
        deltas["duplicates"] = c_dups - b_dups
        deltas["secrets"] = c_secrets - b_secrets
        
        return deltas
        
    except Exception:
        return None
