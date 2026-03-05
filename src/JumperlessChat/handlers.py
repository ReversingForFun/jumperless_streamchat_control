import re
import json
import logging
import sys
import threading

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from JumperlessChat.cmdparser import send_to_jumperless_repl, message_callback

log = logging.getLogger(__name__)
log.setLevel(logging.WARN)
log.addHandler(logging.FileHandler('breadboardchat.log'))
log.addHandler(logging.StreamHandler(sys.stdout))
lf = logging.Formatter("%(asctime)s %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
log.handlers[0].setFormatter(lf)

killproc = threading.Event()

# iterate through the buffer of commands and warn us if there are more than 15 pending
def handle_buffer(buffer, board):
    if len(buffer) >= 1:
        next_cmd = buffer.pop()
        bonus_cmd = None
        if next_cmd:
            if 'oled_set_pixel' in next_cmd:
                bonus_cmd = 'oled_show()'
            log.info(f'next cmd: {next_cmd}')
            resp = send_to_jumperless_repl(next_cmd, board)
            if resp:
                if bonus_cmd:
                    resp = send_to_jumperless_repl(bonus_cmd, board)
    if len(buffer) >= 15:
        log.warning(f'command buffer exceeds threshold: {len(buffer)}')


# listen to a pytchat handle and process the input
# messages will get sent to the message_callback parser prior to getting formatted for REPL
def start_yt_listen(buffer, handle, video_id):
    log.debug('in yt listener')
    while not killproc.is_set():
        try:
            for c in handle.get().items:
                json_data = json.loads(c.json())
                msg = json_data.get('message', '')
                usr = json_data.get('author').get('name')
                log.info(f'{usr}:  {msg}')
                if msg:
                    buffer.append(message_callback(msg, usr))
            killproc.wait(0.05)
        except AttributeError:
            exit_gracefully()


# listen to a prompt session and process the input
# messages will get sent to the message_callback parser prior to getting formatted for REPL
def start_term_listen(buffer):
    log.debug('in term listener')
    session = PromptSession()
    while not killproc.is_set():
        try:
            with patch_stdout():
                msg = session.prompt('jumperless> ')
                if msg:
                    log.info(f'TERM:  {msg}')
                    if re.fullmatch(r'[qQ]uit|[eE]xit', msg):
                        exit_gracefully()
                    buffer.append(message_callback(msg, 'TERM', local=True))
                killproc.wait(0.05)
        except KeyboardInterrupt:
            exit_gracefully()


def exit_gracefully():
    print('in exit_gracefully')
    killproc.set()
    return