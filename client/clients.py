from abak_config.remove import remove_configuration_key
from abak_config.set import set_configuration_key
import click
import json
from iterfzf import iterfzf
from tabulate import tabulate
from abak_shared_functions import get_config, httprequest

@click.group()
@click.pass_context
def client(ctx):
    '''
    Find clients to assign timesheet entries
    '''
    pass


@click.command(name='list')
@click.pass_context
@click.option('-o', '--output', help="The format of the output of this command", type=click.Choice(['json', 'table']), default='table')
@click.option('--query-text', '-q', help="Text to search for in the client name", default="")
def client_list(ctx, output, query_text):
    '''
    Lists the clients available
    '''
    get_clients(query_text, output)

@click.command(name='select')
@click.pass_context
def client_select(ctx):
    '''
    Selects the default client ID to use
    '''
    clients_list = get_clients("", 'python')
    if len(clients_list) > 1:
        selected_dirty = iterfzf([" - ".join([item.get('Id'), item.get('DisplayName')]) for item in clients_list])
        selected = selected_dirty.split(' - ')[0]
    else:
        selected = clients_list[0].get('Id')
    set_configuration_key(selected, 'client_id')
    remove_configuration_key('project_id')
    click.echo("Client " + selected + " selected as default!")

def get_clients(query_text, output):
    config = get_config()
    body = {
        "queryText": query_text,
        "start": 0,
        "limit": 22,
        "employeeId": config['user_id']
    }

    clients = httprequest('GET', body, "/Abak/Common/GetTimesheetClientsPaginated")

    if output == "table": 
        headers = ["Id", "DisplayName"]
        table = tabulate([[client[key]for key in client if key in headers]for client in clients.get('data')], headers=headers)
        print(table)
    elif output == 'json':
        print(json.dumps(clients.get('data')))
    elif output == 'python':
        return clients.get('data')


client.add_command(client_list)
client.add_command(client_select)