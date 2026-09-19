"""
Heatmap generator using Python standard library only.
Generates HTML/SVG visualization of repository metrics.
"""

from pathlib import Path
from typing import List, Dict, Any
import html


def generate_heatmap(data: Any, output_path: str) -> bool:
    """
    Generate an HTML heatmap visualization of repository metrics.
    
    Args:
        data: ReportData object containing analysis results
        output_path: Path where the HTML file should be created
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Collect metrics for heatmap
        file_metrics = _collect_file_metrics(data.files)
        
        if not file_metrics:
            print("No suitable files for heatmap visualization")
            return False
        
        # Generate HTML content
        html_content = _generate_heatmap_html(data, file_metrics)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Verify the file exists and has content
        if not output_file.exists() or output_file.stat().st_size == 0:
            return False
        
        return True
        
    except Exception as e:
        print(f"Error generating heatmap: {e}")
        return False


def _collect_file_metrics(files: List) -> List[Dict[str, Any]]:
    """Collect metrics for heatmap visualization."""
    metrics = []
    
    for file_info in files:
        if file_info.is_binary:
            continue
        
        # Calculate a complexity score for the file
        complexity = 0
        
        if file_info.metrics:
            # Factor in various metrics
            complexity += file_info.lines // 10  # Lines contribute to complexity
            complexity += (file_info.metrics.num_functions or 0) * 2
            complexity += (file_info.metrics.num_classes or 0) * 5
            complexity += (file_info.metrics.max_nesting or 0) * 3
        else:
            complexity = file_info.lines // 10
        
        metrics.append({
            'path': file_info.path,
            'name': Path(file_info.path).name,
            'lines': file_info.lines,
            'complexity': complexity,
            'language': file_info.language or 'Unknown'
        })
    
    # Sort by complexity (descending)
    metrics.sort(key=lambda x: x['complexity'], reverse=True)
    
    # Limit to top 100 files for visualization
    return metrics[:100]


def _generate_heatmap_html(data: Any, file_metrics: List[Dict[str, Any]]) -> str:
    """Generate the HTML content for the heatmap."""
    
    # Find max complexity for scaling
    max_complexity = max(m['complexity'] for m in file_metrics) if file_metrics else 1
    
    # Generate grid cells
    cells_html = []
    for metric in file_metrics:
        intensity = metric['complexity'] / max_complexity if max_complexity > 0 else 0
        
        # Color gradient from green (low) to red (high)
        if intensity < 0.33:
            color = f"rgb({int(255 * intensity * 3)}, 200, 100)"
        elif intensity < 0.67:
            color = f"rgb(255, {int(200 - (intensity - 0.33) * 3 * 200)}, 100)"
        else:
            color = f"rgb(255, {int(100 - (intensity - 0.67) * 3 * 100)}, {int(100 - (intensity - 0.67) * 3 * 100)})"
        
        title = f"{metric['name']} - Lines: {metric['lines']}, Complexity: {metric['complexity']}"
        
        cells_html.append(f'''
        <div class="cell" style="background-color: {color};" title="{html.escape(title)}">
            <div class="cell-label">{html.escape(metric['name'][:20])}</div>
            <div class="cell-value">{metric['complexity']}</div>
        </div>
        ''')
    
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RepoDoctor Heatmap - {html.escape(data.name)}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            padding: 30px;
        }}
        
        h1 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }}
        
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        
        .info {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #667eea;
        }}
        
        .legend {{
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 30px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .legend-label {{
            font-weight: bold;
            color: #333;
        }}
        
        .legend-gradient {{
            flex: 1;
            height: 30px;
            background: linear-gradient(to right, 
                rgb(0, 200, 100), 
                rgb(255, 200, 100), 
                rgb(255, 100, 100), 
                rgb(255, 0, 0));
            border-radius: 4px;
            border: 1px solid #ddd;
        }}
        
        .legend-scale {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 20px;
        }}
        
        .cell {{
            aspect-ratio: 1;
            border-radius: 8px;
            padding: 10px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            border: 2px solid rgba(0,0,0,0.1);
        }}
        
        .cell:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            z-index: 10;
        }}
        
        .cell-label {{
            font-size: 11px;
            font-weight: bold;
            color: rgba(0,0,0,0.8);
            word-wrap: break-word;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .cell-value {{
            font-size: 20px;
            font-weight: bold;
            color: rgba(0,0,0,0.9);
            text-align: right;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Repository Complexity Heatmap</h1>
        <div class="subtitle">{html.escape(data.name)} - {html.escape(data.path)}</div>
        
        <div class="info">
            <strong>About this heatmap:</strong> This visualization shows file complexity based on multiple factors including 
            lines of code, number of functions/classes, and nesting depth. Warmer colors (red) indicate higher complexity.
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Files</div>
                <div class="stat-value">{len(data.files)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Files Visualized</div>
                <div class="stat-value">{len(file_metrics)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Max Complexity</div>
                <div class="stat-value">{max_complexity}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Health Score</div>
                <div class="stat-value">{data.score.score if data.score else 'N/A'}</div>
            </div>
        </div>
        
        <div class="legend">
            <span class="legend-label">Complexity:</span>
            <div style="flex: 1;">
                <div class="legend-gradient"></div>
                <div class="legend-scale">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                    <span>Very High</span>
                </div>
            </div>
        </div>
        
        <div class="grid">
            {''.join(cells_html)}
        </div>
        
        <div class="footer">
            Generated by RepoDoctor | Hover over cells to see details
        </div>
    </div>
</body>
</html>'''
    
    return html_template
