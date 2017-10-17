#!/usr/bin/env python
import json
import sys
import time
import urllib2

ZBX_URL = ""
USERNAME = ''
PASSWORD = ''
SVC_IDs = 17


def api_request(method, params, auth=None):
    """This function is used for API requests"""
    data = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
        "auth": auth
    }
    req = urllib2.Request(
        ZBX_URL,
        data=json.dumps(data).encode(),
        headers={'Content-type': 'application/json'}
    )
    response = urllib2.urlopen(req)
    result = response.read()
    return json.loads(result)['result']


def get_sla(svc_id, t_from, t_to, auth):
    params = {"serviceids": svc_id, "intervals": [{"from": t_from, "to": t_to}]}
    sla = api_request("service.getsla", params, auth)
    print sla[svc_id]['sla'][0]['sla']
    return sla[svc_id]['sla'][0]['sla']


def main():
    params = {"user": USERNAME, "password": PASSWORD}
    try:
        auth = api_request("user.login", params)
    except Exception, e:
        print str(e)
        sys.exit()
    now = int(time.time())
    week_ago = now - 3600 * 24 * 7
    params = {"serviceids": SVC_IDs, "selectDependencies": "extend"}
    service = api_request("service.get", params, auth)
    l = [get_sla(sub_srv['serviceid'], week_ago, now, auth) for sub_srv in service[0]['dependencies']]
    print(sum(l) / float(len(l)))

if __name__ == "__main__":
    main()
