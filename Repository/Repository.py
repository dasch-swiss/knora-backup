import os
import rdflib
import re
import requests
import fnmatch
import time
import logging

base_data_graphs = [
    "http://www.knora.org/data/admin",
    "http://www.knora.org/data/permissions",
    "http://www.knora.org/data/standoff",
    "http://www.knora.org/data/0000/SystemProject",
    "http://www.knora.org/data/standoff"
]

class Repository:
    """
    interact with a DaSCH repository

    the goal is to backup an existing DaSCH triple store
    but to do it in slices and produce one file per slice:
    - one would be the basic data to fire-up knora-api
    - the rests are the data specific to each project
    """

    def __init__(self, config):
        self.config = config
        # current working directory
        self.cwd = os.getcwd()
        # work temp file
        self.file = self.cwd + "/data/{}_{}_{}_{}.ttl"  # potential problem, it means that '_' should not be used in project's short name
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

    def listGraphs(self):
        """
        fetch the list of named graphs
        :return: the list of named graphs
        """
        response = requests.get(
            url="{}/repositories/{}/contexts".format(self.config.target.server,self.config.target.repoId),
            auth=(self.config.user, self.config.pwd)
        )
        response.raise_for_status()
        graphs = response.text.splitlines()
        answer_title = graphs.pop(0)
        if answer_title != "contextID":
            raise Exception("Unexpected response from GraphDB:\n" + response.text)

        self.logger.debug("graphs: {}".format(graphs))
        return graphs


    def download_graph(self, graph, file):
        """
        download a single named graph
        :param graph: named graph to download
        :param file: file to write the data to
        :return: nothing
        """
        self.logger.debug("graph: {}, file: {}".format(graph, file))
        params = {
            "infer": "false",
            "context": "<{}>".format(graph)
        }
        headers = {
            "Accept": "text/turtle"
        }
        url = "{}/repositories/{}/statements".format(self.config.target.server, self.config.target.repoId)

        self.logger.debug("url {}".format(url))
        self.logger.debug("headers {}".format(headers))
        self.logger.debug("params {}".format(params))

        response =  requests.get(
            params=params,
            headers=headers,
            url="{}/repositories/{}/statements".format(self.config.target.server, self.config.target.repoId),
            auth=(self.config.user, self.config.pwd))
        response.raise_for_status()
        with open(file, "wb") as downloaded_file:
            for chunk in response.iter_content(chunk_size=1024):
                downloaded_file.write(chunk)


    def dump(self):
       # output trig file with base (knora base onto and data, permissions, admin)
        base = rdflib.Dataset()
        # list of named graphs
        graphs = self.listGraphs()

        # TODO: add exit switch for a "just dump" option

        # iterate over the graphs
        for prefix_counter, graph in enumerate(graphs):
            # break up the graph name
            context_regex = re.compile(r"^http://www.knora.org/([^/]+)/([^/]+)/?([^/]+)?$")
            match = context_regex.match(graph)
            # TODO: test the case of no match
            ontoData = match.group(1)
            projectCode = match.group(2)
            projectShortName = projectCode
            if match.lastindex == 3:
                projectShortName = match.group(3)
            else:
                projectCode = "-"

            if (graph in base_data_graphs) or (graph.find("onto") > -1):
                # if graph belongs to "base", add it to the base trig file
                self.logger.debug("{} is in base".format(graph))

                # dump graph into a temp file
                thisfile = self.file.format("base", ontoData, projectCode, projectShortName)
                self.download_graph(graph, thisfile)

                graph_parsed = base.graph(graph)
                graph_parsed.parse(source=thisfile, format="turtle")

                base.namespace_manager.bind(prefix="prefix{}".format(prefix_counter), namespace=graph, override=True, replace=True)

            else:
                # the graph doesn't belong to "base": it is a project's data

                # TODO: split apart the lists and the rest of the data

                # dump graph into a turtle file
                thisfile = self.file.format("dump", ontoData, projectCode, projectShortName)
                self.download_graph(graph, thisfile)

        # finally
        base.serialize(destination=os.getcwd()+"/data/base.trig", format="trig")


    def wipe_out(self):
        # ask before wiping out the triple store
        if not self.config.args.quiet:
            prompt = "delete all content of {} on {}? [y]|n ".format(self.config.target.repoId, self.config.target.server)
            answer = input(prompt)
            if not (answer == 'Y' or answer == 'y'):
                self.logger.info("goodbye")
                exit(0)

        # wipe out the triple store
        url = "{}/repositories/{}/statements".format(self.config.target.server, self.config.target.repoId)
        drop_all_response = requests.post(url,
                                          headers={"Content-Type": "application/sparql-update"},
                                          auth=(self.config.user, self.config.pwd),
                                          data="DROP ALL")
        drop_all_response.raise_for_status()
        self.logger.info("Emptied repository.")

    def merge(self):
        # back-up created a set of files {base,dump}_{data,ontology}_{project code}_{project short name}.ttl
        # all the data are uploaded separetely per project
        #
        # create the master graph
        base_graph = rdflib.Dataset()

        # get the files in the data folder, filter the ones starting by `base`
        for filename in fnmatch.filter(os.listdir(self.config.folder), "base*.ttl"):
            # file names look like: dump_data_0001_anything.ttl
            # split to get the project's code `0001` and name `anything`
            elements = filename.split('_')
            project_ex = elements.pop()  # anything.ttl
            project = project_ex.split('.').pop(0)  # anything
            code = elements.pop()  # 0001 or -
            data = elements.pop()  # data or ontology

            # general case
            uri = "http://www.knora.org/{}/{}/{}".format(data, code, project)
            # case of graph without a project
            if code == '-':
                # uri shortened
                uri = "http://www.knora.org/{}/{}".format(data, project)

            prefix = "{}-{}".format(project, data)

            self.logger.debug(
                "merging {} as prefix {} in graph {}".format(filename, prefix, uri))

            graph_parsed = base_graph.graph(uri)
            graph_parsed.parse(
                source="{}/{}".format(self.config.folder, filename), format="turtle")

            base_graph.namespace_manager.bind(
                prefix=prefix, namespace=uri, override=True, replace=True)

        # finally
        base_graph.serialize(destination=os.getcwd() +
                             "/data/base.trig", format="trig")

    def restore(self):
        url = "{}/repositories/{}/statements".format(self.config.target.server, self.config.target.repoId)
        # url = "{}/repositories/{}/statements".format(self.config.target.server, self.config.target.repoId)
        # uri = "http://www.knora.org/data/{}/{}".format(code, project)

        if not self.config.args.dataonly:
            # wipe-out
            self.wipe_out()

            # upload
            start = time.time()
            self.logger.info("uploading base ontologies")

            filename = os.getcwd()+"/data/base.trig"
            self.logger.info("uploading {}".format(filename))

            # upload base
            with open(filename, "r") as file_to_upload:
                file_content = file_to_upload.read().encode("utf-8")

            upload_response = requests.post(url,
                                            headers={"name": "backupbase.trig", "Content-Type": "application/trig"},
                                            auth=(self.config.user, self.config.pwd),
                                            data=file_content)

            upload_response.raise_for_status()
            self.logger.info("uploaded base ontologies in {:d}s".format(int(time.time()-start)))

            # going further?
            if not self.config.args.quiet:
                prompt = "base has been uploaded, you can start knora-api, continue with the projects' data? [y]|n "
                answer = input(prompt)
                if not (answer == 'Y' or answer == 'y'):
                    self.logger.info("goodbye")
                    exit(0)

        # listing projects data

        # get the files in the data folder, filter the ones starting by `dump`
        for filename in fnmatch.filter(os.listdir(self.config.folder), "dump*"):
            # file names look like: dump_data_0001_anything.ttl
            # split to get the project's code `0001` and name `anything`
            elements = filename.split('_')
            project_ex = elements.pop()
            project = project_ex.split('.').pop(0)
            code = elements.pop()

            uri = "<http://www.knora.org/data/{}/{}>".format(code, project)

            with open("{}/{}".format(self.config.folder,filename), "r") as file_to_upload:
                start = time.time()
                self.logger.info("uploading {}".format(uri))

                file_content = file_to_upload.read().encode("utf-8")
                upload_response = requests.post(url,
                                                params={"context": uri},
                                                headers={"Content-Type": "text/turtle"},
                                                auth=(self.config.user, self.config.pwd),
                                                data=file_content)
                upload_response.raise_for_status()
                self.logger.info("uploaded {} in {:d}s".format(uri, int(time.time()-start)))


            self.logger.info("Updating Lucene index...")

            sparql = """
                PREFIX luc: <http://www.ontotext.com/owlim/lucene#>
                INSERT DATA { luc:fullTextSearchIndex luc:updateIndex _:b1 . }
            """
            update_lucene_index_response = requests.post(url,
                                                         headers={"Content-Type": "application/sparql-update"},
                                                         auth=(self.config.user, self.config.pwd),
                                                         data=sparql)
            update_lucene_index_response.raise_for_status()
            self.logger.info("Updated Lucene index.")


def test():
    pass


if __name__ == "__main__":
    test()