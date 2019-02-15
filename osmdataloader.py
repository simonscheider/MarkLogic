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
{'key':'natural', 'value': 'tree'},
{'key':'waterway', 'value': 'all'},
{'key':'power', 'value': 'all'},
{'key':'barrier', 'value': 'all'},
{'key':'amenity', 'value': 'all'}
]

networkfilter= [
{'key': 'highway', 'value': 'residential'}, {'key': 'highway', 'value': 'service'}, {'key': 'highway', 'value': 'track'},
{'key': 'highway', 'value': 'unclassified'},{'key': 'highway', 'value': 'footway'}, {'key': 'highway', 'value': 'path'},
{'key': 'highway', 'value': 'tertiary'},  {'key': 'highway', 'value': 'secondary'}, {'key': 'highway', 'value': 'primary'},
{'key': 'highway', 'value': 'cycleway'},{'key': 'highway', 'value': 'trunk'}, {'key': 'highway', 'value': 'road'},
{'key': 'highway', 'value': 'motorway'}, {'key': 'highway', 'value': 'mortorway_link'},
{'key': 'highway', 'value': 'living_street'}, {'key': 'highway', 'value': 'pedestrian'}, {'key': 'highway', 'value': 'steps'}
]

fieldfilter = [
{'key': 'natural', 'value': '-tree'},
{'key': 'landuse', 'value': 'all'}
]

#Filters out key value pairs that correspond to core concepts
def filter(key, value, filterlist):
    for f in filterlist:
        if f['key'] == key:
            if f['value'][0]=="-" and f['value'][1:] != value:
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
        if  len(value)<30 and len(key)<30:
            if filter(key,value,objectfilter):
                count+=1
                attr = getAttribute(key,value)
                geometrytypes = []
                if cn > 100:
                    geometrytypes.append('point')
                if cw > 100 or  cr  > 100:
                    geometrytypes.append('region')
                constructRDF(graph, key, value,cw,cr,cn, geometrytypes, attr, ccd.ObjectVector)
            if filter(key,value,networkfilter):
                count+=1
                attr = getAttribute(key,value)
                geometrytypes = []
                if cn > 100:
                    geometrytypes.append('point')
                if cw > 100:
                    geometrytypes.append('line')
                constructRDF(graph, key, value,cw,cr,cn, geometrytypes, attr, ccd.NetworkVector)
            if filter(key,value,fieldfilter):
                count+=1
                attr = getAttribute(key,value)
                geometrytypes = []
                if cn > 100:
                    geometrytypes.append('point')
                if cw > 100:
                    geometrytypes.append('region')
                constructRDF(graph, key, value,cw,cr,cn, geometrytypes, attr, ccd.Coverage)


            if count == 40:
                break
    graph.serialize(destination='OSMTypes.ttl',format='turtle')


def getAttribute(key,value):
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

def constructRDF(graph, key, value,cw,cr,cn, geometrytypes, attr, ccdd):
    for t in geometrytypes:
        for a in attr:
            if t == 'point' :
                gdt = ccd.PointDataSet
            if t == 'region':
                gdt = ccd.RegionDataSet
            if t == 'line':
                gdt = ccd.LineDataSet
            graph.add(( osmtypes[key+"-"+value+"-"+t+"-"+a], RDF.type, RDFS.Class))
            graph.add(( osmtypes[key+"-"+value+"-"+t+"-"+a], RDFS.label, Literal("OSM " +key.replace("_", " ")+" "+value.replace("_", " ")+" " +t+" "+a)))
            graph.add(( osmtypes[key+"-"+value+"-"+t+"-"+a], RDFS.subClassOf,ccdd))
            graph.add((osmtypes[key+"-"+value+"-"+t+"-"+a],ccd.ofDataSet,  osmtypes[key+"-"+value+"-"+t]))
            graph.add((osmtypes[key+"-"+value+"-"+t], RDFS.subClassOf,  gdt))
            graph.add(( osmtypes[key+"-"+value+"-"+t], RDFS.label, Literal("OSM " +key+" "+value+" " +t)))
            graph.add(( osmtypes[key+"-"+value+"-"+t], RDFS.subClassOf,osmtypes[key+"-"+value]))
            graph.add(( osmtypes[key+"-"+value], RDFS.label, Literal("OSM " +key+" "+value)))







def main():
    getPopularTagsasRDF()

if __name__ == '__main__':
    main()
