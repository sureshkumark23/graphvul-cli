import json
import requests
import re
from graphvuln.scanner.osv_client import check_vulnerabilities

def get_latest_version(package_name: str, ecosystem: str) -> str:
    try:
        if ecosystem == "npm":
            resp = requests.get(f"https://registry.npmjs.org/{package_name}", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("dist-tags", {}).get("latest")
        elif ecosystem == "PyPI":
            resp = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("info", {}).get("version")
    except:
        pass
    return None

def find_safe_version(package_name: str, current_version: str, ecosystem: str) -> str:
    latest = get_latest_version(package_name, ecosystem)
    clean_current = current_version.replace("^", "").replace("~", "")
    
    if not latest or latest == clean_current:
        return None 
        
    vulns = check_vulnerabilities(package_name, latest, ecosystem)
    if not vulns:
        return latest
    return None

def apply_fixes(filepath: str, updates: dict, ecosystem: str) -> bool:
    try:
        if ecosystem == "npm":
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for pkg, new_ver in updates.items():
                if "dependencies" in data and pkg in data["dependencies"]:
                    data["dependencies"][pkg] = f"^{new_ver}"
                elif "devDependencies" in data and pkg in data["devDependencies"]:
                    data["devDependencies"][pkg] = f"^{new_ver}"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
            
        elif ecosystem == "PyPI":
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            with open(filepath, 'w', encoding='utf-8') as f:
                for line in lines:
                    pkg_match = re.split(r'[=<>~]+', line.strip())[0].strip()
                    if pkg_match in updates:
                        f.write(f"{pkg_match}=={updates[pkg_match]}\n")
                    else:
                        f.write(line)
            return True
    except Exception:
        pass
    return False
