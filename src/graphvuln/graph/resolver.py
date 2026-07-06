import requests
import networkx as nx

def build_dependency_graph(project_name: str, top_level_deps: dict, ecosystem: str = "npm") -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_node(project_name, type="root")

    for pkg, ver in top_level_deps.items():
        clean_ver = ver.replace("^", "").replace("~", "")
        pkg_id = f"{pkg}@{clean_ver}"
        G.add_edge(project_name, pkg_id)

        try:
            if ecosystem == "npm":
                url = f"https://registry.npmjs.org/{pkg}/{clean_ver}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    for sub_pkg, sub_ver in resp.json().get("dependencies", {}).items():
                        sub_id = f"{sub_pkg}@{sub_ver.replace('^', '').replace('~', '')}"
                        G.add_edge(pkg_id, sub_id)
                        
            elif ecosystem == "PyPI":
                url = f"https://pypi.org/pypi/{pkg}/{clean_ver}/json" if clean_ver != "*" else f"https://pypi.org/pypi/{pkg}/json"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    requires = resp.json().get("info", {}).get("requires_dist") or []
                    for req in requires:
                        # PyPI format: "requests (>=2.0)" -> we just grab "requests"
                        sub_pkg = req.split(' ')[0].strip()
                        G.add_edge(pkg_id, f"{sub_pkg}@*")
        except Exception:
            pass
            
    return G

def get_blast_radius(G: nx.DiGraph, node_id: str) -> int:
    if node_id not in G:
        return 0
    return len(nx.ancestors(G, node_id))
