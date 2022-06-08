from abak_shared_functions.requests_functions import httprequest
import click
import re
import json
import yaml
from tabulate import tabulate

from datetime import datetime, timedelta
import calendar
from os import environ

from abak_shared_functions import (
    Sorry, 
    get_config, 
    option_not_none, 
    generate_bs,
    get_date_format_from_abak
)

from abak_context import get_contexts
from project import get_projects

@click.group()
@click.pass_context
def timesheet(ctx):
    '''
    Commands to manage timesheet entries
    '''
    pass

def validate_entry_date(ctx, param, value):
    if not value:
        return None
    config = get_config()
    if value.upper() in ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]:
        return value
    try:
        datetime.strptime(value, config['date_format'])
        return value
    except:
        raise Sorry(f"date needs to be in the format {config['date_format']}")

def validate_description(ctx, param, value):
    if not value:
        raise Sorry("description ('--description', '-d') is a required parameter")
    elif len(value) <= 100:
        return value
    else:
        raise Sorry("description of the timesheet entry must not be larger than 100 characters")

@click.command(name='list')
@click.pass_context
@click.option('-d', '--date', help='The reference date to use for the query. Format in the config key "date_format"', required=False, callback=validate_entry_date)
@click.option('-o', '--output', help='The output type you want', type=click.Choice(['json', 'table', 'wide']), default='table')
@click.option('--query-range', '-r', help="The range to query for", type=click.Choice(['Weekly', 'Monthly', "Daily"]), default="Weekly")
@click.option('--show-totals', help="Show a summary of all projects for the given range", is_flag=True)
@click.option('--show-id', help="Shows the ID of each timesheeet entry", is_flag=True)
@click.option('--previous', help="Shows the previous iteration from the range", is_flag=True)
def timesheet_list(ctx, date, output, query_range, show_totals, show_id, previous):
    '''
    Lists the timesheet entries in ABAK
    '''
    list_timesheet_entries(date, output, query_range, show_totals, show_id, previous)
    
def list_timesheet_entries(date, output, query_range, show_totals, show_id, previous):
    config = get_config()

    if not date:
        date = datetime.strftime(datetime.now(), format=config['date_format'])

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    if previous:
        #click.echo(date)
        date_datetime = datetime.strptime(date, config['date_format']) 
        delta = timedelta(days=date_datetime.day + 1) if query_range == "Monthly" else timedelta(days=1) if query_range == "Daily" else timedelta(weeks=1)
        date = datetime.strftime(date_datetime - delta, format=config['date_format']) 
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

    output_value = httprequest('POST', body, '/Abak/Transact/GetGroupedTransacts', headers=headers)
    if output == 'json':
        print(json.dumps(output_value.get('data')))
    elif output in ['table', 'wide']:
        projects_clean = get_projects(None, "", 'python')
        project_map = {}
        contexts = get_contexts()
        for project in projects_clean:
            project_cons = project['Display'][0:60]
            for context in contexts:
                if project['Id'] == contexts[context]['Project']:
                    project_map[project_cons] = context

        if show_totals:
            date_datetime = datetime.strptime(date, config['date_format']) 
            click.echo("For the " + (f"month of {calendar.month_name[date_datetime.month]}" if query_range == "Monthly" else "day of " + date if query_range == "Daily" else "week of " + date) + 
                        ", here are the totals:")
            totals = {} 
            for row in output_value.get('data'):
                totals[row['ProjectName']] = totals.get(row['ProjectName'], 0) + row.get('Quantity', 0)
            totals['TOTAL'] = sum([ totals[total] for total in totals])
            headers = ['ProjectName', 'Quanty']
            print(tabulate([[total, totals[total]]for total in totals], headers=headers, numalign="left", colalign=("right",)))
        else:
            output_format = {
                "Weekday": "Date",
                "Date": "Date",
                "Project": "ProjectName",
                "Description": "Description",
                "Hrs": "Quantity"
            }
            if output == 'wide':
                output_format['Date'] = 'Date'
                output_format['ID'] = "Id"

            if show_id:
                output_format['ID'] = "Id"
            headers = [header for header in output_format]
            rows = []
            for row in output_value['data']:
                instance = []
                for header in headers:
                    if header == 'Weekday':
                        date_text = row[output_format.get(header)].split('T00')[0]
                        date_instance = datetime.strptime(date_text, config['date_format'])
                        instance.append(date_instance.strftime('%A'))
                    elif header == 'Project':
                        instance.append(project_map.get(row[output_format[header]][0:60], row[output_format[header]]))
                    else:
                        instance.append(row[output_format.get(header)] if header != "Date" else row[output_format.get(header)].split('T00')[0])
                rows.append(instance)
            print(tabulate(rows, headers=headers))
    elif output == "python":
        return output_value.get('data')

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
@click.option('--date', help="Date to set the timesheet entry", callback=validate_entry_date, show_default="Today")
@click.option('--yesterday', help="Sets the date to yesterday", is_flag=True)
@click.option('--description', '-d', help="Description of the activities for that day", required=False)
@click.option('--context', help="Context to use when setting the timesheet", default=lambda: environ.get('current_context', None))
@click.option('--hours', '-h', help="Number of work-hours to be assigned for the timesheet entry.", default=8.0, type=float)
@click.option('--client-id', '-c', help="ID of the client to assign the timesheet entry.", default=lambda: environ.get('client_id', None), show_default="selected client_id")
@click.option('--project-id', '-p', help="ID of the project to to assign the timesheet entry.", default=lambda: environ.get('project_id', None), show_default="selected project_id")
@click.option('--bs', help="For when you need to dazzle!", is_flag=True)
@click.pass_context
def timesheet_set(ctx, date, description, context, hours, client_id, project_id, bs, yesterday):
    '''
    Creates a timesheet entry in ABAK
    '''
    days_of_the_week = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    config = get_config()
    if yesterday:
        date = datetime.strftime(datetime.now() - timedelta(days=1), format=config['date_format'])
    elif date.upper() in days_of_the_week:
        date = datetime.strftime(datetime.now() - timedelta(days=datetime.now().weekday()) + timedelta(days=days_of_the_week.index(date.upper())), format=config['date_format'])
    elif not date:
        date = datetime.strftime(datetime.now(), format=config['date_format'])

    contexts = get_contexts()
    selected_context = contexts.get(context, None)

    if selected_context:
        client_id = selected_context['Client']
        project_id = selected_context['Project']
    if bs:
        description = generate_bs()
        click.confirm(f"Are you sure you would like to add '{description}' to your timesheet?", abort=True)
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
    config = get_config()
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
                                    'date': datetime.strftime(date_entry, format=config['date_format']),
                                    'hours': 8,
                                    'description': "Something Meaningful"
                                }
                            for date_entry in [first_day + timedelta(days=x) for x in range(2)]]
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
    date = datetime.strftime(datetime.strptime(date, config['date_format']), get_date_format_from_abak(config['abak_date_format']))
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
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

    timesheet_entry = httprequest('POST', body, "/Abak/Timesheet/Edit", headers=headers)
    if not timesheet_entry.get('success'):
        raise Sorry(timesheet_entry.get('extraParams', {'Message': 'there was an error with your request'}).get('Message'))
    click.echo("Timesheet entry " + timesheet_entry.get('extraParams', {"newID": ""}).get('newID') + " created successully!")


def get_weekly_timesheet(ctx, *args, **kwargs):
    config = get_config()
    date = datetime.strftime(datetime.now(), format=config['date_format'])
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
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
    output_value = httprequest('POST', body, '/Abak/Transact/GetGroupedTransacts', headers=headers)
    return [(row['Id'], row['Description']) for row in output_value.get('data')]

@click.command(name='delete')
@click.pass_context
@click.argument('id')
def timesheet_delete(ctx, id):
    '''
    Deletes a timesheet entry from ABAK
    '''
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    body = {
        "transacts":[
            {
                "key":id,
                "value":"T"
            }
        ]
    }

    result = httprequest('POST', body, "/Abak/Transact/DeleteTransacts", is_json=True, headers=headers)
    click.echo("Timesheet entry " + id + " deleted successfully!")


@click.command(name='approve')
@click.pass_context
@click.option('--start-date', '-s', help="Start date of the range for timesheet approval", callback=validate_entry_date, required=True)
@click.option('--end-date', '-e', help="End date of the range for timesheet approval", callback=validate_entry_date, required=True)
@click.option('--remove', is_flag=True, help="Unapproves the timesheet range")
def timesheet_approve(ctx, start_date, end_date, remove):
    '''
    Approve timesheet entries
    '''
    config = get_config() 
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

    output_value = httprequest('POST', body, "/Abak/Approval/GetApprovalsList", is_json=True)

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
        click.confirm("Are you sure that you want to approve these timesheets from " + start_date + " to " + end_date + "?", abort=True)
    else:
        click.confirm("Are you sure that you want to remove the approval for these timesheets from " + start_date + " to " + end_date + "?", abort=True)

    if not remove:
        path = "/Abak/Approval/ApproveRangeFromApprobation"
    else:
        path = "/Abak/Approval/UnapproveRange"
    body = {
        "MIME Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "approvalType": "Timesheet",
        "employeeId": config['user_id'],
        "startDate": start_date,
        "endDate": end_date
    }

    result = httprequest('POST', body, path, is_json=True)
    if not remove:
        click.echo("Timesheets approved successfully!")
    else:
        click.echo("Timesheets unapproved successfully!")



timesheet.add_command(timesheet_list)
timesheet.add_command(timesheet_set)
timesheet.add_command(timesheet_delete)
timesheet.add_command(timesheet_approve)
timesheet.add_command(timesheet_apply)
