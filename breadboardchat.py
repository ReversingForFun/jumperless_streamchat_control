import pytchat
import serial
import time
import re
import json
import logging

log = logging.getLogger(__name__)
board = serial.Serial('/dev/ttyACM0', baudrate=115200)


# set the feature flags to enable/disable the feature
# 'rows' is an array of rows that you want to allow access to
# any row not included cannot be accessed by chat commands
config = {'connect': True,
          'disconnect': True,
          'top_rail': True,
          'bottom_rail': False,
          'gnd': True,
          'clear': False,
          'rows': list(range(1,60))
         }

constants = {'t': 'top_rail',
             'b': 'bottom_rail',
             'g': 'gnd',}

log.debug(f'Enabled rows: {config.get('rows')}')

# regex for splitting the chat command into a tuple
CMD_PATTERN = r'!([cd+])([tgb]|\d+)-([tgb]|\d+)'

def parse_to_board_cmd(cmd: tuple):

    left = cmd[1]
    right = cmd[2]

    # abort if we've got a constant in both left and right parts    
    if left.isalpha() and right.isalpha():
        print('aborting early due to 2 constants')
        return

    # handle (c)onnect and (d)isconnect verbs
    if cmd[0] in ['+', 'c']:
        cmd_str = '+'
    if cmd[0] in ['-', 'd']:
        cmd_str = '-'

    left = test_node(left)        
    right = test_node(right)

    if left and right:
        cmd_str += left + '-' + right + '\n'
        log.debug(f'{cmd_str} | cmd_str')
        board.write(cmd_str.encode('utf-8'))


def test_node(v):
    # handle constant conversion if no numbers present, otherwise test row range and config state
    if v.isalpha():
        # get the jumperless semantic from the constants dict
        v = constants.get(v, None)
        # test if the node is disabled or not
        if not config.get(v):
            log.warning(f'{v} | constant disabled!')
            return None
    else:
        # return if the row is out of range
        if int(v) > 60:
            log.warning(f'{v} | row out of range!')
            return None
        # test if the row is disabled
        if int(v) not in config['rows']:
            log.warning(f'{v} | disabled row!')
            return None
    return v



def start_chat_listen(video_id):

    chathandle = pytchat.create(video_id)

    while chathandle.is_alive():
        time.sleep(1)
        for c in chathandle.get().items:
            msg = json.loads(c.json()).get('message', '')
            print(msg)

            m = re.match(CMD_PATTERN, msg)
            if m.groups():
                cmd_parts = m.groups()
                print(cmd_parts)
                parse_board_cmd(cmd_parts)
    board.close()


def start_term_listen():

    print('enter command and press enter:')

    while True:
        msg = input()
        m = re.match(CMD_PATTERN, msg)
        if m:
            if m.groups:
                parse_to_board_cmd(m.groups())
                msg = None


start_term_listen()
# start_chat_listen("tFMVXBqy6nU")



# Syntax: !{action}{left}-{right}
#             !cg-1 | connect GND to row 1
#             !dt-5 | disconnect TOP_RAIL from row 5
#             !cb-6 | connect BOTTOM_RAIL to row 6
#             !c7-t | connect row 7 to TOP_RAIL
#             !cg-t | invalid - only one constant allowed on either side