import click
import requests
import json
from tabulate import tabulate
from abak_shared_functions import get_config

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
    config = get_config()
    url = config['endpoint'] + "/Abak/Common/GetTimesheetClientsPaginated"
    headers = {
        "Cookie": config['token']
    }
    body = {
        "queryText": query_text,
        "start": 0,
        "limit": 22,
        "employeeId": config['user_id']
    }

    result = requests.get(url, headers=headers, data=body)
    result.raise_for_status()

    clients = result.json()

    if output == "table": 
        headers = ["Id", "DisplayName"]
        table = tabulate([[client[key]for key in client if key in headers]for client in clients.get('data')], headers=headers)
        print(table)
    else:
        print(json.dumps(clients.get('data')))


client.add_command(client_list)