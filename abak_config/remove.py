import click
from abak_shared_functions import write_config_file, get_config

def get_keys(ctx, args, incomplete):
    config = get_config()
    return [key for key in config.keys() if incomplete in key]

@click.command(name='remove')
@click.option('--key', '-k', help="The key to be removed", required=True, prompt=True, autocompletion=get_keys)
@click.pass_context
def remove_config(ctx, key):
    '''
    Removes a key from the configuration file

    Args:
        key (str): The key to be removed
    '''
    remove_configuration_key(key)

def remove_configuration_key(key):
    configuration = get_config()
    if configuration.get(key):
        del configuration[key]
    write_config_file(configuration['config_file_path'], configuration)
