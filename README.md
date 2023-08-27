# Knowledge Graph Enrichment using Instruments Meta(data)

This repository contains the functionality to retrieve instruments meta(data) from multiple sources, analyze the instrument-related content to discover the instrument usage in research, and publish the extracted information in a knowledge graph.

### Usage

**mine_zenodo_software_packages** and **figshare data extraction** are used to extract the metadata of software packages from zenodo and figshare, respectively. These files also contain the code to download software packages. First the software packages are extracted from these repositories and stored in downloadedFiles.

An ```ACCESS_TOKEN``` needs to set before accessing zenodo REST API which can be done in the **mine_zenodo_software_packages** 

**read_code.py** reads the all software packages and after extracting, parse each .py and .ipynb file one by one and returns the information about used datasets and operations performed on these datasets.

**verifydataset** implements two functions ```download_pdfs``` and ```read_extracted_data```. ```download_pdfs``` downloads the pdfs of articles to make data searching process easy. ```read_extracted_data``` reads the astData and text from pdf and search the datasets and operations informtion in article text.

**validation** file shows the different between the data extracted manually and using AST approach. The files shows the comparison of information retrieved from different scripts, whereas in paper information of 2 scripts is shown due to space.