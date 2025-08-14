
"""
Manage automatics update
"""

import os
from io import BytesIO
import ast
import time
import pycurl
import requests

BACKUP_PATH = '/pydarts/backup'
VERSION_FILE = '/pydarts/VERSION'
BACKUP_SCRIPT = '/pydarts/scripts/Backup.sh'
HEADERS = ["accept: application/json"]
TIMEOUT = 10000

def get_version(logs):
    """
    Return actual version of raspydarts stored in VERSION file
    """

    with open (VERSION_FILE, 'r', encoding="utf-8") as version_file:
        data = version_file.readlines()

    logs.info(f"Version of raspydarts is {data[0].strip()}")

    return data[0].strip()

def set_version(logs, version):
    """
    Update VERSION file with version
    """

    with open(VERSION_FILE, 'w', encoding="utf-8") as version_file:
        version_file.write(f'{version}')
    version_file.close()
    logs.debug(f"Version set : {version}")

def get_list(logs, host, port, actual_version, last=True):
    """
    Get list of availables updates
    If version, only thoose where version > actual_version
    """

    if ISCONNECTED == False:
        return

    url =  f'{host}:{port}/api/v1/updates?last={last}&version={actual_version}'

    output = BytesIO()

    query = pycurl.Curl()
    query.setopt(query.URL, url)
    query.setopt(query.HTTPHEADER, ["accept: application/json"])
    query.setopt(query.CONNECTTIMEOUT, 15)
    query.setopt(query.WRITEFUNCTION, output.write)
    query.setopt(query.FOLLOWLOCATION, True)

    try:
        query.perform()
        query.close()
        logs.debug(f"Get updates list : {output.getvalue().decode('UTF-8')}")
        return ast.literal_eval(output.getvalue().decode('UTF-8'))['response']
    except pycurl.error as exc:
        logs.error(f"Unable to reach {url} ({exc})")

    return None


def download(logs, host, port, filename, expected_size):
    """
    Download file
    """

    if ISCONNECTED == False:
        return

    backup_name = f'{BACKUP_PATH}/{filename}'
    url = f'{host}:{port}/api/v1/updates/{filename}'
    with open(backup_name, 'wb') as downloaded:
        query = pycurl.Curl()
        query.setopt(query.URL, url)
        query.setopt(query.WRITEDATA, downloaded)
        query.setopt(pycurl.HTTPHEADER, HEADERS)
        query.setopt(pycurl.CONNECTTIMEOUT, TIMEOUT)
        query.setopt(pycurl.FOLLOWLOCATION, True)

        try:
            query.perform()
            query.close()
        except: # pylint: disable=bare-except
            pass

    downloaded.close()

    file_size = os.path.getsize(backup_name)
    if file_size != expected_size:
        logs.error(f"{filename} downloaded but size differs from announced \
            ({file_size} vs {expected_size}")
        return False

    logs.debug(f"{filename} correctly downloaded ({file_size} bytes)")
    return True

def get_last(logs, host, port, actual_version):
    """
    Check, download and apply an update
    """

    get = get_list(logs, host, port, last=True, actual_version=actual_version)

    if get is None or (len(get) == 0):
        logs.debug("NO availables update or error")
        return None, None, None

    available_update = get[0]

    return available_update['file'], available_update['full_version'], available_update['size']

def download_update(logs, host, port, update_file, update_size):

    if download(logs, host, port, update_file, update_size):
        return update_file, update_size

    return None, None

def apply_update(logs, file_name, version):
    """
    Apply downloaded update
    """

    os.system(f"{BACKUP_SCRIPT} r {file_name}")

    set_version(logs, version)

    logs.debug(f"{version} restored")

    return get_version(logs)

def send_infos(logs, game, nb_players, options, rpi_version, rpi_serial, action, competition_mode, play_id, version):

    if ISCONNECTED == False:
        return

    if competition_mode:
        mode = 'competition'
    else:
        mode = 'loisir'

    data_1 = {"game": f"{game}", "nb_players":nb_players, "options": f"{options}", \
            "rpi_version": f"{rpi_version}", "rpi_serial": f"{rpi_serial}", "action": f"{action}", \
            "play_id": f"{play_id}", "play_mode": f"{mode}", "version": f"{version}"}
    url= 'http://raspydarts.fr:8080/api/plays'

    headers = {"Content-Type": "application/json", "accept": "*/*"}

    try:
        res = requests.post(url, json=data_1, headers=headers, timeout=(1,1))
        response_code = res.status_code
        logs.debug(f"Response code is {response_code}")
    except Exception as exception:
        logs.error(f"Unable to reach {url}")
        logs.error(f"Exception is {exception}")

def connected_to_the_web():
    try:
        response = requests.get("https://www.google.com/")
        if(response.status_code == 200):                
            return True
    except:
        pass
    return False   

ISCONNECTED = connected_to_the_web()
