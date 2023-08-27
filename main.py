import json
from api_calls import get_instruments_from_DataCite
import csv
from csv import writer
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from csv import DictReader


def save_html_file(url, name):
    response = requests.get(url)
    html_content = response.text
    file_name = name+".html"
    with open(file_name, 'w', encoding="utf-8") as f:
        f.write(html_content)
        
def parse_html(doi):
    print(doi)
    url = doi.replace("/", "")+'.html'
    HTMLFile = open(url, "r")
    index = HTMLFile.read()
    soup = BeautifulSoup(index, 'lxml')
    
    strong_element = soup.find('strong', text='Selected Applications:')
    if strong_element == None:
        strong_element = soup.find('strong', text='Applications')
    if strong_element == None:
        strong_element = soup.find('strong', text='Instrument applications')
        print(strong_element)
    if strong_element != None:
        ul_element = strong_element.find_next('ul')
        li_elements = ul_element.find_all('li')

        for li in li_elements:
            print(li.text.strip().replace("\n", " "))
    
    table = soup.find('table')
    table_rows = table.find_all('tr')
    fortune = []
    for tr in table_rows:
        td = tr.find_all('td')
        row = [i.text for i in td]
        fortune.append(row)
    fortune = pd.DataFrame(fortune)
    print(fortune)

def retrieve_instruments_metadata():
    file = open("instruments_metadata.csv", "a", encoding="utf-8", newline='')
    writer = csv.writer(file)
    writer.writerow(["doi", "name", "description", "content_url", "creator_id", "creator_name", "related_paper", "references"])
    
    data = get_instruments_from_DataCite()
    instruments = data['instruments']['nodes']
 
    for i in instruments:
        related_papers = []
        references = []
        
        relatedIdentifiers = i['relatedIdentifiers']
        
        for paper in relatedIdentifiers:
            if paper['relationType']=='IsDescribedBy':
                related_papers.append(paper['relatedIdentifier'])
                
            if paper['relationType']=='References':
                references.append(paper['relatedIdentifier'])
        
        if len(related_papers) > 0:
            save_html_file(i['url'], i['doi'].replace("/", ""))
            print(i['doi'])
            writer.writerow([
                    i['doi'],
                    i['titles'][0]['title'],
                    i['descriptions'][0]['description'],
                    i['url'],
                    i['creators'][0]['id'],
                    i['creators'][0]['name'],
                    related_papers,
                    references
                ])
                
def retrieve_instruments_specifications():
    file = open("instruments_metadata.csv", "r", encoding="utf-8")
    csv_dict_reader = DictReader(file)
    for i in csv_dict_reader:
        parse_html(i['doi'])
    

def main():
    #retrieve_instruments_metadata()
    retrieve_instruments_specifications()
    #save_html_file("https://www.helmholtz-berlin.de/pubbin/igama_output?modus=einzel&sprache=en&gid=2127", "PEAXIS - Combined RIXS and XPS")
    

if __name__ == "__main__":
    main()