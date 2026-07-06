import os
import json
import re

def find_manifests(directory: str) -> list:
    manifests = []
    for root, dirs, files in os.walk(directory):
        if 'node_modules' in dirs: dirs.remove('node_modules')
        if 'venv' in dirs: dirs.remove('venv')
        if '.git' in dirs: dirs.remove('.git')
            
        if 'package.json' in files:
            manifests.append(os.path.join(root, 'package.json'))
        if 'requirements.txt' in files:
            manifests.append(os.path.join(root, 'requirements.txt'))
            
    return manifests

def parse_manifest(filepath: str) -> dict:
    if filepath.endswith('package.json'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            return {
                "ecosystem": "npm",
                "filepath": filepath,
                "project_name": data.get("name", "Unknown Node Project"),
                "dependencies": deps
            }
        except json.JSONDecodeError:
            return {"error": f"Failed to parse JSON in {filepath}"}
            
    elif filepath.endswith('requirements.txt'):
        deps = {}
        project_name = os.path.basename(os.path.dirname(filepath)) or "Python Project"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Split by version specifiers (==, >=, etc)
                        parts = re.split(r'[=<>~]+', line)
                        pkg_name = parts[0].strip()
                        ver = parts[1].strip() if len(parts) > 1 else "*"
                        if pkg_name:
                            deps[pkg_name] = ver
            return {
                "ecosystem": "PyPI",
                "filepath": filepath,
                "project_name": project_name,
                "dependencies": deps
            }
        except Exception as e:
            return {"error": f"Failed to parse {filepath}: {e}"}
