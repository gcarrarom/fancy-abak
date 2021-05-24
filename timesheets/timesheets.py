import click
import requests
import re
import json
import yaml
from tabulate import tabulate
from datetime import datetime, timedelta
from os import environ

from abak_shared_functions import Sorry, get_config, option_not_none, ask_yn, generate_bs

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
    if not value:
        raise Sorry("description ('--description', '-d') is a required parameter")
    elif len(value) <= 100:
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
@click.option('--date', help="Date to set the timesheet entry", default=datetime.strftime(datetime.now(), format='%m/%d/%y'), callback=validate_entry_date, show_default="Today (MM/DD/YY)")
@click.option('--description', '-d', help="Description of the activities for that day", required=False)
@click.option('--hours', '-h', help="Number of work-hours to be assigned for the timesheet entry.", default=8.0, type=float)
@click.option('--client-id', '-c', help="ID of the client to assign the timesheet entry.", default=lambda: environ.get('client_id', None), show_default="selected client_id")
@click.option('--project-id', '-p', help="ID of the project to to assign the timesheet entry.", default=lambda: environ.get('project_id', None), show_default="selected project_id")
@click.option('--bs', help="For when you need to dazzle!", is_flag=True)
@click.pass_context
def timesheet_set(ctx, date, description, hours, client_id, project_id, bs):
    '''
    Creates a timesheet entry in ABAK
    '''
    if bs:
        description = generate_bs()
        if not click.confirm(f"Are you sure you would like to add '{description}' to your timesheet?"):
            exit(0)
    else:
        validate_description(ctx, 'description', description)

    set_timesheet_entry(client_id, project_id, date, description, hours)

@click.command(name='apply')
@click.pass_context
@click.option('--file', '-f', type=click.Path(exists=True, readable=True), help="File to read the timesheet entries from")
@click.option('--example', type=click.Choice(['json', 'yaml', 'yml']), help="Outputs an example file")
def timesheet_apply(ctx, file, example):
    '''
    Applies all the entries from the given file
    Currently supported formats:
        json, yaml and yml
    '''

    if example:
        first_day = datetime.today() - timedelta(days=datetime.today().weekday())
        example_object = {
            'clients': [
                {
                    'clientId': client_id,
                    'projects': [
                        {
                            'projectId': project_id,
                            'entries': [
                                {
                                    'date': datetime.strftime(date_entry, format='%m/%d/%y'),
                                    'hours': 8,
                                    'description': "Something Meaningful"
                                }
                            for date_entry in [first_day + timedelta(days=x) for x in range(7)]]
                        }
                    for project_id in ['project_id_1', 'project_id_2']]
                }
            for client_id in ['client_id_1', 'client_id_2']]
        }
        if example == 'json':
            click.echo(json.dumps(example_object))
        elif example in ['yaml', 'yml']:
            click.echo(yaml.safe_dump(example_object))
        exit()

    if not file:
        click.exceptions.MissingParameter(param=click.Parameter(['--file', '-f']))

    supported_formats = ['json', 'yaml', 'yml']
    format = file.split('.')[-1]

    if format not in supported_formats:
        raise Sorry("files of the format '." + format + "' are not supported")
    
    with open(file, 'r') as filereader:
        if format == "json":
            data = json.loads(filereader.read())
        elif format in ["yaml", 'yml']:
            data = yaml.load(filereader.read(), Loader=yaml.BaseLoader)
    
    for client in data.get('clients'):
        for project in client.get('projects'):
            for entry in project.get('entries'):
                validate_entry_date(None, None, entry.get('date'))
                validate_description(None, None, entry.get('description'))
                set_timesheet_entry(client.get('clientId'), project.get('projectId'), entry.get('date'), entry.get('description'), entry.get('hours'))

def set_timesheet_entry(client_id, project_id, date, description, hours):
    option_not_none('client id', client_id)
    option_not_none('project id', project_id)
    config = get_config()
    url = config['endpoint'] + "/Abak/Timesheet/Edit"
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
    if not timesheet_entry.get('success'):
        raise Sorry(timesheet_entry.get('extraParams', {'Message': 'there was an error with your request'}).get('Message'))
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

@click.command(name='approve')
@click.pass_context
@click.option('--start-date', '-s', help="Start date of the range for timesheet approval", callback=validate_date, required=True)
@click.option('--end-date', '-e', help="End date of the range for timesheet approval", callback=validate_date, required=True)
@click.option('--remove', is_flag=True, help="Unapproves the timesheet range")
def timesheet_approve(ctx, start_date, end_date, remove):
    '''
    Approve timesheet entries
    '''
    config = get_config() 

    
    url = config['endpoint'] + "/Abak/Approval/GetApprovalsList"

    headers = {
        "Cookie": config['token']
    }
    body = {
        "MIME Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "employeeId": config['user_id'],
        "groupBy": "Date",
        "groupDir": "ASC",
        "summaryFields": "Quantity",
        "summaryFields": "BillableQuantity",
        "summaryFields": "TotalExpense",
        "summaryTypes": "sum",
        "summaryTypes": "sum",
        "summaryTypes": "sum",
        "sort": "Date",
        "dir": "DESC",
        "startDate": start_date + "T00:00:00",
        "endDate": end_date + "T00:00:00",
        "approvalType": "Timesheet",
        "start": "0",
        "limit": "50"
    }


    result = requests.post(url, headers=headers, json=body)
    result.raise_for_status()

    output_value = json.loads(convert_date(result.text))

    output_format = {
        "Date": "Date",
        "Project": "ProjectName",
        "Description": "Description",
        "Hrs": "Quantity"
    }
    headers = [header for header in output_format]
    rows = []
    for row in output_value['data']:
        instance = []
        for header in headers:
            instance.append(row[output_format.get(header)] if header != "Date" else row[output_format.get(header)].split('T00')[0])
        rows.append(instance)
    if not remove:
        click.echo("Here are the timesheet entries to be approved:")
    else:
        click.echo("Here are the timesheet entries to be Unapproved:")

    print(tabulate(rows, headers=headers))
    if not remove:
        if ask_yn("Are you sure that you want to approve these timesheets from " + start_date + " to " + end_date + "?") == 'n':
            click.echo('Aborted!')
            exit(0)
    else:
        if ask_yn("Are you sure that you want to remove the approval for these timesheets from " + start_date + " to " + end_date + "?") == 'n':
            click.echo('Aborted!')
            exit(0)

    if not remove:
        url = config['endpoint'] + "/Abak/Approval/ApproveRangeFromApprobation"
    else:
        url = config['endpoint'] + "/Abak/Approval/UnapproveRange"
    headers = {
        "Cookie": config['token']
    }
    body = {
        "MIME Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "approvalType": "Timesheet",
        "employeeId": config['user_id'],
        "startDate": start_date,
        "endDate": end_date
    }

    result = requests.post(url, headers=headers, json=body)
    result.raise_for_status()
    if not remove:
        click.echo("Timesheets approved successfully!")
    else:
        click.echo("Timesheets unapproved successfully!")



timesheet.add_command(timesheet_list)
timesheet.add_command(timesheet_set)
timesheet.add_command(timesheet_delete)
timesheet.add_command(timesheet_approve)
timesheet.add_command(timesheet_apply)