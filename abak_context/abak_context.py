import click
import yaml
import json
from tabulate import tabulate
from abak_config import set_configuration_key
from abak_shared_functions import get_clean_config, Sorry
from pyfzf import FzfPrompt
from os import environ

headers = ['Project', 'Client', 'Price']

@click.group()
def context():
    """
    Context operations for Abak. Select which project id and client id to use for the commands.
    """
    pass

@click.command(name='list')
@click.option('--output', '-o', help="Type of output to show the contexts", type=click.Choice(['table', 'json', 'yaml', 'yml']), default='table')
def context_list(output):
    '''
    Lists the available contexts
    '''
    contexts = get_contexts()
    if len(contexts) == 0:
        raise Sorry("there are no contexts created")
    if output == 'table':
        rows = [[context]+[contexts[context].get(header, 0)for header in headers]for context in contexts]
        click.echo(tabulate(rows, headers=['Context'] + headers))
    elif output in ['yaml', 'yml']:
        click.echo(yaml.dump(contexts))
    elif output == 'json':
        click.echo(json.dumps(contexts))

    click.echo()
    pass

@click.command(name='show')
@click.option('--name', '-n', help="Name of the context to show")
def context_show(name):
    '''
    shows the current context or the selected context.
    '''
    clean_config = get_clean_config()
    if not name:
        name = clean_config.get("current_context", None)
    
    if not name:
        raise Sorry('there are no contexts selected')

    contexts = clean_config.get('contexts', {})

    click.echo(f'{name}: {contexts.get(name, {})}')
    pass

@click.command(name='set')
@click.option('--name', '-n', help="Name of the context to be created")
@click.option('--client-id', '-c', help="ID of the client to be used in this context")
@click.option('--project-id', '-p', help="ID of the project to be used in this context")
@click.option('--price', '-r', help="ID of the project to be used in this context", default='0')
def context_set(name, client_id, project_id, price):
    '''
    Creates a new context
    '''
    contexts = get_contexts()
    contexts[name] = {'Project': project_id, 
                      'Client': client_id,
                      'Price': float(price)}
    set_configuration_key(contexts, 'contexts')
    pass

@click.command(name='select')
@click.option('--name', '-n', help='Name of the context to select')
def context_select(name):
    '''
    Selects a context
    '''
    contexts = get_contexts()
    if not name:
        fzf = FzfPrompt()
        selected_context = fzf.prompt([context for context in contexts], fzf_options="+m")
    else:
        if name not in contexts.keys():
            raise Sorry(f'context {name} does not exist')
        else:
            selected_context = name

    if selected_context:
        if isinstance(selected_context, list):
            set_configuration_key(selected_context[0], 'current_context')
        else:
            set_configuration_key(selected_context, 'current_context')
    pass

@click.command(name='remove')
@click.option('--name', '-n', help='Name of the context to be selected', required=True, prompt=True)
def context_remove(name):
    '''
    Removes a context
    '''
    config = get_clean_config()
    if name in config.get('contexts',{}).keys():
        del config['contexts'][name]
    set_configuration_key(config['contexts'], 'contexts')
    if 'current_context' in config.keys():
        if config.get('current_context') == name:
            set_configuration_key(None, 'current_context')

@click.group(name="price")
@click.pass_context
def context_price(ctx):
    '''
    Command group for managing Prices for Contexts
    '''
    pass

@click.command(name='set')
@click.option('--context', '-c', help="Context to set the price of the hour", default=lambda: environ.get('current_context', None))
@click.option('--price', help="Price of the hour in CAD", prompt="Price of the hour", required=True)
@click.pass_context
def context_price_set(ctx, context, price):
    '''
    Sets the price of the hour in a context
    '''
    if not context:
        raise Sorry(f"context cannot be empty")

    contexts = get_contexts()
    selected_context = contexts.get(context, None)

    if not selected_context:
        raise Sorry(f"context {context} not found")
    
    try:
        selected_context['Price'] = float(price)
    except:
        raise Sorry(f"can't convert {price} to a float number")

    contexts[context] = selected_context
    print(contexts)
    set_configuration_key(contexts, 'contexts')




@click.command(name='current')
def context_current():
    '''
    Shows the current context selected
    '''
    click.echo(f'current_context: {get_clean_config().get("current_context", None)}')

def get_contexts():
    return get_clean_config().get('contexts', {})


context_price.add_command(context_price_set)

context.add_command(context_list)
context.add_command(context_show)
context.add_command(context_set)
context.add_command(context_current)
context.add_command(context_select)
context.add_command(context_remove)
context.add_command(context_price)