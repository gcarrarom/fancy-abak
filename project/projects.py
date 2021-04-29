import click
from tabulate import tabulate
import json
import requests
from abak_shared_functions import get_config, option_not_none
from os import environ


@click.group()
@click.pass_context
def project(ctx):
    '''
    Find projects to assign timesheet entries
    '''
    pass

@click.command(name='list')
@click.option('-o', '--output', help="The format of the output of this command", type=click.Choice(['json', 'table']), default='table')
@click.option('--client-id', '-c', help="ID of the client to search for projects.", default=lambda: environ.get('client_id', None))
@click.option('--query-text', '-q', help="Text to search for in the project name", default="")
@click.pass_context
def list_projects(ctx, output, client_id, query_text):
    option_not_none('client id', client_id)
    config = get_config()
    url = config['endpoint'] + "/Abak/Common/GetTimesheetProjectsForPaginatedCombo"
    headers = {
        "Cookie": config['token']
    }
    body = {
        "clientId": client_id,
        "isInModif": "false",
        "queryText": query_text,
        "start": 0,
        "limit": 22,
        "employeeId": config['user_id']
    }

    result = requests.get(url, headers=headers, data=body)
    result.raise_for_status()

    projects = result.json()

    if output == "table": 
        headers = ["Id", "Display"]
        table = tabulate([[project[key]for key in project if key in headers]for project in projects.get('data')], headers=headers)
        print(table)
    else:
        print(json.dumps(projects.get('data')))

project.add_command(list_projects)