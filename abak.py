import webbrowser
import click
import requests
import timesheets
import client
import project
import abak_config
import os


from abak_shared_functions import write_config_file, get_config

@click.group()
@click.pass_context
def abak(ctx):
    config = get_config()
    if ctx.invoked_subcommand not in ['login', 'config']:
        try:
            headers = {
                'Cookie': config['token']
            }        
            result = requests.get(config.get('endpoint') + "/Abak/Transact/GetEmployee_Optimized", headers = headers)
            config['user_id'] = result.json()['data'][0]['Id']
            write_config_file(config['config_file_path'], config)
            [os.environ.setdefault(key, config[key]) for key in config if key not in ['app_dir', 'config_file_path', 'authenticated', 'headers', 'token']]
        except Exception:
            print('Please login first!')
            exit(10)

@click.command()
@click.option('-u', '--username', help="the username to use for login", required=True, prompt=True)
@click.option('-p', '--password', help="the password to use for login", required=True, prompt=True, hide_input=True)
@click.option('-e', '--endpoint', help="The endpoint where abak is hosted", required=True, prompt=True)
def login(username, password, endpoint):
    config = get_config()
    body = {
        'username': username,
        'password': password,
        'device': 'W'
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    result = requests.post(endpoint + '/Abak/Account/Authenticate', data=body, headers=headers)
    result.raise_for_status()
    if result.headers['Set-Cookie'].find('AbakUsername') > 0:
        config["token"] = result.headers['Set-Cookie']
        config['endpoint'] = endpoint
        write_config_file(config['config_file_path'], config)
        print("Login successful!")
    else:
        print(result.json()['errorMessage'])
        exit(10)

@click.command(name='open')
def open_browser():
    config = get_config()
    webbrowser.open(config['endpoint'])


abak.add_command(login)
abak.add_command(open_browser)

abak.add_command(timesheets.timesheet)
abak.add_command(client.client)
abak.add_command(project.project)
abak.add_command(abak_config.config)