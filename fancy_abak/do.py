import click

from fancy_abak.abak_shared_functions import (
    fancy_abak_request,
)


@click.command()
@click.pass_context
@click.argument("prompt")
def do(ctx, prompt):
    """
    GPT Powered command to "do" something
    """

    result = fancy_abak_request("POST", {"message": prompt}, "/chat", True)

    click.echo(result["message"])
