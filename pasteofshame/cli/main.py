"""Main CLI entrypoint."""

import json
import sys

import click

from pasteofshame.app.config import Config
from pasteofshame.app.daemon import Daemon
from pasteofshame.core.detector import Detector
from pasteofshame.core.rules import RulePack
from pasteofshame.core.scoring import ScoringEngine
from pasteofshame.notify.notifier import Notifier


@click.group()
@click.version_option(version="0.1.0", prog_name="paste-of-shame")
def main() -> None:
    """Paste of Shame - Clipboard watchdog for detecting LLM boilerplate."""
    pass


@main.command()
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.option("--threshold", type=int, help="Score threshold for warnings")
@click.option("--no-notify", is_flag=True, help="Disable desktop notifications")
def watch(config: str | None, threshold: int | None, no_notify: bool) -> None:
    """Start watching the clipboard for LLM boilerplate."""
    # Load config
    cfg = Config.load(config)

    # Override with CLI options
    if threshold is not None:
        cfg.threshold = threshold
    if no_notify:
        cfg.notify_enabled = False

    # Start daemon
    daemon = Daemon(cfg)
    daemon.start()


@main.command()
@click.argument("text", required=False)
@click.option("--config", type=click.Path(exists=True), help="Path to config file")
@click.option("--threshold", type=int, help="Score threshold for warnings")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.option("--rulepack", type=click.Path(exists=True), help="Path to custom rulepack YAML")
def scan(text: str | None, config: str | None, threshold: int | None, output_json: bool, rulepack: str | None) -> None:
    """Scan text for LLM boilerplate (from argument or stdin)."""
    # Get text from argument or stdin
    if text is None:
        if sys.stdin.isatty():
            click.echo("Error: No text provided. Use argument or pipe via stdin.", err=True)
            sys.exit(1)
        text = sys.stdin.read()

    # Load config
    cfg = Config.load(config)
    if threshold is not None:
        cfg.threshold = threshold

    # Load rule pack
    rule_pack = RulePack.from_yaml(rulepack) if rulepack else RulePack.builtin()

    rule_pack = rule_pack.filter_by_language(cfg.enabled_languages)

    # Create detector
    scoring_engine = ScoringEngine(
        threshold=cfg.threshold,
        allowlist_patterns=cfg.allowlist_patterns,
    )
    detector = Detector(rule_pack=rule_pack, scoring_engine=scoring_engine)

    # Scan
    result = detector.scan(text)

    # Output
    if output_json:
        notifier = Notifier(desktop_enabled=False, verbose=False)
        output = notifier.format_json(result)
        click.echo(json.dumps(output, indent=2))
    else:
        if result.is_warning:
            notifier = Notifier(desktop_enabled=False, verbose=True)
            notifier.notify(result)
            sys.exit(1)
        else:
            click.echo("✓ No significant LLM boilerplate detected")


@main.command()
@click.option("--rulepack", type=click.Path(exists=True), help="Path to custom rulepack YAML")
@click.option("--validate", is_flag=True, help="Validate a rulepack file")
@click.option("--test", "test_text", help="Test rules against provided text")
def rules(rulepack: str | None, validate: bool, test_text: str | None) -> None:
    """List, validate, or test detection rules."""
    if validate and not rulepack:
        click.echo("Error: --validate requires --rulepack", err=True)
        sys.exit(1)

    # Load rule pack
    try:
        if rulepack:
            rule_pack = RulePack.from_yaml(rulepack)
            click.echo(f"✓ Successfully loaded {len(rule_pack)} rules from {rulepack}")
        else:
            rule_pack = RulePack.builtin()
            click.echo(f"Built-in ruleset ({len(rule_pack)} rules):\n")

        if not validate:
            # List rules
            for rule in rule_pack.rules:
                click.echo(f"  [{rule.id}] {rule.description}")
                click.echo(f"    Pattern: {rule.pattern}")
                click.echo(f"    Type: {rule.rule_type.value}, Weight: {rule.weight}, Severity: {rule.severity.value}")
                click.echo()

        if test_text:
            # Test rules against text
            detector = Detector(rule_pack=rule_pack)
            result = detector.scan(test_text)
            click.echo("\nTest Results:")
            click.echo(f"  Total Score: {result.total_score}")
            click.echo(f"  Warning: {result.is_warning}")
            click.echo(f"  Matches: {len(result.matches)}")
            for match in result.matches:
                click.echo(f"    - {match.rule.id}: {match.rule.description}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
def config() -> None:
    """Show config file location and current settings."""
    config_path = Config.get_config_path()
    click.echo(f"Config file: {config_path}")

    if config_path.exists():
        cfg = Config.load()
        click.echo("\nCurrent settings:")
        click.echo(f"  Threshold: {cfg.threshold}")
        click.echo(f"  Enabled languages: {', '.join(cfg.enabled_languages)}")
        click.echo(f"  Desktop notifications: {cfg.notify_enabled}")
        click.echo(f"  Poll interval: {cfg.poll_interval}s")
        click.echo(f"  Cooldown: {cfg.cooldown_seconds}s")
        click.echo(f"  Max clipboard size: {cfg.max_clipboard_size} chars")
        if cfg.allowlist_patterns:
            click.echo(f"  Allowlist patterns: {len(cfg.allowlist_patterns)}")
    else:
        click.echo("\n(Config file does not exist - using defaults)")
        click.echo("\nTo create a config file, run:")
        click.echo(f"  mkdir -p {config_path.parent}")
        click.echo(f"  cat > {config_path} << 'EOF'")
        click.echo("threshold: 20")
        click.echo("enabled_languages: [en]")
        click.echo("notify_enabled: true")
        click.echo("poll_interval: 0.3")
        click.echo("cooldown_seconds: 5.0")
        click.echo("EOF")


if __name__ == "__main__":
    main()
