import click
import os
import json
import requests
import re

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
        config['abak_date_format'] = re.findall(r'(?:\{)(.*?)(?:\})', re.findall(r'(?:AbakDateFormat=)(.*?)(?:;)', result.headers['Set-Cookie'])[0])[-1]
        if not config.get('date_format'):
            config['date_format'] = "%Y-%m-%d"
        write_config_file(config['config_file_path'], config)
    else:
        click.echo(result.json()['errorMessage'])
        exit(10)

def get_clean_config():
    configuration = get_config()
    configuration['token'] = "**********"
    del configuration['headers']
    return configuration


def get_date_format_from_abak(abak_date):
    format_date = {
        'M/dd/yy': '%m/%d/%y',
        "d/M/y": '%m/%d/%y',
        "dd/MM/yy": "%d/%m/%y",
        "dd/MM/yyyy": "%d/%m/%Y",
        "d/M/yy": "%d/%m/%y",
        "d/M/yyyy": "%d/%m/%Y",
        "d/MM/yyyy": "%d/%m/%Y",
        "dd/M/yyyy": "%d/%m/%Y",
        "dd-MM-yyyy": '%d-%m-%Y', 
        "d-MM-yyyy": '%d-%m-%Y', 
        "d-M-yyyy": '%d-%m-%Y', 
        "d-M-yy": '%d-%m-%y', 
        "dd-M-yyyy": '%d-%m-%Y',
        "d-M-y":  '%d-%m-%y',
        "M-dd-yy": '%m-%d-%y',
        "Y/M/d": '%Y/%m/%d',
        "yyyy/MM/dd": '%Y/%m/%d',
        "Y-M-d": '%Y-%m-%d', 
        "yyyy-MM-dd": '%Y-%m-%d',
        "yyyy/M/d": '%Y/%m/%d',
        "yyyy-M-d": '%Y-%m-%d',
        "y/M/d": '%y/%m/%d',
        "yy/MM/dd": '%y/%m/%d',
        "y-M-d": '%y-%m-%d',
        "yy-MM-dd": '%y-%m-%d'
    }

    return format_date.get(abak_date)