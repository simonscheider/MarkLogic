#-------------------------------------------------------------------------------
# Name:        osmdataloader
# Purpose:      Loads OSM Ontology from tag sources and converts it into RDF using core concept data types
#
# Author:      Schei008
#
# Created:     15-02-2019
# Copyright:   (c) Schei008 2019
# Licence:     MIT
#-------------------------------------------------------------------------------


import requests
from requests import auth
import json
import rdflib
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import RDF, FOAF, RDFS
from rdflib import Namespace

#This is an ontology of cleaned datatypes extracted from OSM tags
osmtypes = Namespace('https://questionbasedanalysis.com/OSMTypes.rdf#')
ccd = Namespace('http://geographicknowledge.de/vocab/CoreConceptData.rdf#')
ada = Namespace('http://geographicknowledge.de/vocab/AnalysisData.rdf#')

def setPrefixes(graph):
    graph.bind('osmt', 'https://questionbasedanalysis.com/OSMTypes.rdf#')
    graph.bind('ccd', 'http://geographicknowledge.de/vocab/CoreConceptData.rdf#')
    graph.bind('ada', 'http://geographicknowledge.de/vocab/AnalysisData.rdf#')


#see https://taginfo.openstreetmap.org/tags
objectfilter = [{'key':'building', 'value': 'all'},
{'key':'natural', 'value': 'tree'}, {'key': 'natural', 'value': 'peak'}, {'key': 'natural', 'value': 'spring'},
{'key':'waterway', 'value': 'all'},
{'key':'power', 'value': 'all'},
{'key':'barrier', 'value': 'all'},
{'key':'amenity', 'value': 'all'}
]

objectattributefilter = ['name'] #If something has a unique name, then its likely to be an object

networkfilter= [
{'key': 'highway', 'value': 'residential'}, {'key': 'highway', 'value': 'service'}, {'key': 'highway', 'value': 'track'},
{'key': 'highway', 'value': 'unclassified'},{'key': 'highway', 'value': 'footway'}, {'key': 'highway', 'value': 'path'},
{'key': 'highway', 'value': 'tertiary'},  {'key': 'highway', 'value': 'secondary'}, {'key': 'highway', 'value': 'primary'},
{'key': 'highway', 'value': 'cycleway'},{'key': 'highway', 'value': 'trunk'}, {'key': 'highway', 'value': 'road'},
{'key': 'highway', 'value': 'motorway'}, {'key': 'highway', 'value': 'mortorway_link'},
{'key': 'highway', 'value': 'living_street'}, {'key': 'highway', 'value': 'pedestrian'}, {'key': 'highway', 'value': 'steps'}
]

fieldfilter = [
{'key': 'natural', 'value': ['tree', 'peak', 'spring']}, #This is how 'negation' is encoded!
{'key': 'landuse', 'value': 'all'}
]

#Filters out key value pairs that correspond to core concepts
def filter(key, value, filterlist):
    for f in filterlist:
        if f['key'] == key:
            if isinstance(f['value'], list) and value not in f['value']: #Handling negations
                return True
            elif f['value']=="all":
                return True
            elif f['value'] == value:
                return True
            else:
                return False

def getPopularTagsasRDF():
    url = 'https://taginfo.openstreetmap.org/api/4/tags/popular?sortname=count_all&sortorder=desc&format=json_pretty'
    results = requests.get(url=url)
    #with open("poposmtags.json", "w") as write_file:
        #json.dump(results.json(), write_file)
    res= results.json()
    tags = res['data']
    count = 0
    graph = rdflib.Graph()
    setPrefixes(graph)
    for t in tags:
        key = t['key']
        value = t['value']
        cw = t['count_ways']
        cr = t['count_relations']
        cn = t['count_nodes']
        attr = getAttributes(key,value)
        geometrytypes = []
        if  len(value)<30 and len(key)<30:
            if filter(key,value,objectfilter) or 'name' in attr:
                count+=1
                if cn > 100:
                    geometrytypes.append('point') #This needs to be improved to know how often a way is a polygon or not.
                if cw > 100 or  cr  > 100:
                    geometrytypes.append('region')
                constructObjectRDF(graph, key, value,cw,cr,cn, geometrytypes, attr)
            if filter(key,value,networkfilter):
                count+=1
                if cn > 100:
                    geometrytypes.append('point')
                if cw > 100:
                    geometrytypes.append('line')
                constructNetworkRDF(graph, key, value,cw,cr,cn, geometrytypes, attr)
            if filter(key,value,fieldfilter):
                count+=1
                if cn > 100:
                    geometrytypes.append('point')
                if cw > 100:
                    geometrytypes.append('region')
                constructFieldRDF(graph, key, value,cw,cr,cn, geometrytypes, attr)
            if count == 40:
                break
    graph.serialize(destination='OSMTypes.ttl',format='turtle')


def getAttributes(key,value):
    url = "https://taginfo.openstreetmap.org/api/4/tag/combinations?key="+key+"&value="+value+"&sortname=together_count&sortorder=desc"
    results = requests.get(url=url)
    #with open("poposmtags.json", "w") as write_file:
        #json.dump(results.json(), write_file)
    res= results.json()
    tags = res['data']
    #print tags
    attr = []
    if tags != [] and tags != None:
        count =0
        for t in tags:
            attr.append(t['other_key'])#+('-'+t['other_value'] if (t['other_value'] != "" or len(t['other_value'])<30) else "")
            count+=1
            if count > 3:
                break

    else:
        attr = ["A"]
    return attr


def constructFieldRDF(graph, key, value,cw,cr,cn, geometrytypes, attr):
     attr.append(key) #the key at the same time denotes the field attribute that holds the field values
     for t in geometrytypes:
        for a in attr:
            if t == 'point' :
                gdt = ccd.PointDataSet
                ccdd = ccd.PointMeasures
            if t == 'region':
                gdt = ccd.RegionDataSet
                ccdd = ccd.Coverage
            constructRDF(graph, key, value,cw,cr,cn, gdt, a, t, ccdd)


def constructObjectRDF(graph, key, value,cw,cr,cn, geometrytypes, attr):
     for t in geometrytypes:
        for a in attr:
            if t == 'point' :
                gdt = ccd.PointDataSet
                ccdd = ccd.ObjectVector
            if t == 'region':
                gdt = ccd.RegionDataSet
                ccdd = ccd.ObjectVector
            constructRDF(graph, key, value,cw,cr,cn, gdt, a, t, ccdd)

def constructNetworkRDF(graph, key, value,cw,cr,cn, geometrytypes, attr):
     for t in geometrytypes:
        for a in attr:
            if t == 'point' :
                gdt = ccd.PointDataSet
                ccdd = ccd.NetworkVector
            if t == 'line':
                gdt = ccd.LineDataSet
                ccdd = ccd.NetworkVector
            constructRDF(graph, key, value,cw,cr,cn, gdt, a, t, ccdd)

def constructRDF(graph, key, value,cw,cr,cn, gdt, a, t, ccdd):
            graph.add(( osmtypes[key+"-"+value+"-"+t+"-"+a], RDFS.label, Literal("OSM attribute "+a +" of " +key.replace("_", " ")+" "+value.replace("_", " ") +" "+t)))
            graph.add(( osmtypes[key+"-"+value+"-"+t+"-"+a], RDF.type,ccdd))
            graph.add((osmtypes[key+"-"+value+"-"+t+"-"+a],ccd.ofDataSet,  osmtypes[key+"-"+value+"-"+t]))
            graph.add((osmtypes[key+"-"+value+"-"+t], RDF.type,  gdt))
            graph.add(( osmtypes[key+"-"+value+"-"+t], RDFS.label, Literal("OSM data set " +key.replace("_", " ")+" "+value.replace("_", " ")+" " +t)))
            graph.add(( osmtypes[key+"-"+value+"-"+t], RDF.type,osmtypes[key+"-"+value]))
            graph.add((osmtypes[key+"-"+value], RDF.type, RDFS.Class))
            graph.add(( osmtypes[key+"-"+value], RDFS.label, Literal("OSM type " +key+" "+value)))
            graph.add(( osmtypes[key+"-"+value],RDFS.comment, Literal(getkeyvalueDescription(key, value))))
            graph.add((osmtypes[key+"-"+value], RDFS.subClassOf, osmtypes[key]))
            graph.add(( osmtypes[key], RDFS.label, Literal("OSM type " +key)))



def getkeyvalueDescription(key, value, lang='en'):
    url = "https://taginfo.openstreetmap.org/api/4/tag/wiki_pages?key="+key+"&value="+value
    results = requests.get(url=url)
    res = results.json()
    for i in res['data']:
        if i['lang']==lang:
            return i['description']
            break





def main():
    getPopularTagsasRDF()

if __name__ == '__main__':
    main()
