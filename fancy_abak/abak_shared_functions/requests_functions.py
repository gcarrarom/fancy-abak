import requests
from .exceptions import Sorry
from .abak_configuration_functions import get_config, write_config_file
import json
import re


def convert_date(text):
    start = text.find("new Date")
    finish = text.find("),", start) + 1
    next_instance = finish
    while next_instance > 0:
        date_to_convert = text[start:finish]
        date_to_convert_array = date_to_convert[
            date_to_convert.find("(") + 1 : date_to_convert.find(")")
        ].split(",")
        date_output = f'"{date_to_convert_array[0]}-{int(date_to_convert_array[1])+1:02d}-{date_to_convert_array[2]}T00:00:00"'
        text = text.replace(date_to_convert, date_output)
        start = text.find("new Date", next_instance)
        finish = text.find("),", start) + 1
        next_instance = finish

    return text


def httprequest(request_type, body, path, is_json=False, headers={}):
    request_function = {"GET": requests.get, "POST": requests.post}.get(
        request_type.upper(), None
    )

    config = get_config()
    headers["Cookie"] = config["token"]

    if is_json:
        result = request_function(config["endpoint"] + path, headers=headers, json=body)
    else:
        result = request_function(config["endpoint"] + path, headers=headers, data=body)
    try:
        result.raise_for_status()
        output_value = json.loads(convert_date(result.text))
        return output_value
    except requests.exceptions.HTTPError as error:
        raise Sorry(re.findall("(<title>)(.*)(</title>)", result.text)[0][1])


def fancy_abak_request(request_type, body, path, is_json, headers={}):
    request_function = {
        "GET": requests.get,
        "POST": requests.post,
        "DELETE": requests.delete,
    }.get(request_type.upper(), None)

    config = get_config()
    headers["Authorization"] = config["access_token"]
    if path == "/chat":
        if config.get("thread_id"):
            body["thread_id"] = config.get("thread_id")
    if is_json:
        result = request_function(
            config["fancy_abak_endpoint"] + path, headers=headers, json=body
        )
    else:
        result = request_function(
            config["fancy_abak_endpoint"] + path, headers=headers, data=body
        )
    try:
        result.raise_for_status()
        output_value = json.loads(convert_date(result.text))
        if path == "/chat":
            config["thread_id"] = output_value["thread_id"]
            write_config_file(config["config_file_path"], config)
        return output_value
    except requests.exceptions.HTTPError as error:
        raise Sorry(re.findall("(<title>)(.*)(</title>)", result.text)[0][1])
