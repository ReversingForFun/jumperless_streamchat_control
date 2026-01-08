import pytchat
import serial
import time
import re
import json
import logging
from acl import acl_dict

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.FileHandler('breadboardchat.log'))
lf = logging.Formatter("%(asctime)s %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
log.handlers[0].setFormatter(lf)


board = serial.Serial('/dev/ttyACM2', baudrate=115200)

buffer = []


# we want mostly valid syntax so we don't clean up the user's command too much
# - convert function name to lowercase,
# - remove any spaces trailing commas in the params
# pattern match examples:
#   !helloworld(a, 2, 3, d)
def parse_to_repl(cmd: tuple):
    CMD_PATTERN = r'^!(\w+)\(([\w, -]+?)\)$'
    matches = re.match(CMD_PATTERN, cmd)
    if matches:
        groups = matches.groups()
        f = groups[0].lower()
        params = groups[1].replace(', ', ',')
        repl_cmd = f'{f}({params})'
        allowed = test_acl(f, params)
        if allowed:
            log.debug(f'{repl_cmd} passes ACL, adding to buffer')
            return repl_cmd


# test parameters against the ACL
def test_param(p):
    # check if our params are addressing default params and split out the important bit accordingly
    if '=' in p:
        p = p.split('=')[1]
    # if our param is not numeric (I.E. a constant) then handle it accordingly
    if not p.isnumeric():
        if p in acl_dict['constants']:
            return True
        else:
            log.warning(f'ACL denied constant: {p}')
    # otherwise handle the numeric values as row numbers
    elif int(p) in acl_dict['rows']:
            return True
    else:
        log.warning(f'ACL denied row: {p}')
    # ensure we fail if neither conditions are met
    return False

# test the whole repl command against the ACL
def test_acl(t, i):
    # test if our action is in the ACL and abort early if it is not
    if t in acl_dict['actions']:
        # split the param variable on the comma if we have multiple parameters
        if ',' in i:
            i = i.split(',')
        if not isinstance(i, list):
            return test_param(i)
        else:
            log.debug('testing multiple params')
            tests = []
            for p in i:
                tests.append(test_param(p))
            log.debug(f'tests passed: {tests}')
            if all(tests):
                return True
            log.warning(f'ACL denied param: {t}({i})')
            return False
    else:
        log.warning(f'ACL denied action: {t}({i})')
        return False


def send_to_jumperless_repl(rawpython: str):
    log.debug(f'send_to_jumperless_repl() :: {rawpython}')
    # if it doesn't exist then append the carriage return required to send the command
    if '\r\n' not in rawpython[-2:]:
        rawpython += '\r\n'
    # write the encoded python to the board
    board.write(rawpython.encode('utf-8'))
    # read the incoming buffer until we see our repl command so we know it made it
    resp = board.read_until(rawpython.encode('utf-8')).decode()
    if resp:
        return resp
    else:
        return False

# handle messages here, if you want to you can do other things with them before they get to the repl parse function
def message_callback(msg, user):
    if msg.startswith('!'):
        cmd = (msg)
        parsed = parse_to_repl(cmd)
        if parsed:
            buffer.append(parsed)

# iterate through the buffer of commands and warn us if there are more than 15 pending
def handle_buffer():
    if len(buffer) >= 15:
        log.warning(f'command buffer exceeds threshold: {len(buffer)}')
    if len(buffer) >= 1:
        next_cmd = buffer.pop()
        log.info(f'next cmd: {next_cmd}')
        resp = send_to_jumperless_repl(next_cmd)
        if resp:
            log.debug('sent command to jumperless successfully')
        else:
            log.error(f'failed to send command to jumperless!\n {resp}')


def start_chat_listen(video_id):

    chathandle = pytchat.create(video_id)
    while chathandle.is_alive():
        time.sleep(1)
        for c in chathandle.get().items:
            json_data = json.loads(c.json())
            msg = json_data.get('message', '')
            usr = json_data.get('author').get('name')
            log.info(f'{usr}:  {msg}')
            if msg:
                message_callback(msg, usr)
        handle_buffer()

    board.close()


def start_term_listen():

    print('enter command and press enter:')

    while True:
        msg = input()
        if msg:
            message_callback(msg, 'TERM')
        handle_buffer()

    board.close()


start_term_listen()
# start_chat_listen("")