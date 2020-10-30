import sys
import os
import argparse
import logging
import re

headers = []
headersstate = "in"
graphs = {}
header = open("headers.ttl", "w")
context_regex = re.compile(r"^http://www.knora.org/([^/]+)/([^/]+)/?([^/]+)?$")


def parseArgs():
    parser = argparse.ArgumentParser(description="clean and split triple store dump")
    parser.add_argument("-f", "--file", help="input file, i.e. the trig file dump", type=str)

    args = parser.parse_args()

    return args

def nameOfGraph(line, stripped_line):
    # if we encounter a graph, the the header is over
    if headersstate:
        header.close()
        headersState = False

    # work out a name for the graph
    graph = stripped_line.strip('<> {')
    match = context_regex.match(graph)
    ontoData = match.group(1)
    projectCode = match.group(2)
    projectShortName = "base"
    if match.lastindex == 3:
        projectShortName = match.group(3)
    # file name:
    fileName = "{}_{}_{}.trig".format(ontoData, projectCode, projectShortName)
    # if not done open a file for the graph
    if fileName in graphs:
        return graphs.get(fileName)

    #print("adding graph: "+ fileName)    
    handle = open(fileName, "w")
    graphs[fileName] = handle
    handle.writelines(headers)
    handle.write(line)
    return handle

def main():
    # logging.getLogger("main")
    args = parseArgs()

    handler = "None"

    if not args.file:
        logging.error("you should provide an input file with the '-f' option")
        sys.exit("no input file")

    with open(args.file, "r") as source:
        for line in source:

            # headers
            if line.startswith("@prefix"):
                headers.append(line)
                header.write(line)
                continue

            stripped_line = line.rstrip('} \n')

            # skip empty lines
            if not stripped_line:
                continue
            
            # graph definition
            # line: <http://www.knora.org/data/0116/medframes> {
            #print(line)
            if stripped_line.endswith('{'):
                handler = nameOfGraph(line, stripped_line)
                continue

            # collate multiline definitions
            while not stripped_line.endswith('.'):
                stripped_line = stripped_line +" "+ source.readline().strip()
            else:
                line = stripped_line + '\n'
                
            # write line into its file
            handler.write(line)

    for handler in graphs.values():
        handler.write('}\n')
        handler.close()

if __name__ == "__main__":
    main()