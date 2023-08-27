from api_calls import api_request
#import fitz
import spacy
nlp1 = spacy.load(r"./output/model-best")
import requests

def save_html_file(url, name):
    response = requests.get(url)
    html_content = response.text
    file_name = name+".html"
    with open(file_name, 'w', encoding="utf-8") as f:
        f.write(html_content)

def get_pdf_file(doi):
    url = 'https://api.unpaywall.org/v2/'+doi+'?email=hariskmohammadk@gmail.com'
    print(url)
    pdf_urls=[]
    title=''
    r=''
    r = api_request(url).json()
   
    if 'HTTP_status_code' in r:
        return ''
    if 'best_oa_location' in r and r['best_oa_location']!=None and 'url_for_pdf' in r['best_oa_location'] and r['best_oa_location']['url_for_pdf']!=None:
        pdf_urls.append(r['best_oa_location']['url_for_pdf'])
        title= r['title']

    if 'first_oa_location' in r and r['first_oa_location']!=None and 'url_for_pdf' in r['first_oa_location'] and r['first_oa_location']['url_for_pdf']!=None:
        pdf_urls.append(r['first_oa_location']['url_for_pdf'])
        title= r['title']

    if 'oa_locations' in r and r['oa_locations']!=None:
        for i in r['oa_locations']:
            if 'url_for_pdf' in i and i['url_for_pdf']!=None:
                pdf_urls.append(i['url_for_pdf'])
                title= r['title']

    
    if len(pdf_urls)>0:
        print(pdf_urls)
        for pdf in pdf_urls:
            file = api_request(pdf)
            if file!='' and file.status_code==200:
                print("downloading")
                file_name='paper-pdfs/'+doi.replace('/', '')+'.pdf'
                f=open(file_name, 'wb')
                f.write(file.content)
                break
        #file_name='paper-pdfs/'+doi.replace('/', '')+'.pdf'
        #os.rename('paper-pdfs/temp.pdf', file_name)
    
    print('-----')
    #return None
    
def parse_data_from_pdf(doi):
    print('doi', doi)
    filePath='paper-pdfs/'+doi.replace('/', '')+'.pdf'

    doc=''
    try:
        doc = fitz.open(filePath)
    except:
        print('pdf error')

    string = []

    text=''
    for page in doc:
        #print(page)
        text=text+' '+page.get_text().lower()

    text1=text.replace('\n', ' ')
    return text1
    
def identify_entity(text):
    data=[]
    method=[]
    doc = nlp1(text)
    
    for ent in doc.ents:
        ent.text, ent.label_
        if ent.label_=='METH':
            method.append(ent.text)
        if ent.label_=='DATA':
            data.append(ent.text)
            
    return {'method': list(set(method)), 'data': list(set(data))}
    