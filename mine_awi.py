import json
from api_calls import get_sensors_list, get_sensors_devices, get_device_information
import csv
from csv import writer
import numpy as np
import pandas as pd1
import requests
from bs4 import BeautifulSoup
from csv import DictReader
import re
import pangaeapy.panquery as query
import pangaeapy.pandataset as pd


def get_dataset_details(doi):
    location=[]
    ds = pd.PanDataSet(doi)
    print(ds.title)
    print(ds.events)
    supplement_to=''
    for event in ds.events:
        print(event.location)
        location.append(event.location)
    if 'uri' in ds.supplement_to:
        print(ds.supplement_to['uri'])
        supplement_to=ds.supplement_to['uri']
      
    location=list(set(location))
    return {'title': ds.title, 'description': ds.abstract , 'location': location, 'supplement_to': supplement_to}

def get_sensors_datasets():
    data = pd1.read_csv("devices_metadata.csv")
    sensors = list(set(data['sensor_name'].tolist()))
    
    file = open("sensors_datasets.csv", "a", encoding="utf-8", newline='')
    writer = csv.writer(file)
    writer.writerow(["sensor_name",
                "dataset_doi",
                "title",
                "description",
                "location",
                "supplement_to"])
                
    exclude=["lander", "mooring", "pH meter"]
    for i in sensors[:]:
        if i in exclude:
            sensors.remove(i)
    print(sensors)
                
    for sensor in sensors:
        value=0
        total_pages=0
        while True:
            print('sensor', sensor)
            print("value", value)
            response=query.PanQuery(query='device:'+f'"{sensor}"', offset=value)
            if value==0:
                total_pages=response.totalcount/10
            print(len(response.result))
            for dataset in response.result:
                print(dataset['URI'])
                dataset_info=get_dataset_details(dataset['URI'])
                writer.writerow([sensor, dataset['URI'], dataset_info['title'], dataset_info['description'], dataset_info['location'], dataset_info['supplement_to']])
                #sensor, dataset['URI'], dataset_info['title'], dataset_info['description'], dataset_info['location'], dataset_info['supplement_to']
            if value > total_pages:
                break
            value = value+10

def retrieve_sensors_list():
    return get_sensors_list().json()['facets'][0]['children']
    
def get_sensor_devices(sensor_name):
    return get_sensors_devices(sensor_name).json()
    
def get_device_metadata(device_id):
    response=get_device_information(device_id).json()

    contact=''
    if len(response['contactRoleItem'])>0:
        contact=response['contactRoleItem'][0]['contact']
    print(response['longName'], response['description'], response['serialNumber'], response['manufacturer'], response['model'], response['citation'])
    
    companyName=''
    firstName=''
    lastName=''
    if 'companyName' in contact:
        companyName=contact['companyName']
    if 'firstName' in contact:
        firstName=contact['firstName']
    if 'lastName' in contact:
        lastName=contact['lastName']
    print(companyName, firstName+' '+lastName)
    
    return {
        'longName': response['longName'],
        'description': response['description'],
        'serialNumber': response['serialNumber'],
        'manufacturer': response['manufacturer'],
        'model': response['model'],
        'citation': 'https://hdl.handle.net/'+response['citation'],
        'companyName': companyName,
        'name': firstName+' '+lastName
    }
    
def add_sensors_datasets_in_orkg():
    df = pd1.read_csv('sensors_datasets.csv')
    
    new_df = df.groupby(['sensor_name'])
    count=0
    for name, group in new_df:
        for index, row in group.iterrows():
            supplement_to=row['supplement_to']
            if not supplement_to is np.nan:
                print(name, supplement_to)
                count=count+1
                print("\n")
    print(count)
    
    

def main():
    #HTMLFile = open("platforms.html", "r", encoding="utf-8")
    #index = HTMLFile.read()
        
    #parse_platforms_information(index)
    #retrieve_instruments_metadata()
    
    #retrieve_sensors_related_papers()
    #1
    '''
    file = open("devices_metadata.csv", "a", encoding="utf-8", newline='')
    writer = csv.writer(file)
    writer.writerow(["sensor_name",
                "device_id",
                "longName",
                "description",
                "serialNumber",
                "manufacturer",
                "model",
                "citation",
                "companyName",
                "name"])
    
    sensors_list=retrieve_sensors_list()
    for sensor in sensors_list:
        print(sensor['label'])
        devices=get_sensor_devices(sensor['label'])
        for device in devices['records']:
            print(device['uniqueId'])
            device_info=get_device_metadata(device['uniqueId'])
            writer.writerow([sensor['label'],
                device['uniqueId'],
                device_info['longName'],
                device_info['description'],
                device_info['serialNumber'],
                device_info['manufacturer'],
                device_info['model'],
                device_info['citation'],
                device_info['companyName'],
                device_info['name']])
    '''
     
    #2
    #get_sensors_datasets()
    
    #3
    add_sensors_datasets_in_orkg()
    
    
    #HTMLFile = open("Browse by Platform_EPIC.html", "r", encoding="utf-8")
    #index = HTMLFile.read()
        
    #dois = extract_doi(index)
    #print(dois)

    

if __name__ == "__main__":
    main()