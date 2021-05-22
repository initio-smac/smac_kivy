from kivy.app import App
from kivy.clock import Clock

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
    app = App.get_running_app()
    try:
        if request == "request_device_uid":
            headers['Authorization'] = 'smac:smac1'

        if app.ID_DEVICE != "":
            username = app.ID_DEVICE
            password = get_password(username)
            headers['Authorization'] = '{}:{}'.format(username, password)

        req = urequests.request(method, url, data=data, json=json_data, headers=headers)
        res = req.text
        r = req.json()
        if req.status_code == 200:
            print(res)
            print(type(res))
            #r = json.loads(res)
            print(r)
            # r = res
            if request == "request_device_uid":
                return r["id_device"]
            elif request == "request_send_pin":
                #app.open_modalInfo(title="Info", text="PIN Sent to Email Address.")
                #Clock.schedule_once(app.close_modalInfo, 2)
                return (req.status_code, r)
            elif request == "request_verify_pin":
                app.open_modalInfo(title="Info", text="PIN Verified Successfully.\nLogin To Continue")
                #Clock.schedule_once(app.close_modalInfo, 2)
                return (req.status_code, r)
        else:
            print(req.status_code)
            print(res)
            print(request)

            if request == "request_send_pin":
                return (req.status_code, r["error"])
            elif request == "request_verify_pin":
                return (req.status_code, r["error"])
            else:
                if r.get("error", None) != None:
                    print("a")
                    app.open_modalInfo(title="Info", text=r["error"])

        req.close()
    except Exception as e:
        print("urequests error: {}".format(e))
        app.open_modalInfo(title="Info", text="Some error occured")


def req_get_device_id():
    request = "request_device_uid"
    url = SMAC_SERVER + request
    return rest_call(url=url, method="GET", request=request)


