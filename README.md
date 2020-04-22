# knora-backup

backup and restore a knora based tripple store.

## back-up

This tool download each graph in a turtle file in the `data` subdirectory, leaves the project data as is and merge the rest in a single trig file.

The result `data` folder looks like:

```
# resulting trig file merge of the below `base_*` turtle files
base.trig
# individual turtle files
base_data_-_admin.ttl
base_data_-_permissions.ttl
base_data_-_standoff.ttl
base_data_0000_SystemProject.ttl
base_ontology_-_knora-admin.ttl
base_ontology_-_knora-base.ttl
base_ontology_-_salsah-gui.ttl
base_ontology_-_standoff.ttl
base_ontology_0001_anything.ttl
base_ontology_<project code>_<project short name>.ttl
# project data
dump_data_0001_anything.ttl
dump_data_<project code>_<project short name>.ttl
```

### invocation

example:

```bash
python knora-backup.py --graphdb http://localhost:7200 --repoId knora-test --user user
```

usage:

```
usage: knora-backup.py [-h] [-t TARGET] [-g GRAPHDB] [-r REPOID] -u USER
                       [-p PWD] [-f FOLDER] [-q] [-v]

knora based repo back-up tool, dump graphs

optional arguments:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        target setup (utility feature to set `graphdb` and
                        `repoId` at once, requires editing config file)
  -g GRAPHDB, --graphdb GRAPHDB
                        Server running GraphDB repository
  -r REPOID, --repoId REPOID
                        name of the repoId to dump
  -u USER, --user USER  GraphDB username (add gibberish if none)
  -p PWD, --pwd PWD     GraphDB password (if not provided, will prompt for
                        password)
  -f FOLDER, --folder FOLDER
                        data folder to write dump files (default: `data`)
  -q, --quiet           no confirmation check
  -v, --verbose         increased verbosity
```

### usual ways

#### vendor dump procedure

The most straightforward way to back-up is to dump the whole repo as instructed by the vendor.  
For examplerer: Instructions for [graphdb](http://graphdb.ontotext.com/documentation/free/backing-up-and-recovering-repo.html?highlight=dump).

#### knora project's AllData

In order to extract a given project, knora has a dedicated route: [/admin/projects/iri/<identifier>/AllData](https://docs.knora.org/paradox/03-apis/api-admin/projects.html#dump-project-data-)

### this way

In some cases, you might want to split projects:

- debug a faulty repo
- test on a part of the whole repo
- reloading all but one project
- mix and match different repos
- edit turtle files

this

## install

- knora-backup requires python 3

- you might want to use [venv](https://docs.python.org/3/library/venv.html)

- clone this project

- install required packages

  ```bash
  pip install -r requirements.txt
  ```

  