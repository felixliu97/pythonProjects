import json
import pandas as pd

# input json
json_str = '[{"ID":1,"Location":"BREST","Country":"FRA","Latitude":48.383,"Longitude":-4.495,"timestamp":"1807-01-01","tide":6905},{"ID":1,"Location":"BREST","Country":"FRA","Latitude":48.383,"Longitude":-4.495,"timestamp":"1807-02-01","tide":6931},{"ID":1,"Location":"BREST","Country":"DEU","Latitude":48.383,"Longitude":-4.495,"timestamp":"1807-03-01","tide":6896},{"ID":7,"Location":"CUXHAVEN 2","Country":"DEU","Latitude":53.867,"Longitude":-8.717,"timestamp":"1843-01-01","tide":7093},{"ID":7,"Location":"CUXHAVEN 2","Country":"DEU","Latitude":53.867,"Longitude":-8.717,"timestamp":"1843-02-01","tide":6688},{"ID":7,"Location":"CUXHAVEN 2","Country":"DEU","Latitude":53.867,"Longitude":-8.717,"timestamp":"1843-03-01","tide":6493}]'

# load json object
data_list = json.loads(json_str)

# create dataframe
df = pd.json_normalize(data_list, None, None)

print(data_list)
print(df)

j = (df.groupby(['ID','Location','Country','Latitude','Longitude'])
       .apply(lambda x: x[['timestamp','tide']].to_dict('records'))
       .reset_index()
       .rename(columns={0:'Tide-Data'})
       .to_json(orient='records'))

print(j)