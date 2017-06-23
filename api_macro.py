#!/usr/bin/env python
# -*- coding: utf-8 -*-
import getpass
from argparse import ArgumentParser
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import sys
from pyzabbix import ZabbixAPI, ZabbixAPIException


def log(message, debug):
    if debug:
        print message

def getzapi(server, user, passwd):
    zapi = ZabbixAPI(server)
    zapi.session.verify = False
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    try:
        zapi.login(user, passwd)
        return zapi
    except ZabbixAPIException:
        print "Connection to API failed!"
        print "Please check  zabbix server URL, username and password"
        sys.exit()

def get_opts():
    parser = ArgumentParser(
        usage='%(prog)s -a add | delete | update -g <Group ID> -m <Macros> [ -v <Macros new value> ] '
              '[ -z <Zabbix server URL> ] [ -u <Zabbix user> ] [ -p <Zabbix user password> ] [ -d ]',
        description='This program adds/updates/deletes macros for all hosts in given group',
    )
    parser.add_argument(
        "-a", "--action",
        action="store",
        dest="action",
        choices=['add', 'delete', 'rewrite', 'update'],
        help="""add - adds a macro to hosts that do not have it, does not overwrite existing values; delete - delete
        macroses; rewrite - the same as 'add' but also overwrites existing values; update - updates only values of 
        existing macroses""",
        required=True,
    )
    parser.add_argument(
        "-g", "--group",
        action="store",
        type=int,
        dest="groupid",
        help="ID of the host group",
        required=True,
    )
    parser.add_argument(
        "-m", "--macro",
        action="store",
        dest="newmacro",
        help="User macro. For example {$SNMP_COMMUNITY}",
        required=True,
    )
    parser.add_argument(
        "-v", "--value",
        action="store",
        dest="newvalue",
        help="New value for the macro",
    )
    parser.add_argument(
        "-z", "--zabbix",
        action="store",
        dest="server_url",
        default="https://zabbix.au.syrahost.com",
        help="URL of the Zabbix server. Default value is 'https://zabbix.au.syrahost.com'",
    )
    parser.add_argument(
        "-u", "--user",
        action="store",
        dest="user",
        default="Admin",
        help="Name of the Zabbix user who has permission to change settings. Default  is 'Admin'",
    )
    parser.add_argument(
        "-p", "--pass",
        action="store",
        dest="passwd",
        nargs='?',
        help="Password for the Zabbix user",
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        dest="debug",
        help="Show debug messages",
    )
    args = parser.parse_args()
    if not args.passwd:
        args.passwd = getpass.getpass("Password for " + args.user + ":")
    return args

def main():
    args = get_opts()
    zapi = getzapi(args.server_url, args.user, args.passwd)
    log("Connected to Zabbix API Version %s" % zapi.api_version(), args.debug)

    hosts = zapi.host.get(groupids=[args.groupid])

    if not hosts:
        print "No hosts were found. Wrong group ID or group is empty"
        sys.exit()
    else:
        for host in hosts:
            hostid = host["hostid"]
            hostname = host["host"]
            macroses = zapi.usermacro.get(hostids=[hostid])
            existing = filter(lambda macro: macro['macro'] == args.newmacro, macroses)
            if existing:
                macro = existing[0]
                if args.action == "delete":
                    zapi.usermacro.delete(macro["hostmacroid"])
                    log(
                        'Host: {0} - Deleted macro {1} with value {2}'.format(hostname, macro['macro'], macro['value']),
                        args.debug)
                if args.action == "rewrite" or args.action == "update":
                    log(
                        "Host: {0} - Found existing macro {1} "
                        "with value {2}".format(hostname, macro['macro'], macro['value']), args.debug)
                    zapi.usermacro.update(hostmacroid=macro["hostmacroid"], value=args.newvalue)
                    log(
                        "Host: {0} - Macro {1} updated "
                        "with new value {2}".format(hostname, macro['macro'], args.newvalue), args.debug)
            else:
                if args.action == "add" or args.action == "rewrite":
                    zapi.usermacro.create(hostid=hostid, macro=args.newmacro, value=args.newvalue)
                    log(
                        "Host: {0} - Created new macro {1} "
                        "with value {2}".format(hostname, args.newmacro, args.newvalue), args.debug)

if __name__ == "__main__":
    main()
