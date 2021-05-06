from abak_config.set import set_configuration_key
import click
from iterfzf import iterfzf
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
    '''
    Lists the projects available for the given client
    '''
    get_projects(client_id, query_text, output)

@click.command(name='select')
@click.option('--client-id', '-c', help="ID of the client to search for projects", default=lambda: environ.get('client_id', None))
@click.pass_context
def project_select(ctx, client_id):
    '''
    Selects the project to use as default
    '''
    projects_list = get_projects(client_id, "", 'python')
    if len(projects_list) > 1:
        selected_dirty = iterfzf([" - ".join([item.get('Id'), item.get('Display')]) for item in projects_list])
        selected = selected_dirty.split(' - ')[0]
    else:
        selected = projects_list[0].get('Id')
    set_configuration_key(selected, 'project_id')
    click.echo("project " + selected + " selected as default!")

def get_projects(client_id, query_text, output):
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
    elif output == 'json':
        print(json.dumps(projects.get('data')))
    elif output == 'python':
        return projects.get('data')

project.add_command(list_projects)
project.add_command(project_select)