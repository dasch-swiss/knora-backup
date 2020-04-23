import argparse
import Repository
from Repository import Config
from Repository import Repository
import logging


def parseArgs():
    parser = argparse.ArgumentParser(description="back-up and restore tool.")
    parser.add_argument("-t", "--target", help="target setup (utility feature to set `graphdb` and `repoId` at once, requires editing config file)", type=str)
    parser.add_argument("-g", "--graphdb", help="Server running GraphDB repository", type=str)
    parser.add_argument("-r", "--repoId", help="name of the repoId to dump", type=str)
    parser.add_argument("-u", "--user", help="GraphDB username (add gibberish if none)", type=str, required=True)
    parser.add_argument("-p", "--pwd", help="GraphDB password (if not provided, will prompt for password)", type=str)
    parser.add_argument("-f", "--folder", help="data folder to write dump files (default: `data`)", default="data", type=str)
    parser.add_argument("-d", "--dataonly", help="upload data (skip base and ontologies)", action='store_true', default=False)
    parser.add_argument("-m", "--merge", help="merge base ttl files into trig before restore", action='store_true', default=False)
    parser.add_argument("-s", "--store", help="store: wipe-out and restore", action='store_true', default=False)
    # todo:
    # parser.add_argument("-e", "--exclude", help="project to exclude", type=str)
    # parser.add_argument("-o", "--only", help="limit to a single project", type=str)

    parser.add_argument("-q", "--quiet", help="no confirmation check", action='store_true', default=False)
    parser.add_argument("-v", "--verbose", help="increased verbosity", action='store_true', default=False)

    args = parser.parse_args()

    return args


def main():
    args = parseArgs()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = Config.Config(args)

    repository = Repository.Repository(config)

    if (args.merge):
        repository.merge()
    if (args.store):
        repository.restore()


if __name__ == "__main__":
    main()
