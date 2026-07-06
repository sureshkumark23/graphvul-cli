import requests

OSV_QUERY_URL = "https://api.osv.dev/v1/query"

def check_vulnerabilities(package_name: str, version: str, ecosystem: str = "npm") -> list:
    clean_version = version.replace("^", "").replace("~", "")
    payload = {
        "version": clean_version,
        "package": {"name": package_name, "ecosystem": "npm" if ecosystem == "npm" else "PyPI"}
    }
    try:
        response = requests.post(OSV_QUERY_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json().get("vulns", [])
    except requests.exceptions.RequestException:
        return []