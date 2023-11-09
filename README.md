# Fancy Abak

![PyPI - Downloads](https://img.shields.io/pypi/dm/fancy-abak)
![PyPI](https://img.shields.io/pypi/v/fancy-abak?style=flat)
CLI tool to use ABAK

- [Fancy Abak](#fancy-abak)
  - [Available Commands](#available-commands)
  - [Requirements](#requirements)
  - [Installation](#installation)
    - [MacOS](#macos)

## Available Commands

```bash
$ abak --help
Usage: abak [OPTIONS] COMMAND [ARGS]...

  Abak UI, NEVER AGAIN!

Options:
  --help  Show this message and exit.

Commands:
  client     Find clients to assign timesheet entries
  config     Group of commands to manage the jiractl command line
  context    Context operations for Abak.
  do         GPT Powered command to "do" something
  login
  open       Opens abak on your default browser - Please don't use this :)
  project    Find projects to assign timesheet entries
  timesheet  Commands to manage timesheet entries
```

## Requirements

- (Tested and built using) Python >3.11

## Installation

Package is available in PyPi:

```shell
pip install fancy-abak
```

### MacOS

Package is available in brew:

```shell
brew tap gcarrarom/fancygui
brew install gcarrarom/fancygui/fancy-abak
```
