import click
import os
import json
import requests

def get_headers(config):
    return {}

def get_config():
    app_name = '.abakctl'
    config_file = 'config.json'
    app_dir = click.get_app_dir(app_name)
    config_file_path = os.path.join(app_dir, config_file)
    config = read_configfile(config_file_path)
    config['authenticated'] = True
    config['headers'] = get_headers(config)
    config['app_dir'] = app_dir
    config['config_file_path'] = config_file_path
    return config

def read_configfile(config_file_path: str) -> dict:
    '''
    This function reads the contents of the config file for jiractl and dumps it as a dict for later use

    Args:
        config_file_path (string): path of the config file

    Returns:
        dict: dictionary with the configuration to run jiractl
    '''
    if not os.path.isfile(config_file_path):
        create_default_configfile()
    with open(config_file_path, 'r') as file_reader:
        config_dict = json.loads(file_reader.read())
    return config_dict

def create_default_configfile():

    app_name = '.abakctl'
    config_file = 'config.json'
    app_dir = click.get_app_dir(app_name)
    dir_split = app_dir.split('/')
    for i in range(2, len(dir_split)+1, 1):
        current_path = "/".join(dir_split[:i])
        print(current_path)
        if not os.path.isdir(current_path):
                os.mkdir(current_path)
    config = {}
    write_config_file(os.path.join(app_dir, config_file), config)

def write_config_file(file_path, data):
    if data.get('headers'): del data['headers']
    if data.get('app_dir'): del data['app_dir']
    if data.get('config_file_path'): del data['config_file_path']
    if data.get('authenticated'): del data['authenticated']
    with open(file_path, 'w') as file_writer:
        file_writer.write(json.dumps(data))

def authenticate(username, password, endpoint):
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
        config['username'] = username
        write_config_file(config['config_file_path'], config)
    else:
        click.echo(result.json()['errorMessage'])
        exit(10)

def get_clean_config():
    configuration = get_config()
    configuration['token'] = "**********"
    del configuration['headers']
    return configuration
