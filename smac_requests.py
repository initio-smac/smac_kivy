from kivy.app import App

try:
    import urequests
except:
    import requests as urequests

import time
import json

SMAC_SERVER = "https://smacsystem.com/smacapi/"
REQ_HEADERS = {'Accept': 'application/json',
               'content-type': 'application/json'
               }

def get_password(username):
    try:
        print(username)
        #print(datetime.now(tz=timezone.utc))
        dt = int(time.time())
        du = 50
        password = dt - du

        print(password)
        return str(password)
    except Exception as e:
        print("get password err: {}".format(e) )

def rest_call(url, method, request, data={}, json_data={}, headers=REQ_HEADERS):
    try:
        if request == "request_device_uid":
            headers['Authorization'] = 'smac:smac1'

        app = App.get_running_app()

        if app.ID_DEVICE != "":
            username = app.ID_DEVICE
            password = get_password(username)
            headers['Authorization'] = '{}:{}'.format(username, password)

        req = urequests.request(method, url, data=data, json=json_data, headers=headers)
        res = req.text

        if req.status_code == 200:
            print(res)
            print(type(res))
            r = json.loads(res)
            print(r)
            # r = res
            if request == "request_device_uid":
                return r["device_id"]

        else:
            print(req.status_code)
            print(res)
        req.close()
    except Exception as e:
        print("urequests error: {}".format(e))


def req_get_device_id():
    request = "request_device_uid"
    url = SMAC_SERVER + request
    return rest_call(url=url, method="GET", request=request)


