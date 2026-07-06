import typer
from rich.console import Console
from rich.table import Table
from graphvuln.parsers.manifest_parser import find_manifests, parse_package_json
from graphvuln.scanner.osv_client import check_vulnerabilities

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
        console.print("❌ [bold red]No package.json files found.[/bold red]")
        raise typer.Exit(1)

    for manifest in manifests:
        parsed = parse_package_json(manifest)
        if "error" in parsed:
            continue
            
        console.print(f"📦 [bold green]Project:[/bold green] {parsed['project_name']} ({manifest})")
        
        # Create a beautiful terminal table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Package")
        table.add_column("Version")
        table.add_column("Status", justify="center")
        table.add_column("Vulnerabilities", justify="left")

        vulnerable_count = 0

        # Scan each dependency
        for pkg, ver in parsed['dependencies'].items():
            vulns = check_vulnerabilities(pkg, ver, parsed['ecosystem'])
            
            if vulns:
                vulnerable_count += 1
                vuln_ids = [v.get("aliases", [v.get("id")])[0] for v in vulns]
                vuln_str = ", ".join(vuln_ids[:3]) 
                if len(vuln_ids) > 3:
                    vuln_str += f" (+{len(vuln_ids)-3} more)"
                
                table.add_row(
                    f"[red]{pkg}[/red]", 
                    ver, 
                    "[bold red]VULNERABLE[/bold red]", 
                    f"[yellow]{vuln_str}[/yellow]"
                )
            else:
                table.add_row(pkg, ver, "[green]SAFE[/green]", "-")

        console.print(table)
        
        if vulnerable_count > 0:
            console.print(f"⚠️  [bold red]Found {vulnerable_count} vulnerable top-level packages.[/bold red]")
        else:
            console.print("✅ [bold green]All top-level dependencies are safe![/bold green]")

if __name__ == "__main__":
    app()