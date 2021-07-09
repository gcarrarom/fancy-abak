import click
import yaml
import json
from tabulate import tabulate
from abak_config import set_configuration_key
from abak_shared_functions import get_clean_config, Sorry
from iterfzf import iterfzf

headers = ['Project', 'Client']

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
        rows = [[context]+[contexts[context][header]for header in headers]for context in contexts]
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
def context_set(name, client_id, project_id):
    '''
    Creates a new context
    '''
    contexts = get_contexts()
    contexts[name] = {'Project': project_id, 
                      'Client': client_id}
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
        selected_context = iterfzf([context for context in contexts])
    else:
        if name not in contexts.keys():
            raise Sorry(f'context {name} does not exist')
        else:
            selected_context = name

    if selected_context:
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


@click.command(name='current')
def context_current():
    '''
    Shows the current context selected
    '''
    click.echo(f'current_context: {get_clean_config().get("current_context", None)}')

def get_contexts():
    return get_clean_config().get('contexts', {})

context.add_command(context_list)
context.add_command(context_show)
context.add_command(context_set)
context.add_command(context_current)
context.add_command(context_select)
context.add_command(context_remove)