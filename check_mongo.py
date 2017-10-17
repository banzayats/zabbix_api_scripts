#!/usr/bin/python
import json
import re
import sys
from argparse import ArgumentParser
from subprocess import Popen, PIPE


def get_opts():
    parser = ArgumentParser(
        usage='%(prog)s -t <stats|replica> [ -s <host:port> -u <user> -p <password> ] key [key ...]',
        description='This program gets MongoDB stats',
    )
    parser.add_argument(
        "-t", "--type",
        action="store",
        choices=['stats', 'replica'],
        help="Type of the returned statistics",
        required=True
    )
    parser.add_argument(
        "-s", "--server",
        action="store",
        default="127.0.0.1:27017",
        help="Address/port of Mongo database",
    )
    parser.add_argument(
        "-u", "--user",
        action="store",
        default="admin",
        help="Name of the Mongo user who has permission to view stats. Default is 'admin'"
    )
    parser.add_argument(
        "-p", "--pass",
        action="store",
        dest="passwd",
        nargs='?',
        help="Password for the Mongo user",
    )
    parser.add_argument(
        'keys',
        nargs='+',
        help=' Names / indexes of fields for access to a specific metric'
    )
    args = parser.parse_args()
    if '.' in args.keys[0]:
        args.keys = args.keys[0].split('.')
    args.server = args.server.split(':')
    return args


def main():
    opts = get_opts()
    if opts.type == 'stats':
        mongo_cmd = 'serverStatus'
    else:
        mongo_cmd = 'replSetGetStatus'
    command = (
        '/usr/bin/mongo admin --host {0} --port {1} --username {2} '
        '--password "{3}" --authenticationDatabase admin --quiet '
        '--eval "db.runCommand( {{ {4}: 1}} )"'
    ).format(
        opts.server[0],
        opts.server[1],
        opts.user,
        opts.passwd,
        mongo_cmd
    )
    proc = Popen(command, shell=True, stdout=PIPE)
    status = proc.stdout.read()

    # Cleaning the output so it looked like a valid JSON
    output = re.sub('\s+', '', status)
    output = re.sub("ISODate\((.*?)\)", r"\1", output, flags=re.DOTALL)
    output = re.sub("NumberLong\((.*?)\)", r"\1", output, flags=re.DOTALL)
    output = re.sub("ObjectId\((.*?)\)", r"\1", output, flags=re.DOTALL)
    output = re.sub("Timestamp\((.*?),\d+\)", r"\1", output, flags=re.DOTALL)

    status_json = json.loads(output)
    for i in opts.keys:
        if isinstance(status_json, list):
            i = int(i)
        try:
            result = status_json[i]
        except KeyError:
            print('Check your keys')
            sys.exit(3)
        status_json = result
    print status_json

if __name__ == "__main__":
    main()
