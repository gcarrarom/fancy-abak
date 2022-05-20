import webbrowser
import click
import timesheets
import client
import project
import abak_config
import os
from click_keyring import keyring_option
import keyring
from abak_context import context

from requests.exceptions import ConnectionError

from abak_shared_functions import (
    write_config_file,
    get_config,
    authenticate,
    httprequest,
    Sorry
)


@click.group()
@click.pass_context
def abak(ctx):
    config = get_config()
    if ctx.invoked_subcommand not in ["login", "config"]:
        try:
            result = httprequest("get", None, "/Abak/Transact/GetEmployee_Optimized")
            config["user_id"] = result["data"][0]["Id"]
            write_config_file(config["config_file_path"], config)
            [
                os.environ.setdefault(key, config[key])
                for key in config
                if key
                not in [
                    "app_dir",
                    "config_file_path",
                    "authenticated",
                    "headers",
                    "token",
                    "contexts"
                ]
            ]
        except ConnectionError:
            Sorry(
                "it seems that you are not connected to the internet or the endpoint is not available"
            )
        except Exception:
            try:
                authenticate(
                    config["username"],
                    keyring.get_password("fancy-abak", config["username"]),
                    config["endpoint"],
                )
            except KeyError:
                click.echo("Please login first!")
                exit(127)
            except Exception as exception:
                raise exception


@click.command()
@click.option(
    "-u", "--username", help="the username to use for login", required=True, prompt=True
)
@keyring_option(
    "-p", "--password", help="the password to use for login", prefix="fancy-abak"
)
@click.option(
    "-e",
    "--endpoint",
    help="The endpoint where abak is hosted",
    required=True,
    prompt=True,
)
def login(username, password, endpoint):
    authenticate(username, password, endpoint)
    click.echo("Login Successul!")


@click.command(name="open")
def open_browser():
    config = get_config()
    webbrowser.open(config["endpoint"])



abak.add_command(login)
abak.add_command(open_browser)

abak.add_command(timesheets.timesheet)
abak.add_command(client.client)
abak.add_command(project.project)
abak.add_command(abak_config.config)
abak.add_command(context)


if __name__ == "__main__":
    abak()