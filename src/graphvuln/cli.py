import typer
import warnings
import urllib3
import time
from rich.console import Console
from rich.table import Table
from graphvuln.parsers.manifest_parser import find_manifests, parse_manifest
from graphvuln.scanner.osv_client import check_vulnerabilities
from graphvuln.graph.resolver import build_dependency_graph, get_blast_radius
from graphvuln.fixer.auto_fixer import find_safe_version, apply_fixes

urllib3.disable_warnings()
warnings.filterwarnings("ignore", category=urllib3.exceptions.NotOpenSSLWarning)

app = typer.Typer(help="GraphVuln: Intelligent Dependency Scanner & Auto-Fixer")
console = Console()

@app.command()
def scan(
    directory: str = typer.Option(".", "--dir", "-d", help="Directory to scan"),
    fix: bool = typer.Option(False, "--fix", help="Automatically apply safe version updates")
):
    console.print(f"🔍 [bold blue]Scanning directory:[/bold blue] {directory}\n")
    manifests = find_manifests(directory)

    if not manifests:
        console.print("❌ [bold red]No manifest files (package.json or requirements.txt) found.[/bold red]")
        raise typer.Exit(1)

    for manifest in manifests:
        # ⏱️ Start the timer for this specific manifest
        start_time = time.perf_counter()
        
        parsed = parse_manifest(manifest)
        if "error" in parsed:
            continue
            
        eco = parsed['ecosystem']
        console.print(f"📦 [bold green]{eco} Project:[/bold green] {parsed['project_name']} ({manifest})")
        
        with console.status(f"[bold cyan]🕸️ Building {eco} dependency graph...", spinner="dots"):
            G = build_dependency_graph(parsed['project_name'], parsed['dependencies'], eco)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Package")
        table.add_column("Current")
        table.add_column("Status", justify="center")
        table.add_column("Blast Radius", justify="center")
        table.add_column("Fix Available?", justify="center")

        vulnerable_count = 0
        updates_needed = {}

        with console.status("[bold yellow]🛡️ Scanning OSV and calculating updates...", spinner="bouncingBar"):
            for pkg, ver in parsed['dependencies'].items():
                vulns = check_vulnerabilities(pkg, ver, eco)
                node_id = f"{pkg}@{ver.replace('^', '').replace('~', '')}"
                
                if vulns:
                    vulnerable_count += 1
                    radius = get_blast_radius(G, node_id)
                    radius_str = f"[bold red]{radius} affected[/bold red]" if radius > 0 else "0"
                    
                    safe_ver = find_safe_version(pkg, ver, eco)
                    if safe_ver:
                        fix_str = f"[bold green]Yes -> {safe_ver}[/bold green]"
                        if fix: updates_needed[pkg] = safe_ver
                    else:
                        fix_str = "[dim red]No safe update[/dim red]"
                    
                    table.add_row(f"[red]{pkg}[/red]", ver, "[bold red]VULNERABLE[/bold red]", radius_str, fix_str)
                else:
                    table.add_row(pkg, ver, "[green]SAFE[/green]", "-", "-")

        console.print(table)
        
        if vulnerable_count > 0:
            console.print(f"⚠️  [bold red]Found {vulnerable_count} vulnerable top-level packages.[/bold red]")
            if fix and updates_needed:
                console.print(f"\n🔧 [bold yellow]Applying safe updates to {manifest}...[/bold yellow]")
                success = apply_fixes(manifest, updates_needed, eco)
                if success:
                    console.print(f"✅ [bold green]Successfully updated {len(updates_needed)} packages![/bold green]")
                    console.print(f"💡 Run [bold cyan]`{'pip install -r requirements.txt' if eco == 'PyPI' else 'npm install'}`[/bold cyan] to sync.")
                else:
                    console.print("❌ [bold red]Failed to write updates to file.[/bold red]")
            elif not fix:
                console.print("ℹ️  [dim]Run with --fix to automatically apply available updates.[/dim]")
        else:
            console.print("✅ [bold green]All top-level dependencies are safe![/bold green]")

        # ⏱️ Stop the timer and calculate elapsed time
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        console.print(f"⏱️  [dim italic]Scan completed in {elapsed_time:.2f} seconds[/dim italic]\n")

if __name__ == "__main__":
    app()
