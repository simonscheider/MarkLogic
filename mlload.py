#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Schei008
#
# Created:     18-02-2019
# Copyright:   (c) Schei008 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os
import requests
import platform
import subprocess

def loadRDF(data_file, host, port, username, password, collection, databasename = 'Documents'):
        mlcp_path = ''#r"C:\Program Files\MarkLogic\mlcp-9.0.8-bin\mlcp-9.0.8"
        which_script = "mlcp.sh"
        if platform.system() == "Windows":
                which_script = "mlcp.bat"

        mlcp_path = which_script#os.path.join(mlcp_path, "bin", which_script)
        #print mlcp_path

        command_line = "{0} import -username {1} -password {2} -host {3} -port {4} -database {5}  -output_collections {6} " \
                       "-input_file_path {7} -input_file_type RDF -output_uri_prefix '/triplestore/'"


        full_path = os.path.abspath(data_file)
        #if platform.system() == "Windows":
            #full_path = "/" + full_path.replace("\\", "/")
        run_line = command_line.format(mlcp_path, username, password, host,
                                       port, databasename,  collection,
                                       full_path)
        print run_line
        os.system(run_line)


def getmlcp_path():
        if platform.system() == "Windows":
            for path in os.environ["PATH"].split(os.pathsep):
                full_path = os.path.abspath(os.path.join(path, "mlcp.bat"))
                if os.path.exists(full_path):
                    return full_path
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                full_path = os.path.abspath(os.path.join(path, "mlcp.sh"))
                if os.path.exists(full_path):
                    return full_path
        return None
def main():
    loadRDF('C:\\Users\\schei008\\Documents\\github\\MarkLogic\\OSMTypes.ttl', 'localhost', '8000', 'simon', '$28*Mfrh', 'osm')

if __name__ == '__main__':
    main()
