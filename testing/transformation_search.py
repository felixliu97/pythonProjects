import requests
from datetime import date

schema = input('Which Schema would you like to search in? ')
user = input('What is your user id? ')
search = input('What would you like to search for? ')

today = date.today()

cert = 'ca_bundle.crt'
url = "https://ebglossary.prod.k8s.osp.dataeng.internal/api/search"
payload = "{{\n\t\"searchString\": \"{}\",\n\t\"asset_types\": [\"EDH Table\"],\n\t\"user_id\": \"{}\"}}".format(schema, user)
headers = {'Content-Type': 'application/json',}

result = requests.post(url, headers=headers, data = payload, verify = cert).json()

tab_result = []
tab_result.extend(result['data'])
output_result = []

for item in tab_result:
    if item['title']:
        tab_step = tab_result.index(item)
        arr_result = tab_result[tab_step]['__elements']

        for item1 in arr_result:
            if item1['type'] == 'table_column':
                if 'Transformation logic detail' in item1.keys():
                    tl = item1['Transformation logic detail']
                    ex = tl.find(search)
                    if ex >= 0:
                        res = item['title'] + "." + item1['column']
                        output_result.append(res)
                        print(res)
                        
open('{}.output_result.{}.{}.txt'.format(schema, user, today),'w').write('\n'.join(sorted(output_result)))