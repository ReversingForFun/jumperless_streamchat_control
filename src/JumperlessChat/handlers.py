import logging
import sys
import threading
import time
import asyncio
import json
import re

from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from JumperlessChat.cmdparser import send_to_jumperless_repl, message_callback

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.FileHandler('breadboardchat.log'))
log.addHandler(logging.StreamHandler(sys.stdout))
lf = logging.Formatter("%(asctime)s %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
log.handlers[0].setFormatter(lf)

killproc = threading.Event()


# iterate through the buffer of commands and warn us if there are more than 15 pending
def handle_board(buffer, board):
    while not killproc.is_set():
        log.debug('in handle_buffer')
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
        time.sleep(.2)


# listen to a pytchat handle and process the input
# messages will get sent to the message_callback parser prior to getting formatted for REPL
def youtube_chat(buffer, handle):
    log.debug('in yt listener')
    log.info('Python YTChat connected!')
    while not killproc.is_set():
        log.debug('handle.is_alive(True)')
        try:
            if handle.is_alive():
                for c in handle.get().sync_items():
                    json_data = json.loads(c.json())
                    msg = json_data.get('message', '')
                    usr = json_data.get('author').get('name')

                    log.info(f'\n{usr}:  {msg}')
                    if msg:
                        buffer.append(message_callback(msg, usr))
                killproc.wait(0.25)
        except Exception as e:
            log.debug(f'Exception: {e}')
            handle.terminate()
            exit_gracefully('youtube_chat')


# await coroutine for twitch API, establishes connection with parameters and sets up callbacks for certain events
async def await_twitch(appid, appsecret, channel, buffer):
    log.debug('in twitch listener')

    # on_message callback to append message and user to the buffer after being parsed
    async def on_message(msg: ChatMessage):
        if msg:
            log.info(f'{msg.user.name}: {msg.text}')
            buffer.append(message_callback(msg.text, msg.user.name))

    # on_ready callback to connect to the twitch channel when the chatbot is ready
    async def on_ready(ready_event: EventData):
        log.info(f'\npyTwitchAPI handler ready, connecting to {channel}')
        await ready_event.chat.join_room(channel)

    # twitchAPI scope is set here. bot only needs read permissions unless we decided to chat back later
    scope = [AuthScope.CHAT_READ]

    # create the twitch object with our appid and secret, do some authentication
    twitch = await Twitch(appid, appsecret)
    auth = UserAuthenticator(twitch, scope)
    token, refresh_token = await auth.authenticate()
    await twitch.set_user_authentication(token, scope, refresh_token)

    # set up the Chat object and register our event callbacks then start the chat listener
    chat = await Chat(twitch)
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.start()


# non-async wrapper function to allow threaded usage
def twitch_chat(*args):
    twitch_coroutine = await_twitch(*args)
    asyncio.run(twitch_coroutine)
    if killproc.is_set():
        exit_gracefully('twitch_chat')


# listen to a prompt session and process the input
# messages will get sent to the message_callback parser prior to getting formatted for REPL
def term_chat(buffer, bypass=False):
    log.debug('in term listener (bypasss={bypass})')
    session = PromptSession()
    while not killproc.is_set():
        try:
            with patch_stdout():
                msg = session.prompt('jumperless> ')
                if msg:
                    log.info(f'TERM:  {msg}')
                    if re.fullmatch(r'[qQ]uit|[eE]xit', msg):
                        exit_gracefully()
                    buffer.append(message_callback(msg, 'TERM', local=True, insecure=bypass))
            killproc.wait(0.05)
        except KeyboardInterrupt:
            exit_gracefully('term_chat')


def exit_gracefully(callee):
    log.debug(f'in exit_gracefully from {callee}')
    killproc.set()
    return