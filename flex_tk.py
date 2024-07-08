import click
from cli import configuration
from core.config import load_config
from core.schema import ContextKeys


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx: click.Context):
    """
    A versatile Python Command line offering utilities for file operations,
    media conversions, logging, cloud storage interactions, and more.
    """
    config_data = load_config()
    ctx.ensure_object(dict)
    ctx.obj[ContextKeys.config] = config_data


@cli.group()
def config():
    """Configuration for cli."""


config.add_command(configuration.set_password)
config.add_command(configuration.reset_password)
config.add_command(configuration.gcs)
config.add_command(configuration.bb2)
