import asyncio
import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .orchestrator import ReconOrchestrator
from .models import IntelligenceReport

console = Console()


def print_risk_banner(report: IntelligenceReport):
    score = report.risk_score
    color = "green" if score < 30 else ("yellow" if score < 70 else "red")
    text = f"[bold {color}]EXPOSURE & RISK SCORE: {score}/100[/bold {color}]\n"
    if report.risk_factors:
        text += "\n[bold]Identified Vectors:[/bold]\n"
        for factor in report.risk_factors:
            text += f" • [{color}]{factor}[/{color}]\n"
    console.print(Panel(text, title=f"Intelligence Audit: {report.target}", border_style=color))


@click.group()
def main():
    """Value-Enhancer: Unified OSINT & Digital Reconnaissance Suite."""
    pass


@main.command()
@click.argument("username")
@click.option("--json-out", is_flag=True, help="Output raw JSON instead of tables")
def identity(username: str, json_out: bool):
    """Scan digital footprint & discover public accounts matching USERNAME."""
    orchestrator = ReconOrchestrator()
    with console.status(f"[cyan]Scanning digital footprint for '[bold]{username}[/bold]' across platforms..."):
        report = asyncio.run(orchestrator.scan_username(username))

    if json_out:
        click.echo(report.model_dump_json(indent=2))
        return

    print_risk_banner(report)

    table = Table(title=f"Discovered Profiles for '{username}'", border_style="cyan")
    table.add_column("Platform", style="bold white")
    table.add_column("Category", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Profile URL", style="blue")
    table.add_column("Latency (ms)", justify="right")

    for item in report.identity_results:
        status_str = "[bold green]FOUND[/bold green]" if item.exists else "[dim red]NOT FOUND[/dim red]"
        table.add_row(
            item.platform,
            item.category,
            status_str,
            item.url if item.exists else "-",
            str(item.response_time_ms),
        )

    console.print(table)


@main.command()
@click.argument("phone_number")
@click.option("--json-out", is_flag=True, help="Output raw JSON instead of tables")
def phone(phone_number: str, json_out: bool):
    """Analyze carrier, line type, country, and OSINT footprint of PHONE_NUMBER."""
    orchestrator = ReconOrchestrator()
    with console.status(f"[cyan]Analyzing carrier & line type for '[bold]{phone_number}[/bold]'..."):
        report = orchestrator.scan_phone(phone_number)

    if json_out:
        click.echo(report.model_dump_json(indent=2))
        return

    print_risk_banner(report)
    res = report.phone_results
    if not res or not res.valid:
        console.print(f"[bold red]Invalid or unparseable phone number input: {phone_number}[/bold red]")
        return

    table = Table(title="Carrier & Geo Intelligence", border_style="cyan")
    table.add_column("Property", style="bold white")
    table.add_column("Value", style="cyan")

    table.add_row("E.164 Format", res.e164 or "-")
    table.add_row("International", res.international or "-")
    table.add_row("National", res.national or "-")
    table.add_row("Country / Region", f"{res.location or ''} ({res.region_code})")
    table.add_row("Carrier", res.carrier or "Unknown / Ported")
    table.add_row("Line Type", res.line_type or "Unknown")
    table.add_row("Timezone", res.timezone or "-")

    console.print(table)

    if res.google_dorks:
        console.print("\n[bold yellow]Targeted OSINT Dork Links:[/bold yellow]")
        for link in res.google_dorks[:4]:
            console.print(f" • [link={link}]{link}[/link]")


@main.command()
@click.argument("domain")
@click.option("--json-out", is_flag=True, help="Output raw JSON instead of tables")
def domain(domain: str, json_out: bool):
    """Enumerate DNS, subdomains, and audit email spoofing vulnerability."""
    orchestrator = ReconOrchestrator()
    with console.status(f"[cyan]Mapping DNS and subdomains for '[bold]{domain}[/bold]'..."):
        report = asyncio.run(orchestrator.scan_domain(domain))

    if json_out:
        click.echo(report.model_dump_json(indent=2))
        return

    print_risk_banner(report)
    res = report.domain_results
    if not res:
        return

    table = Table(title=f"DNS & Infrastructure: {domain}", border_style="cyan")
    table.add_column("Record Type", style="bold white")
    table.add_column("Entries", style="cyan")

    table.add_row("A (IPv4)", ", ".join(res.ip_addresses) or "None")
    table.add_row("AAAA (IPv6)", ", ".join(res.ipv6_addresses) or "None")
    table.add_row("MX Records", ", ".join(res.mx_records) or "None")
    table.add_row("Name Servers", ", ".join(res.name_servers) or "None")
    table.add_row("SPF Policy", res.spf_record or "[red]MISSING[/red]")
    table.add_row("DMARC Policy", res.dmarc_record or "[red]MISSING[/red]")
    table.add_row(
        "Spoofing Protection",
        "[bold red]VULNERABLE (Spoofable)[/bold red]" if res.email_spoofable else "[bold green]SECURED[/bold green]"
    )

    console.print(table)

    if res.discovered_subdomains:
        sub_table = Table(title="Discovered Subdomains", border_style="magenta")
        sub_table.add_column("FQDN", style="white")
        for sub in res.discovered_subdomains:
            sub_table.add_row(sub)
        console.print(sub_table)


@main.command()
@click.argument("path")
@click.option("--json-out", is_flag=True, help="Output raw JSON instead of tables")
def secrets(path: str, json_out: bool):
    """Audit codebase or files for leaked credentials, API keys, and high-entropy secrets."""
    orchestrator = ReconOrchestrator()
    with console.status(f"[cyan]Scanning codebase '[bold]{path}[/bold]' for leaked secrets..."):
        report = orchestrator.scan_secrets(path)

    if json_out:
        click.echo(report.model_dump_json(indent=2))
        return

    print_risk_banner(report)

    if not report.secret_results:
        console.print("[bold green]Clean: No unencrypted credentials or high-entropy tokens detected.[/bold green]")
        return

    table = Table(title=f"Discovered Leaked Credentials ({len(report.secret_results)})", border_style="red")
    table.add_column("File", style="bold white")
    table.add_column("Line", justify="right")
    table.add_column("Rule", style="yellow")
    table.add_column("Snippet (Masked)", style="cyan")
    table.add_column("Severity", style="bold")

    for f in report.secret_results:
        sev_color = "red" if f.severity.value == "CRITICAL" else ("yellow" if f.severity.value == "HIGH" else "white")
        table.add_row(
            f.file_path,
            str(f.line_number),
            f.description,
            f.matched_snippet,
            f"[{sev_color}]{f.severity.value}[/{sev_color}]"
        )
    console.print(table)


@main.command()
@click.argument("image_path")
@click.option("--json-out", is_flag=True, help="Output raw JSON instead of tables")
def metadata(image_path: str, json_out: bool):
    """Extract EXIF metadata, camera device fingerprints, and GPS geolocation coordinates."""
    orchestrator = ReconOrchestrator()
    report = orchestrator.scan_metadata(image_path)

    if json_out:
        click.echo(report.model_dump_json(indent=2))
        return

    print_risk_banner(report)
    f = report.metadata_results[0]
    if not f.has_exif:
        console.print("[yellow]No EXIF metadata found in image (stripped or non-photographic).[/yellow]")
        return

    table = Table(title=f"Image Metadata & GPS Analysis: {f.filename}", border_style="cyan")
    table.add_column("Field", style="bold white")
    table.add_column("Details", style="cyan")

    table.add_row("Device Make/Model", f"{f.make or 'Unknown'} {f.model or ''}".strip())
    table.add_row("Software/OS", f.software or "Unknown")
    table.add_row("Capture Timestamp", f.datetime_original or "Unknown")
    if f.latitude and f.longitude:
        table.add_row("GPS Coordinates", f"{f.latitude}, {f.longitude}")
        table.add_row("Altitude", f"{f.altitude} meters" if f.altitude else "Unknown")
        table.add_row("Google Maps Link", f"[link={f.maps_link}]{f.maps_link}[/link]")
    else:
        table.add_row("GPS Coordinates", "[dim]No GPS coordinates embedded[/dim]")

    console.print(table)


@main.command()
@click.option("--host", default="127.0.0.1", help="Host interface")
@click.option("--port", default=8000, help="Port to serve dashboard on")
def web(host: str, port: int):
    """Launch the local web dashboard."""
    import uvicorn
    console.print(f"[bold cyan]Launching Value-Enhancer Local Intelligence Dashboard at http://{host}:{port}...[/bold cyan]")
    uvicorn.run("value_enhancer.web.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
