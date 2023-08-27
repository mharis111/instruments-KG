import json
from api_calls import get_instruments_from_DataCite, add_instrument_metadata_in_orkg, link_paper_and_instrument, get_datasets_by_doi_from_DataCite
from api_calls import create_paper_in_orkg, get_paper_citations, get_paper_references, add_paper_in_orkg, link_paper_with_dataset, add_dataset_metadata_in_orkg
import csv
from csv import writer
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from csv import DictReader
import ast
from utils import get_pdf_file, parse_data_from_pdf, identify_entity
import re

def get_datasets_compiled_by_instrument(instrument_doi):
    response=get_datasets_by_doi_from_DataCite(instrument_doi)
    if len(response)>0:
        dataset_response=response[0]
        creators=dataset_response["creators"]
        description=dataset_response["descriptions"][0]["description"]
        dataset_id=dataset_response["id"]
        title=dataset_response["titles"][0]["title"]
        dataset_url=dataset_response["url"]
        dataset_related_identifiers=dataset_response["relatedIdentifiers"]

        print(dataset_id)
        print(title)
        print(dataset_url)
        print(description)
        cited_by=''
        for ri in dataset_related_identifiers:
            if ri["relationType"]=="IsCompiledBy":
                print(ri["relatedIdentifier"])
            if ri["relationType"]=="IsCitedBy":
                print(ri["relatedIdentifier"])
                cited_by=ri["relatedIdentifier"]
        return {'doi': dataset_id, 'title': title, 'url': dataset_url, 'description': description, 'creators': creators, 'related_identifiers': dataset_related_identifiers, 'cited_by': cited_by}
    return ''


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
    applications = []
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
            applications.append(li.text.strip().replace("\n", " "))
    
    table = soup.find('table')
    table_rows = table.find_all('tr')
    fortune = []
    for tr in table_rows:
        td = tr.find_all('td')
        row = [i.text for i in td]
        if len(row)>0:
            fortune.append(row)
        #fortune = pd.DataFrame(fortune)
        #print(row)
        #if len(row) > 1:
            #print('row')
            #print(row[0])
    print(fortune)
    print('----------')
    return {'specifications': fortune, 'applications': applications}

def extract_context(text, count, window=1):
    sentences = text.split('. ')

    context_sentences = []
    
    citation_tag = '['+str(count)+']'
   
    for i in range(len(sentences)):
        #matches = re.findall(citation_tag, sentences[i])
        
        #if matches!=None:
            # Add sentences before, after and the current sentence (based on window size)
        if citation_tag in sentences[i]:
            context_sentences.extend(sentences[max(0, i-window):i+window+1])
    
    
    #if len(context_sentences)>0:
        #for i in range(len(sentences)):
            #footnote_pattern = fr'\[{0}\]'.format(count)
            #matches = re.findall(footnote_pattern, sentences[i])
            #if matches!=None:
                #context_sentences.extend(sentences[max(0, i-window):i+window+1])
            
    return ' '.join(context_sentences)
    
    
def locate_reference_in_article(citationsDOI, referenceList, instrument_paper_doi, file_writer, instrument_name):
    count=1
    for rl in referenceList:
        if 'DOI' in rl:
            refDOI=rl['DOI']
            if refDOI == instrument_paper_doi:
                print(count)
                #citation_tag = '['+str(count)+']'
                citation_tag = r'\[(\d+,)*{0}(,\d+)*\]'.format(count)
                text = parse_data_from_pdf(citationsDOI)
                context = extract_context(text, count, window=1)
                response=identify_entity(context)
                print(response)
                print(refDOI)
                print(context)
                if len(context)>0:
                    add_paper_in_orkg(citationsDOI, instrument_name, response['data'], response['method'])
                    file_writer.writerow([instrument_paper_doi, citationsDOI, context])
                #get_pdf_file(refDOI)
        count=count+1
        
        
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
            #save_html_file(i['url'], i['doi'].replace("/", ""))
            print(i['doi'])
            instrument_id=add_instrument_metadata_in_orkg(
                i['doi'], #identifier
                'DOI', #identifierType
                i['url'], #landingPage
                i['titles'][0]['title'], #name
                i['creators'][0]['name'], #owner
                '', #ownerName
                '', #manufacturer
                '', #manufacturerName
                '', #manufacturerIdentifier
                i['descriptions'][0]['description'], #description
                '', #instrumentType
                related_papers, #relatedIdentifier
            )
        for paper in related_papers:
            paper_id=add_paper_in_orkg(paper)
            link_paper_and_instrument(paper_id,instrument_id)
            
        dataset_response=get_datasets_compiled_by_instrument(i['doi'])
        if 'doi' in dataset_response:
            dataset_id=add_dataset_metadata_in_orkg(dataset_response['description'],
            dataset_response['title'],
            dataset_response['doi'],
            instrument_id,
            dataset_response['url'],
            'Dataset',
            '')
            if len(dataset_response['cited_by'])>0:
                paper_id=add_paper_in_orkg(dataset_response['cited_by'])
                link_paper_with_dataset(paper_id, dataset_id)
        #break
            
            
        '''
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
        '''
                
def retrieve_instruments_specifications():
    file = open("instruments_metadata.csv", "r", encoding="utf-8")
    csv_dict_reader = DictReader(file)
    for i in csv_dict_reader:
        parsed_result = parse_html(i['doi'])
        related_paper = ast.literal_eval(i['related_paper'])
        create_paper_in_orkg(
            i['doi'],
            i['name'],
            i['description'],
            i['content_url'],
            i['creator_id'],
            i['creator_name'],
            related_paper, 
            parsed_result
        )
        
def retrieve_instruments_usage():
    file = open("instruments_metadata.csv", "r", encoding="utf-8")
    csv_dict_reader = DictReader(file)
    
    file1 = open("instruments_usage.csv", "a", encoding="utf-8", newline='')
    file_writer = csv.writer(file1)
    file_writer.writerow(["doi", "paper_doi", "sentences"])
    
    for i in csv_dict_reader:
        #retrieve paper DOI describes an instrument
        related_paper = ast.literal_eval(i['related_paper'])
        for doi in related_paper:
            print('paper', doi)
            #get citations of instrument paper
            citations=get_paper_citations(doi).json()
            if 'data' in citations:
                citations=citations['data']
                for c in citations:
                    if 'DOI' in c['citingPaper']['externalIds']:
                        citationsDOI=c['citingPaper']['externalIds']['DOI']
                        #get_pdf_file(citationsDOI)
                        try:
                            references=get_paper_references(citationsDOI)      
                        except:
                            print("error")
                        print('citation', citationsDOI)
                        if 'reference' in references['message']:
                            referenceList=references['message']['reference']
                            locate_reference_in_article(citationsDOI, referenceList, doi, file_writer, i['name'])
                    

def main():
    retrieve_instruments_metadata()
    #retrieve_instruments_specifications()
    #retrieve_instruments_usage()
    
    
    

if __name__ == "__main__":
    main()