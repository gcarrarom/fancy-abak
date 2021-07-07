import click
import json
import yaml
from abak_shared_functions import get_clean_config

@click.command(name="show")
@click.option('-o', '--output', help="Type of output of the configuration", default='json', type=click.Choice(['json', 'yaml']))
@click.argument('key', required=False)
@click.pass_context
def show_config(ctx, key, output):
    '''
    Shows the current configuration file for JIRA communication and default values

    Args:
        key (str): the key to show
    '''
    configuration = get_clean_config()
    if not key:
        if output == 'json':
            click.echo(json.dumps(configuration))
        elif output == 'yaml':
            click.echo(yaml.dump(configuration))
    elif configuration.get(key):
        click.echo(configuration[key])
