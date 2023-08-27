from collections import Counter
import numpy as np
import random
import requests
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import json
from orkg import ORKG, OID # import base class from package
from habanero import Crossref
cr = Crossref()
import time

orkg = ORKG(host="https://incubating.orkg.org/", creds=("", ""))
orkg.templates.materialize_templates(["R566000", "R573091"])
tp = orkg.templates

def api_request(url):
    response=''
    count=0
    while response == '':
        try:
            response = requests.get(url)
            break
        except:
            count=count+1
            if count>5:
                return ''
            print("Connection refused by the server..")
            time.sleep(10)
            continue
    return response
    
def execute_DataCite_query(query):
    _transport = RequestsHTTPTransport(
        url='https://api.datacite.org/graphql',
        use_json=True,
    )

    client = Client(
        transport=_transport,
        fetch_schema_from_transport=True,
    )
    
    query = gql(query)

    return client.execute(query)
    
def get_sensors_list():
    url='https://sensor.awi.de/rest/search/sensor?q=id:/[%5E:]*:[%5E:]*/&f=types.typeName:500&qf=states.itemState/public'
    return api_request(url)
    
def get_sensors_devices(sensor_name):
    url='https://sensor.awi.de/rest/search/sensor?q=id:/[%5E:]*:[%5E:]*/&qf=types.typeName/'+sensor_name+'&qf=states.itemState/public&hits=9999&exclude=identifiers,persons,description,genericType,parameters,events,devices'
    return api_request(url)

def get_device_information(device_id):
    url='https://sensor.awi.de/rest/sensors/item/getDetailedItem/'+device_id+'?includeChildren=true'
    return api_request(url)

def get_datasets_by_doi_from_DataCite(doi):
    doi=f'"{doi}"'
    query="""{
  datasets(query:"""+ doi +""") {
    nodes {
      creators {
        id
        affiliation {
          id
          name
        }
        name
      }
      descriptions {
        description
      }
      id
      url
      titles {
        title
      }
      relatedIdentifiers {
        relatedIdentifier
        relationType
      }
    }
  }
}
"""
    return execute_DataCite_query(query)['datasets']['nodes']

def get_instruments_from_DataCite():
    query="""{
        instruments(first: 50) {
            nodes {
                doi
                url
                titles {
                title
            }
            creators {
            id
            name
           }
            relatedIdentifiers {
                relatedIdentifier
                relationType
            }
            descriptions {
                description
            }
        }
    }
}
"""

    return execute_DataCite_query(query)

def get_gpt_response():
    reponse=openai.Completion.create(
        model="gpt-3.5-turbo",
        prompt="extract entities like data name, instrument name and its purpose and any other entity like method, and also mention their relations. return result in form of triples, where property must be one word without underscores. exclude the triples which mention instrument name in subject: The WANS data were acquired at the E2 flat-cone diffractometer at the BER II reactor of Helmholtz-Zentrum Berlin using a Debye–Scherrer geometry",
        temprature=0.7,
        max_token=256,
        top_p=1,
        frequency_penalty=0,
        presence_penatly=0
    )
    print(reponse['choice'][0]['text'])

def get_paper_citations(doi):
    url='https://api.semanticscholar.org/graph/v1/paper/'+doi+'/citations?fields=externalIds,title'
    return api_request(url)
    
def get_paper_references(doi):
    lookupResult = cr.works(ids=doi)
    #url='https://api.crossref.org/works/'+doi+'/'
    return lookupResult
    

def createClassIfNotExist(id, label):
    findClass = orkg.classes.by_id(id).content
    if ('status' in findClass and findClass['status'] == 404):
        orkg.classes.add(id=id, label=label)


def createPredicateIfNotExist(id, label):
    findPredicate = orkg.predicates.by_id(id).content
    if ('status' in findPredicate and findPredicate['status'] == 404):
        orkg.predicates.add(id=id, label=label)


def createOrFindPredicate(label):
    findPredicate = orkg.predicates.get(q=label, exact=True).content
    if (len(findPredicate) > 0):
        predicate = findPredicate[0]['id']
    else:
        predicate = orkg.predicates.add(label=label).content['id']
    return predicate


def createOrFindResource(label, classes=[]):
    findResource = orkg.resources.get(q=label, exact=True).content
    if (len(findResource) > 0):
        resource = findResource[0]['id']
    else:
        resource = orkg.resources.add(label=label, classes=classes).content['id']
    return resource
    
def add_instrument_metadata_in_orkg(
        identifier,
        identifierType,
        landingPage,
        name,
        owner,
        ownerName,
        manufacturer,
        manufacturerName,
        manufacturerIdentifier,
        description,
        instrumentType,
        relatedIdentifier
    ):
    
    
    instance=tp.metadata_schema_for_instruments(
    label=name,
    identifier=identifier,
    identifiertype=identifierType,
    landingpage=landingPage,
    name=name,
    owner=owner,
    ownername=ownerName,
    manufacturer=manufacturer,
    manufacturername=manufacturerName,
    manufactureridentifier=manufacturerIdentifier,
    description=description,
    instrumenttype=instrumentType,
    relatedidentifier=relatedIdentifier
    )
    
    response=instance.save()
    return response.content["id"]
    
def add_dataset_metadata_in_orkg(
        description,
        title,
        identifier,
        compiledBy,
        landingpage,
        artefacttype,
        location
    ):
    
    
    instance=tp.dataset(
    label=title,
    description=description,
    identifier=identifier,
    compiledby=OID(compiledBy),
    landingpage=landingpage,
    artefacttype=artefacttype,
    location=location
    )
    
    response=instance.save()
    return response.content["id"]
    


def doiLookup(paper):
    if ("doi" in paper['paper']):
        lookupResult = cr.works(ids=paper['paper']['doi'])
        if (lookupResult['status'] == 'ok'):
            paper['paper']['title'] = lookupResult['message']['title'][0]
            if 'published-print' in lookupResult['message']:
                if (len(lookupResult['message']['published-print']['date-parts'][0]) > 0):
                    paper['paper']['publicationYear'] = lookupResult['message']['published-print']['date-parts'][0][0]

                if (len(lookupResult['message']['published-print']['date-parts'][0]) > 1):
                    paper['paper']['publicationMonth'] = lookupResult['message']['published-print']['date-parts'][0][1]
            elif 'created' in lookupResult['message']:
                if (len(lookupResult['message']['created']['date-parts'][0]) > 0):
                    paper['paper']['publicationYear'] = lookupResult['message']['created']['date-parts'][0][0]

                if (len(lookupResult['message']['created']['date-parts'][0]) > 1):
                    paper['paper']['publicationMonth'] = lookupResult['message']['created']['date-parts'][0][1]

            if (len(lookupResult['message']['author']) > 0):
                paper['paper']['authors'] = []
                for author in lookupResult['message']['author']:
                    paper['paper']['authors'].append(
                        {"label": author['given'] + ' ' + author['family']})
    return paper
    
def add_paper_in_orkg(doi):
    
    paper = {
        "paper": {
            "doi": doi,
            "researchField": "R274",
            "contributions": [
                {
                    "name": "Contribution 1",
                }
            ]
        }
    }

    paper = doiLookup(paper)
    response = orkg.papers.add(paper, merge_if_exists=True)
    #paper_contribution = orkg.statements.get_by_subject_and_predicate(subject_id=response.content['id'], predicate_id='P31', size=5, sort='id', desc=False).content
    #contributionId = paper_contribution[0]['object']['id']
    return response.content['id']
    
def link_paper_and_instrument(paperId, instrumentResourceId):
    paper_contribution = orkg.statements.get_by_subject_and_predicate(subject_id=paperId, predicate_id='P31', size=5, sort='id', desc=False).content
    contributionId = paper_contribution[0]['object']['id']
    describesPredicate = createOrFindPredicate(label='describes')
    orkg.statements.add(subject_id=contributionId, predicate_id=describesPredicate, object_id=instrumentResourceId)
    
def link_paper_with_dataset(paperId, datasetResourceId):
    paper_contribution = orkg.statements.get_by_subject_and_predicate(subject_id=paperId, predicate_id='P31', size=5, sort='id', desc=False).content
    contributionId = paper_contribution[0]['object']['id']
    datasetPredicate = createOrFindPredicate(label='dataset')
    orkg.statements.add(subject_id=contributionId, predicate_id=datasetPredicate, object_id=datasetResourceId)

def create_paper_in_orkg(doi,
            name,
            description,
            content_url,
            creator_id,
            creator_name,
            related_papers, 
            parsed_result
        ):
    
    for p in related_papers:
        paper = {
            "paper": {
                "doi": p,
                "researchField": "R274",
                "contributions": [
                    {
                        "name": "Contribution 1",
                    }
                ]
            }
        }

        paper = doiLookup(paper)
        response = orkg.papers.add(paper, merge_if_exists=True)
        paper_contribution = orkg.statements.get_by_subject_and_predicate(subject_id=response.content['id'], predicate_id='P31', size=5, sort='id', desc=False).content
        contributionId = paper_contribution[0]['object']['id']
        
        instrument_id = createOrFindResource(label=name)
        applicationsPredicate = createOrFindPredicate(label='applications')
        descriptionPredicate = createOrFindPredicate(label='description')
        urlPredicate = createOrFindPredicate(label='url')
        creatorPredicate = createOrFindPredicate(label='creator')
        doiPredicate = createOrFindPredicate(label='doi')
        describesPredicate = createOrFindPredicate(label='describes')
        
        print(instrument_id)
        
        literal_id = orkg.literals.add(label=doi, datatype='xsd:url').content['id']
        orkg.statements.add(subject_id=instrument_id, predicate_id=doiPredicate, object_id=literal_id)
        
        if len(description) > 0:
            literal_id = orkg.literals.add(label=description, datatype='xsd:string').content['id']
            orkg.statements.add(subject_id=instrument_id, predicate_id=descriptionPredicate, object_id=literal_id)
            
        if len(content_url) > 0:
            literal_id = orkg.literals.add(label=content_url, datatype='xsd:url').content['id']
            orkg.statements.add(subject_id=instrument_id, predicate_id=urlPredicate, object_id=literal_id)
            
        if len(creator_id)>0 and len(creator_name)>0:
            literal_id = orkg.literals.add(label=creator_id, datatype='xsd:url').content['id']
            orkg.statements.add(subject_id=instrument_id, predicate_id=creatorPredicate, object_id=literal_id)
            
            literal_id = orkg.literals.add(label=creator_name, datatype='xsd:string').content['id']
            orkg.statements.add(subject_id=instrument_id, predicate_id=creatorPredicate, object_id=literal_id)
        
        for row in parsed_result['applications']:
            print(row.strip())
            literal_id = orkg.literals.add(label=row.strip(), datatype='xsd:string').content['id']
            orkg.statements.add(subject_id=instrument_id, predicate_id=applicationsPredicate, object_id=literal_id)
            
        for row in parsed_result['specifications']:
            count=0
            for element in row:
                if count == 0:
                    print('property')
                    print(element.strip())
                    predicateId = createOrFindPredicate(label=element.strip())
                    count=1
                else:
                    print(element.strip())
                    literal_id = orkg.literals.add(label=element.strip(), datatype='xsd:string').content['id']
                    orkg.statements.add(subject_id=instrument_id, predicate_id=predicateId, object_id=literal_id)
        

        orkg.statements.add(subject_id=contributionId, predicate_id=describesPredicate, object_id=instrument_id)
        #print(paper_contribution[0]['object']['id'])
        
def link_paper_and_dataset(doi, instrument_name, data, method):
    
    
    paper = {
        "paper": {
            "doi": doi,
            "researchField": "R274",
            "contributions": [
                {
                    "name": "Contribution 1",
                }
            ]
        }
    }

    paper = doiLookup(paper)
    response = orkg.papers.add(paper, merge_if_exists=True)
    paper_contribution = orkg.statements.get_by_subject_and_predicate(subject_id=response.content['id'], predicate_id='P31', size=5, sort='id', desc=False).content
    contributionId = paper_contribution[0]['object']['id']
        
        
        
    instrumentId = createOrFindResource(label=instrument_name)
    instrumentPredicate = createOrFindPredicate(label='utilized')
    dataPredicate = createOrFindPredicate(label='data')
    methodPredicate = createOrFindPredicate(label='method')
        
    if len(data) > 0:
        dataId = createOrFindResource(label=data[0])
        orkg.statements.add(subject_id=contributionId, predicate_id=dataPredicate, object_id=dataId)
        orkg.statements.add(subject_id=dataId, predicate_id=instrumentPredicate, object_id=instrumentId)
            
    if len(method) > 0:
        methodId = createOrFindResource(label=method[0])
        orkg.statements.add(subject_id=contributionId, predicate_id=methodPredicate, object_id=methodId)
            
            
            
        
        
        
