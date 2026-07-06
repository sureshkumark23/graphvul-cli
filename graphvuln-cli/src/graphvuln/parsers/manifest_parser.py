import os
import json

def find_manifests(directory: str) -> list:
    manifests = []
    for root, dirs, files in os.walk(directory):
        if 'node_modules' in dirs:
            dirs.remove('node_modules') 
            
        if 'package.json' in files:
            manifests.append(os.path.join(root, 'package.json'))
            
    return manifests

def parse_package_json(filepath: str) -> dict:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}
        
        return {
            "ecosystem": "npm",
            "filepath": filepath,
            "project_name": data.get("name", "Unknown Project"),
            "dependencies": all_deps
        }
    except json.JSONDecodeError:
        return {"error": f"Failed to parse JSON in {filepath}"}