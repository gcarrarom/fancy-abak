import click
import requests
import re
import json
from tabulate import tabulate
from datetime import datetime, timedelta
from os import environ

from abak_shared_functions import Sorry, get_config, option_not_none

@click.group()
@click.pass_context
def timesheet(ctx):
    '''
    Commands to manage timesheet entries
    '''
    pass

def validate_date(ctx, param, value):
    if re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        return value
    else:
        raise Sorry("date needs to be in the format YYYY-MM-dd")

def validate_entry_date(ctx, param, value):
    if re.match('[0-9]{2}/[0-9]{2}/[0-9]{2}', value):
        return value
    else:
        raise Sorry("date needs to be in the format MM/dd/YY")

def validate_description(ctx, param, value):
    if len(value) <= 100:
        return value
    else:
        raise Sorry("description of the timesheet entry must not be larger than 100 characters")

@click.command(name='list')
@click.pass_context
@click.option('-d', '--date', help='The reference date to use for the query. Format YYYY-MM-dd', required=False, callback=validate_date, default=datetime.strftime(datetime.now(), format='%Y-%m-%d'))
@click.option('-o', '--output', help='The output type you want', type=click.Choice(['json', 'table']), default='table')
@click.option('--query-range', '-r', help="The range to query for", type=click.Choice(['Weekly', 'Monthly', "Daily"]), default="Weekly")
@click.option('--show-totals', help="Show a summary of all projects for the given range", is_flag=True)
@click.option('--show-id', help="Shows the ID of each timesheeet entry", is_flag=True)
@click.option('--previous', help="Shows the previous iteration from the range", is_flag=True)
def timesheet_list(ctx, date, output, query_range, show_totals, show_id, previous):
    '''
    Lists the timesheet entries in ABAK
    '''
    config = get_config()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": config['token']
    }
    if previous:
        #click.echo(date)
        date_datetime = datetime.strptime(date, "%Y-%m-%d") 
        delta = timedelta(days=date_datetime.day + 1) if query_range == "Monthly" else timedelta(days=1) if query_range == "Daily" else timedelta(weeks=1)
        date = datetime.strftime(date_datetime - delta, format='%Y-%m-%d') 
        #click.echo(date)
    body = {
        "groupBy": "TransactType",
        "groupDir": "ASC",
        "summaryFields": "Quantity",
        "summaryTypes": "sum",
        "sort": "Date",
        "dir": "ASC",
        "employe": config['user_id'],
        "date": date + "T00:00:00",
        "range": query_range
    }
    result = requests.post(config['endpoint'] +  '/Abak/Transact/GetGroupedTransacts', headers=headers, data=body)
    result.raise_for_status()
    output_value = json.loads(convert_date(result.text))
    #click.echo(result.text)
    if output == 'json':
        print(json.dumps(output_value.get('data')))
    elif output == 'table':
        if show_totals:
            click.echo("For the " + ("month" if query_range == "Monthly" else "day" if query_range == "Daily" else "week") + 
                        " of " + date + ", here are the totals:")
            totals = {} 
            for row in output_value.get('data'):
                totals[row['ProjectName']] = totals.get(row['ProjectName'], 0) + row.get('Quantity', 0)
            totals['TOTAL'] = sum([ totals[total] for total in totals])
            headers = ['ProjectName', 'Quanty']
            print(tabulate([[total, totals[total]]for total in totals], headers=headers, numalign="left", colalign=("right",)))
        else:
            output_format = {
                "Date": "Date",
                "Project": "ProjectName",
                "Description": "Description",
                "Hrs": "Quantity"
            }
            if show_id:
                output_format['ID'] = "Id"
            headers = [header for header in output_format]
            rows = []
            for row in output_value['data']:
                instance = []
                for header in headers:
                    instance.append(row[output_format.get(header)] if header != "Date" else row[output_format.get(header)].split('T00')[0])
                rows.append(instance)
            print(tabulate(rows, headers=headers))
    elif output == "python":
        return [(row['Id'], row['Description']) for row in output_value.get('data')]

def convert_date(text):
    start = text.find('new Date')
    finish = text.find('),', start) + 1
    next = finish
    while next > 0:
        date_to_convert = text[start:finish]
        date_to_convert_array = date_to_convert[date_to_convert.find('(')+1:date_to_convert.find(')')].split(',')
        date_output = f'"{date_to_convert_array[0]}-{int(date_to_convert_array[1])+1:02d}-{date_to_convert_array[2]}T00:00:00"'
        text = text.replace(date_to_convert, date_output)
        start = text.find('new Date', next)
        finish = text.find('),', start) + 1
        next = finish

    return text

@click.command(name='set')
@click.option('--date', help="Date to set the timesheet entry", default=datetime.strftime(datetime.now(), format='%m/%d/%y'), callback=validate_entry_date)
@click.option('--description', '-d', help="Description of the activities for that day", required=True, callback=validate_description)
@click.option('--hours', '-h', help="Number of work-hours to be assigned for the timesheet entry.", default=8.0, type=float)
@click.option('--client-id', '-c', help="ID of the client to assign the timesheet entry.", default=lambda: environ.get('client_id', None))
@click.option('--project-id', '-p', help="ID of the project to to assign the timesheet entry.", default=lambda: environ.get('project_id', None))
@click.pass_context
def timesheet_set(ctx, date, description, hours, client_id, project_id):
    '''
    Creates a timesheet entry in ABAK
    '''
    option_not_none('client id', client_id)
    option_not_none('project id', project_id)
    config = get_config()
    url = "https://payme.objectsharp.com/Abak/Timesheet/Edit"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": config['token']
    }
    body = {
        "MIME Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "fieldDate": date,
        "typeTab": "timesheetDetail",
        "": "true",
        "rangeField": "Weekly",
        "defaultDate": date,
        "fieldId": "",
        "fieldIsDuplicatingTs": False,
        "fieldEmployeeId": config['user_id'],
        "isPhaseEmplAssigned": "",
        "isDefaultTaskAssignedOnEmp": "",
        "isDefaultPayCodeAssignedOnEmp": "",
        "defaultPayCodeAssignedOnEmp": "",
        "taskDefaultPayCode": "",
        "isDefaultTaskAssignedOnFun": "",
        "isDefaultPayCodeAssignedOnFun": "",
        "defaultPayCodeAssignedOnFun": "",
        "isPhaseFunctionAssigned": "",
        "taskDefaultTaskCode": "",
        "phaseDefaultPayCode": "",
        "functionDefaultTaskCode": "",
        "phaseDefaultDepartment": "",
        "phaseDefaultReference": "",
        "isPhaseBillable": "",
        "phaseDefaultExpenseType": "",
        "defaultDepartmentAssignedOnEmp": "",
        "defaultReferenceAssignedOnEmp": "",
        "defaultExpenseTypeAssignedOnEmp": "",
        "defaultDepartmentAssignedOnFun": "",
        "defaultReferenceAssignedOnFun": "",
        "defaultExpenseTypeAssignedOnFun": "",
        "defaultTaskAssignedOnEmp": "",
        "defaultTaskAssignedOnFun": "",
        "defaultPayCodeOnTaskAssignedOnEmp": "",
        "defaultPayCodeOnTaskAssignedOnFun": "",
        "phaseDescFr": "",
        "phaseDescEn": "",
        "phaseDesc": "",
        "queryTextField": "Consulting by Associate (CONS)",
        "fieldManualCost": "",
        "fieldManualDayCost": "",
        "fieldManualSelling": "",
        "fieldManualDaySelling": "",
        "fieldcheckPaySystem": "fieldcheckPaySystem",
        "fieldcheckPaySystemSate": "fieldcheckPaySystemSate",
        "payCodeIsInList": "true",
        "clientIsInList": "true",
        "projectIsInList": "true",
        "taskCodeIsInList": "true",
        "departmentIsInList": "true",
        "datebookId": "",
        "fieldClientId_Value": client_id,
        "fieldClientId_SelIndex": -1,
        "fieldProjectId_Value": project_id,
        "fieldProjectId_SelIndex": -1,
        "fieldTaskCode_Value": "CONS",
        "fieldTaskCode_SelIndex": -1,
        "fieldPhaseId": "",
        "fieldPhaseId_current": "",
        "fieldPhaseIdReal": "",
        "fieldMSProjectCode": "",
        "fieldMsProject": "",
        "fieldDescription_Value": description,
        "fieldDescription": description,
        "fieldDescription_SelIndex": "-1",
        "fieldReference": "",
        "fieldIsPrintOnInvoice": "fieldIsPrintOnInvoice",
        "fieldDepartmentId_Value": "",
        "fieldDepartmentId": "",
        "fieldDepartmentId_SelIndex": -1,
        "fieldPayCode_Value": "REG",
        "fieldPayCode": "Regular (REG)",
        "fieldPayCode_SelIndex": -1,
        "fieldIsAffectingTimebank": "fieldIsAffectingTimebank",
        "fieldQuantity": str(hours) + " hrs",
        "fieldTimeStart_Value": "",
        "fieldTimeStart": "",
        "fieldTimeStart_SelIndex": -1,
        "fieldTimeEnd_Value": "",
        "fieldTimeEnd": "",
        "fieldTimeEnd_SelIndex": -1,
        "fieldLunchTime": "0.00 hrs",
        "fieldIsBillable": "fieldIsBillable",
        "fieldBillableQuantity": str(hours) + " hrs",
        "panelGroupInvoicableTimesheetDetailFieldUnitCost": "0.0000 $",
        "TimesheetDetailFieldSubTotal": "0.00 $",
        "fieldEmployeeTimesheetDetail": "",
        "fieldNote": "",
        "billableDescriptionTimesheetDetail": "",
        "fieldBillableNoteTimesheetDetail": "",
        "tabPanel_ActiveTab": {"tabDetail":0}
    }

    result = requests.post(url, headers=headers, data=body)
    result.raise_for_status()
    timesheet_entry = result.json()
    click.echo("Timesheet entry " + timesheet_entry.get('extraParams', {"newID": ""}).get('newID') + " created successully!")


def get_weekly_timesheet(ctx, *args, **kwargs):
    config = get_config()
    date = datetime.strftime(datetime.now(), format='%Y-%m-%d')
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": config['token']
    }
    body = {
        "groupBy": "TransactType",
        "groupDir": "ASC",
        "summaryFields": "Quantity",
        "summaryTypes": "sum",
        "sort": "Date",
        "dir": "ASC",
        "employe": config['user_id'],
        "date": date + "T00:00:00",
        "range": range
    }
    result = requests.post(config['endpoint'] + '/Abak/Transact/GetGroupedTransacts', headers=headers, data=body)
    result.raise_for_status()
    output_value = json.loads(convert_date(result.text))
    return [(row['Id'], row['Description']) for row in output_value.get('data')]

@click.command(name='delete')
@click.pass_context
@click.argument('id')
def timesheet_delete(ctx, id):
    '''
    Deletes a timesheet entry from ABAK

    id (str): ID of the timesheet to delete
    '''
    config = get_config() 
    url = config['endpoint'] + "/Abak/Transact/DeleteTransacts"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Cookie": config['token']
    }
    body = {
        "transacts":[
            {
                "key":id,
                "value":"T"
            }
        ]
    }

    result = requests.post(url, headers=headers, json=body)
    result.raise_for_status()
    click.echo("Timesheet entry " + id + " deleted successfully!")

timesheet.add_command(timesheet_list)
timesheet.add_command(timesheet_set)
timesheet.add_command(timesheet_delete)