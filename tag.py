import pygsheets
from google.oauth2 import service_account
import json
from datetime import *
import datetime
import os
import subprocess as sp, sys
from dateutil.parser import parse

# Get the all arguments
username=sys.argv[1]
password=sys.argv[2]
tenantid=sys.argv[3]
sub_id=sys.argv[4]
grace_Days=int(sys.argv[5])
clientkey=sys.argv[6]
# print(type(grace_Days))
# grace_Days=3

# opening & authnetication of google sheet
with open('/gcp/gcp.json') as source:
    info = json.load(source)
credentials = service_account.Credentials.from_service_account_info(info)
client = pygsheets.authorize(service_account_file='/gcp/gcp.json')
sheet = client.open_by_key(clientkey)
wks = sheet.worksheet_by_title('Sheet1')
all_values = wks.get_all_values()

def auth():
    authoutput=sp.getstatusoutput("az login --service-principal -u {} -p {} --tenant {}".format(username,password,tenantid))
    return authoutput

authout=auth()
if(authout[0]==0):
    print("Authentication is successed")
else:
    print("Authentication failed",authout[1])
    exit()
# print("Raw All sheet values", all_values)
#getting required columns
cleaned_values = [[item for item in unique_list if item ]for unique_list in all_values]

# print("Clean values",cleaned_values)

fifth_column = wks.get_col(5)
fifth_list = [i for i in fifth_column if i]

fifth_list.remove('Required till (mm/dd/yyyy)')
# print("5th col final",fifth_list)

first_column = wks.get_col(1)
first_list = [i for i in first_column if i]

first_list.remove('Resource Details')
# print("1st col final",first_list)


second_column = wks.get_col(2)
second_list = [i for i in second_column if i]

second_list.remove('Azure Resource Group')
# print("\n2nd col final",second_list)

allready_schedul=(sp.getoutput(f'az group list --tag schedule-deletion --query [].name  -o tsv'))
allready_schedul_final=allready_schedul.split()
# print("already tag rg",allready_schedul_final)


#all Fuctions
# 1-function to tag
def tag(rg_name,enddate):
    if rg_name not in allready_schedul_final:
        print("Need to tag",rg_name)
        exit_status=os.system(f'az tag update --resource-id /subscriptions/{sub_id}/resourcegroups/{rg_name} --operation merge --tags schedule-deletion={enddate}')
        print(exit_status)
        if(exit_status==0):
            print("Tagged RG"+" --> "+ rg_name)
        else:
            print("Command fail to execute with exit status -> %d" % exit_status)
    else:
        print("Already scheduled deletion rg",rg_name)

# 2-function to find difference
def diff(list1, list2):
    return list(set(list1).symmetric_difference(set(list2)))

#3- function to remove common name from two list
def remove_common(a, b):
    for i in a[:]:
        if i in b:
            a.remove(i)
            b.remove(i)
    return a

output = sp.getoutput(f'az group list --query [].name  -o tsv')
azure_rg=output.split()
print("\nAll azure rg list: ",azure_rg)
print("\n All rg name in sheet: ",second_list)
required=diff(second_list,azure_rg)
print("\nlist of rg which are not in sheet",required)


deletion_tag =(sp.getoutput(f'az group list --tag deletion=locked --query [].name  -o tsv'))
deletion_tag_update=deletion_tag.split()

print("\nLocked rg",deletion_tag_update)
remove_common_update=remove_common(required,deletion_tag_update)
print("\nRG which do not have any deletion locked tag and not in sheet as well",remove_common_update)
date=datetime.datetime.today().strftime('%m/%d/%Y')
date1 = datetime.datetime.strptime(date, "%m/%d/%Y")
new_date=datetime.datetime(date1.year,date1.month,date1.day)
enddate = new_date + timedelta(days=grace_Days)

for x in remove_common_update:
    tag(x,enddate)

#vm_date= required till date
#date= current date 
for (rg_name,vm_date) in zip(second_list,fifth_list):
    date1 = parse(vm_date)
    date2 = parse(date)
    if(date2>date1):
        date1 = datetime.datetime.strptime(vm_date, "%m/%d/%Y")
        new_date=datetime.datetime(date1.year,date1.month,date1.day)
        enddate = new_date + timedelta(days=grace_Days)
        tag(rg_name,enddate)
    else:
        print("Resource group --->"+ rg_name + " is in required limits ")
