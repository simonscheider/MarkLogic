#-------------------------------------------------------------------------------
# Name:       mlsparql
# Purpose:      To access and query MarkLogic server
#
# Author:      Schei008
#
# Created:     13-02-2019
# Copyright:   (c) Schei008 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import requests
from requests import auth
import json
import pandas as pd
import rdflib



me = auth.HTTPDigestAuth("simon", "$28*Mfrh")

url = 'http://localhost:8000/v1/graphs/sparql'

prefixes = 'PREFIX db: <http://dbpedia.org/resource/> \
            PREFIX onto: <http://dbpedia.org/ontology/> \
            PREFIX owl: <http://www.w3.org/2002/07/owl#> \
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> \
            PREFIX cts: <http://marklogic.com/cts#> \
            PREFIX dc: <http://purl.org/dc/elements/1.1/>\
             '

""""Firing SPARQL queries against Mark Logic"""

#Fires a query against MarkLogic and returns a Pandas DF
def queryforDF(query):
    headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept':'application/sparql-results+json'}
    results = requests.post(url=url, headers=headers, auth=me, data = {'query': query})
    print results.status_code
    results = results.json()
    #print results

    resultbindings = results['results']['bindings']
    cols =results['head']['vars']
    out = []
    for row in resultbindings:
            item = []
            for c in cols:
                item.append(row.get(c, {}).get('value'))
            out.append(item)

    return pd.DataFrame(out, columns=cols)


#Fires a DESCRIBE or CONSTRUCT query against MarkLogic and returns RDF
def queryforRDF(query, format = 'turtle'):
    if format == 'rdf+xml':
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept':'application/rdf+xml'}
    elif format == 'turtle':
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept':'text/turtle'}
    results = requests.post(url=url, headers=headers, auth=me, data = {'query': query})
    print results.status_code
    rdf = results.content
    #graph = rdflib.Graph()
    #graph.parse(data=rdfxml, format='xml')
    return rdf




""""Firing SPARQL updates against Mark Logic. Creates a new document each time in the graph specified in the update statement. Danger: redundancy """
def update(update, format = 'rdf+xml', permissions=None):
    if format == 'rdf+xml':
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept':'application/rdf+xml'}
    elif format == 'turtle':
        headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept':'text/turtle'}
    d = {'update': update}
    if permissions != None:
        d['perm:rest-writer']= permissions #This will allow you to set permissions for the graph you are updating
    results = requests.post(url=url, headers=headers, auth=me, data =  d)
    print 'successfully updated!' if results.status_code != '400' else 'failure!'
    return results







def main():
    #Examples:
    selectquery = prefixes +''' SELECT DISTINCT ?a \
        WHERE {\
        ?a a owl:Class.\
        ?a rdfs:subClassOf onto:Place.\
        ?a rdfs:label ?l.\
        } LIMIT 10'''
        #FILTER( cts:contains(?l, cts:or-query(("straat", "village"))))\

    #with open('example.rq', 'r') as f:
    #query=f.read()

    print selectquery
    print queryforDF(selectquery)

    describequery = prefixes +''' DESCRIBE ?a \
        WHERE {\
        ?a a owl:Class.\
        ?a rdfs:subClassOf onto:Place.\
        ?a rdfs:label ?l.\
        } LIMIT 10'''
    print describequery
    print queryforRDF(describequery)

    insert = prefixes +''' INSERT DATA \
        {\
        GRAPH <examplegraph> \
        {\
        <http://example./book/> dc:title "ExampleBook"
        }\
        } '''
    print insert
    print update(insert)

    emptygraph =prefixes +'''CLEAR GRAPH <examplegraph> '''
    print update(emptygraph)



if __name__ == '__main__':
    main()
