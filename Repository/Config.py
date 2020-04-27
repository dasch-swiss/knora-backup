from collections import namedtuple
import sys
import getpass
import os

Target = namedtuple('Target', ['server', 'repoId'])

targets = dict(
    local=Target('http://localhost:7200', 'knora-test'),
    localunil=Target('http://db-local.unil.ch:8888', 'knora-test'),
    junipero=Target('http://junipero.unil.ch:9200', 'knora-test'),
    sipipv=Target('http://db-sipipv.unil.ch', 'knora-test'),
    unil=Target('http://knora.unil.ch:7200', 'knora-prod')
)


class Config:
    """
    Configuration for Repository
    """

    def __init__(self, args):
        """
        constructor with a predefined target
        :param target:
        :param user:
        :param pwd:
        """

        if args.target:
            self.target = targets[args.target]
        else:
            assert (args.graphdb and args.repoId), "check your args: specify either a target or (a graphdb and a repoId)"
            self.target = Target(args.graphdb, args.repoId)

        self.user = args.user

        self.pwd = args.pwd
        if not args.pwd:
            self.pwd = getpass.getpass()

        assert os.path.isdir(args.folder), "data folder does not exist (`{}`)".format(args.folder)
        self.folder = args.folder

        self.args = args


def test():
    """
    - config should have a target or a graphdb and a repoId"
    - target should be in the target list

    :return:
    """


if __name__ == "__main__":
    test()
