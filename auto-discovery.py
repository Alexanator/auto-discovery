import argparse
import getpass
import json
import requests
requests.packages.urllib3.disable_warnings()
import ssl
import sys
import logging
import schedule
import time
import oyaml as yaml
from urllib import request
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
logger = logging.getLogger('auto-discovery')

sys.tracebacklimit = 1

def do_act(url, data=None, add_headers={}):
    res, headers = "" , {"Content-Type":"application/json", "Accept":"application/json"}
    if len(add_headers) > 0 :
        headers.update(add_headers)
    if len(token) > 0:
        headers.update({"Authorization":"Bearer {}".format(token)})
    ctx=ssl._create_unverified_context()
    ctx.check_hostname, ctx.verify_mode = False, ssl.CERT_NONE
    logger.debug('Trying to get list of vRA machines by API')
    try:
        req = request.Request(url=url, data=data, headers=headers)
        with request.urlopen(req, context=ctx ) as f:
            res = f.read().decode('utf-8')
        logger.debug('Content from vRA obtained successfully')
    except HTTPError as e:
        res = "HTTPError={}".format(str(e.code))
        logger.debug(res)
    return res

def get_token():
    logger.debug('Trying to get bearer token by vRA API')
    try:
        res = json.loads(do_act(args.server+"/identity/api/tokens", '{{"username":"{}","password":"{}", "tenant":"{}"}}'.format(args.username, args.password, args.tenant).encode()))["id"]
        logger.info('Bearer token obtained successfully')
    except:
        logger.error("Can't get token for args: {}".format(args))
        raise
    return res 

def get_descr():
    return  do_act(args.server+"/catalog-service/api/consumer/resources/types/Infrastructure.Machine?page=1&limit=50000")

def get_info(id):
    out = []
    ra = do_act(args.server+"/catalog-service/api/consumer/requests/{}/resourceViews".format(id))
    rv = json.loads(ra)
    for i in rv["content"]:
        res = {}
        if "resourceType" in i and i["resourceType"] == "Infrastructure.Virtual":
            if "description" in i:
                res["description"] = i["description"]
            if "name" in i:
                res["name"] = i["name"]
            if "ip_address" in i["data"]:
                res["ip_address"] = i["data"]["ip_address"]
            if "MachineName" in i["data"]:
                res["MachineName"] = i["data"]["MachineName"]
            out.append(res)
    return out

def check_prom_machines(vra_machine):
    prom_machines = []
    add = True
    with open("/prom_config/prometheus.yml") as file:
        prometheus_file = yaml.load(file, Loader=yaml.FullLoader)
        for job in prometheus_file['scrape_configs']:
            if job['job_name'] == "node-exporter" or job['job_name'] == "windows-exporter":
                for prom_machine in job['static_configs'][0]['targets']:
                    prom_machines.append(prom_machine)
    prom_machines = [s.split(":")[0] for s in prom_machines]
    if vra_machine in prom_machines:
        add = False
    return add

def check_remove(vra_machines):
    prom_machines = []
    to_remove = []
    with open("/prom_config/prometheus.yml") as file:
        prometheus_file = yaml.load(file, Loader=yaml.FullLoader)
        for job in prometheus_file['scrape_configs']:
            if job['job_name'] == "node-exporter" or job['job_name'] == "windows-exporter":
                for prom_machine in job['static_configs'][0]['targets']:
                    prom_machines.append(prom_machine)
    prom_machines = [s.split(":")[0] for s in prom_machines]
    for prom_machine in prom_machines:
        if prom_machine not in vra_machines:
            to_remove.append(prom_machine)
    return to_remove

def check_metrics(vra_machine):
    add = True
    url = "http://"+args.monitoring+":8428/api/v1/series?"
    params = {'match[]' : 'node_cpu_seconds_total{node="' + vra_machine + '"}'}
    r = requests.get(url, params=params).json()

    if r['data'] != []:
        add = False
    return add

def check_exporter(vra_machine):
    add = True
    url = "http://" + vra_machine + ":9100/metrics"
    try:
        r = requests.get(url)
        logger.info('Exporter on ' + vra_machine + ':9100 is responding. Machine can be added to monitoring')
    except:
        logger.warning('Exporter on ' + vra_machine + ':9100 is not responding. Unable add machine to monitoring')
        add = False
    return add

def ping_vra():
    url = args.server
    vra_available = False
    try:
        r = requests.get(url, verify=False)
        if r.status_code == 200:
            vra_available = True
    except:
        vra_available = False
    return vra_available

def add_to_prom_config(to_add):
    with open("/prom_config/prometheus.yml") as file:
        prometheus_file = yaml.load(file, Loader=yaml.FullLoader)
        for machine in to_add:
            for job in prometheus_file['scrape_configs']:
                if machine.find("WINDOWS") == -1:
                    if job['job_name'] == "node-exporter":
                        job['static_configs'][0]['targets'].append(machine + ":9100")
                        logger.info("Added machine to monitoring: " + machine)
                else:
                    if job['job_name'] == "windows-exporter":
                        job['static_configs'][0]['targets'].append(machine.replace('WINDOWS', '') + ":9100")
                        logger.info("Added Windows machine to monitoring: " + machine.replace('WINDOWS', ''))
    with open("/prom_config/prometheus.yml", "w") as file:
        yaml.dump(prometheus_file, file)

def remove_from_prom_config(to_remove):
    with open("/prom_config/prometheus.yml") as file:
        prometheus_file = yaml.load(file, Loader=yaml.FullLoader)
        for machine in to_remove:
            for job in prometheus_file['scrape_configs']:
                if job['job_name'] == "node-exporter" or job['job_name'] == "windows-exporter":
                    if str(machine + ":9100") in job['static_configs'][0]['targets']:
                        job['static_configs'][0]['targets'].remove(machine + ":9100")
                        if job['job_name'] == "windows-exporter": logger.info("Removed windows machine from monitoring: " + machine.replace('WINDOWS', ''))
                        else: logger.info("Removed machine from monitoring: " + machine)
                         
    with open("/prom_config/prometheus.yml", "w") as file:
        yaml.dump(prometheus_file, file)

def gets(par):
    n, i, des = par
    main_stand = ""
    exp_stand = ""
    its = get_info(i) if i else [{"description":des,"name":n,"requestId":None}]
    for info in its: 
        d = info["description"]
        l = list(map(lambda x: str.strip(x), d.split("|"))) if d!=None else []
        host = ""
        for z in l:
            if "cbr.ru" in z:
                host = z
                l.remove(z)
                break
        vra_machine = ""
        out={}
        out["name"] = info["name"]
        out["host"] = host
        out["desc"] = str.strip(" ".join( l ).replace(",","_")).replace("\n"," ").replace("\r"," ")
        out["ip"] = info["ip_address"] if "ip_address" in info else "" 
        
        #Processing Y2 zone
        if args.zone == "dev":
            main_stand = "Y2"
            exp_stand = "QWERTY"
        elif args.zone == "tst":
            main_stand = "Y2 TST"
            exp_stand = "Y2 EXP"
        elif args.zone == "prd":
            main_stand = "Y2 PRD"
            exp_stand = "QWERTY"

        #Work only with Y2-machines (not exp, not k8s, not cluster and not monitoring)
        if (out["desc"].startswith(main_stand) or out["desc"].startswith(exp_stand)) and out["host"].find("k8s") == -1 \
                                        and out["host"].find("exp") == -1 \
                                        and not out["host"].startswith("master") \
                                        and not out["host"].startswith("node") \
                                        and not out["host"].startswith("dn") \
                                        and not out["host"].startswith("monitoring"):
            if out["host"]=="":
                if out["desc"].find("(windows)") != -1:
                #When hostname doesn't exists and OS is Win

                    vra_machine = out["ip"]
                    vra_machines.append(vra_machine)
                    if check_prom_machines(vra_machine) and check_metrics(vra_machine) and check_exporter(vra_machine): to_add.append(vra_machine + "WINDOWS")
                else:
                #When hostname doesn't exists and OS is Unix

                    vra_machine = out["ip"]
                    vra_machines.append(vra_machine)
                    if check_prom_machines(vra_machine) and check_metrics(vra_machine) and check_exporter(vra_machine): to_add.append(vra_machine)
            elif out["desc"].find("(windows)") != -1:
            #When hostname exist and OS is Windows

                vra_machine = out["host"]
                vra_machines.append(vra_machine)
                if check_prom_machines(vra_machine) and check_metrics(vra_machine) and check_exporter(vra_machine): to_add.append(vra_machine + "WINDOWS")
            else:
            #When hostname exist and OS is Unix

                vra_machine = out["host"]
                vra_machines.append(vra_machine)
                if check_prom_machines(vra_machine) and check_metrics(vra_machine) and check_exporter(vra_machine): to_add.append(vra_machine)
    return "" 

args_pr = argparse.ArgumentParser()
args_pr.add_argument("-u", "--username", required=True, type=str, help="user name (required)")
args_pr.add_argument("-p", "--password", required=False, type=str, help="user password")
args_pr.add_argument("-t", "--tenant", required=False, type=str, help="tenant")
args_pr.add_argument("-s", "--server", required=False, type=str, help=" server for connection")
args_pr.add_argument("-m", "--monitoring", required=False, type=str, help=" monitoring server for connection")
args_pr.add_argument("-z", "--zone", required=False, type=str, help="Yggdrasil-2 zone (dev/tst/prd)")
args_pr.add_argument("-q", "--query", type=str, default="*",  help="only items with name have SUBSTR")
args = args_pr.parse_args()

token = ""
token = get_token()
vra_machines = []
to_add = []
info = json.loads(get_descr())
gid = []

def job():
    if ping_vra():
        logger.debug('vRA server is available. Going further...')
        global args, token, info, gid, vra_machines, to_add
        skiped=[]
        added=[]
        gid = list([x["name"], x["requestId"], x["description"]] for x in info["content"] if ((args.query=="*") or (args.query.lower() in x["name"].lower())))
        logger.info('Serching for machines to add or to remove from monitoring...')
        for ll in gid:
            if not (ll[1] in skiped):
                added.append(ll)
                if ll[1]:
                    skiped.append(ll[1])
        with ThreadPoolExecutor(50) as ex:
            ex.map(gets, added)
        to_remove = check_remove(vra_machines)

        logger.debug('vRA machines:' + str(vra_machines))
        logger.debug('Machines to add to prometheus config: ' + str(to_add))
        logger.debug('Machines to remove from prometheus config: ' + str(to_remove))
        if not to_add and not to_remove:
            logger.info('Nothing to do. Everything is up to date')

        if to_add and vra_machines:
            add_to_prom_config(to_add)
            to_add = []

        if to_remove and vra_machines:
            remove_from_prom_config(to_remove)
            to_remove = []

        vra_machines = []
    else:
        logger.error('vRA server is not responding. Prometheus config can not be changed.')

job()