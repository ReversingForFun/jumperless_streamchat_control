import re
import logging
import sys

from JumperlessChat.acl import acl_dict

log = logging.getLogger(__name__)
log.setLevel(logging.WARN)
log.addHandler(logging.FileHandler('breadboardchat.log'))
log.addHandler(logging.StreamHandler(sys.stdout))
lf = logging.Formatter("%(asctime)s %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
log.handlers[0].setFormatter(lf)


# we want mostly valid syntax so we don't clean up the user's command too much
# - convert function name to lowercase,
# - remove any spaces trailing commas in the params
# pattern match examples:
#   !helloworld(a, 2, 3, d)
def parse_to_repl(cmd: string):
    # CMD_PATTERN = r'^!(\w+)\(([\w, -\.]+?)\)$'
    CMD_PATTERN = r'^!(\w+)\((.+?)?\)$'
    matches = re.match(CMD_PATTERN, cmd)
    if matches:
        groups = matches.groups()
        f = groups[0].lower()
        if groups[1]:
            params = groups[1].replace(', ', ',')
        else:
            params = ''
        print(params)
        repl_cmd = f'{f}({params})'
        allowed = test_acl(f, params)
        if allowed:
            log.debug(f'{repl_cmd} passes ACL, adding to buffer')
            return repl_cmd


# test parameters against the ACL dictionary
# parameters that are not in the dictionary should fail the ACL and return false
def test_param(p):

    def isfloat(num):
        try:
            float(num)
            return True
        except ValueError:
            return False

    def isint(num):
        try:
            int(num)
            return True
        except ValueError:
            return False

    # check if our params are addressing default params and split out the important bit accordingly
    if '=' in p:
        p = p.split('=')[1]
    # if our param is not numeric (I.E. a constant) then handle it accordingly
    if not isint(p):
        if not isfloat(p):
            if p in acl_dict['constants']:
                return True
            else:
                log.warning(f'ACL denied constant: {p}')
        else:
            return True
    else:
        return True

    # ensure we fail if neither conditions are met
    return False


# test the whole repl command against the ACL including each sequential parameter
def test_acl(t, i):
    # test if our action is in the ACL and abort early if it is not
    if t in acl_dict['actions']:
        # split the param variable on the comma if we have multiple parameters
        if ',' in i:
            i = i.split(',')
        if t in acl_dict['bypass_actions']:
            log.info(f'bypass parameter ACL action:{t}')
            return True
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


def send_to_jumperless_repl(rawpython: str, board):
    log.debug(f'send_to_jumperless_repl() :: {rawpython}')
    # if it doesn't exist then append the carriage return required to send the command
    if '\r\n' not in rawpython[-2:]:
        rawpython += '\r\n'
    # write the encoded python to the board
    board.write(rawpython.encode('utf-8'))
    # read the incoming buffer until we see our repl command so we know it made it
    resp = board.read_until(rawpython.encode('utf-8')).decode()
    if resp:
        log.info('sent command to jumperless successfully')
        return resp
    else:
        log.error(f'failed to send command to jumperless!\n {resp}')
        return False


# handle messages here, if you want to you can do other things with them before they get to the repl parse function
def message_callback(msg, user, local=False):
    if local:
        if not msg.startswith('!'):
            msg = '!' + msg
    if msg.startswith('!'):
        parsed = parse_to_repl(msg)
        if parsed:
            return parsed