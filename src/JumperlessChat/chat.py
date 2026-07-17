import argparse
import pytchat
import serial
import threading
import time
import logging
import sys
import os

from JumperlessChat.handlers import start_term_listen, start_yt_listen, start_twitch_listen, handle_buffer, exit_gracefully



log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.FileHandler('breadboardchat.log'))
log.addHandler(logging.StreamHandler(sys.stdout))
lf = logging.Formatter("%(asctime)s %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
log.handlers[0].setFormatter(lf)


# set up the arg parser, args can be passed to the JumperlessChat binary or the chat.py file directly
parser = argparse.ArgumentParser(prog='JumperlessV5 chat handler', description='Connect JumperlessV5 to your stream chat!')
parser.add_argument('-yt', '--youtubeid', help='connect to a YouTube stream, provide the ID portion of the URL')
parser.add_argument('-l',  '--local', help='run a local prompt for testing and control', action='store_true')
parser.add_argument('-D',  '--device', help='specify the serial device to use (normally /dev/ttyACM2)')
parser.add_argument('-b',  '--bypass', help='bypass the ACL in the local session', action='store_true')
parser.add_argument('-t',  '--twitchchannel', help='provide a twitch channel to connect to', action='store_true')

args = parser.parse_args()


def main():

    # set up the pytchat handle if a youtube video id was provided
    chathandle = None if not args.youtubeid else pytchat.create(args.youtubeid)
    twitch = None if not args.twitchchannel else True
    # grab the tty device, this may need to be changed depending on your configuration
    board = serial.Serial(args.device, baudrate=115200)

    # prepare the command buffer and threads for the various command listeners
    buffer = []
    threads = []

    if chathandle:
        threads.append(threading.Thread(target=start_yt_listen, args=(buffer, chathandle, args.youtubeid,)))
    if twitch:
        appid = os.getenv("TTV_APPID")
        auth = os.getenv("TTV_AUTH")
        channel = os.getenv("TTV_CHANNEL")
        if not appid:
            print(f'no TTV_APPID environment variable provided!')
            return
        if not auth:
            print(f'no TTV_AUTH environment variable provided!')
            return
        if not channel:
            print(f'no TTV_CHANNEL environment variable provided!')
            return
        threads.append(threading.Thread(target=start_twitch_listen, args=(appid, auth, channel, buffer,)))

    if args.local:
        if args.bypass:
            log.warning('!!Hang onto yer butts, running local mode with ACL bypass!!')
        threads.append(threading.Thread(target=start_term_listen, args=(buffer, ), kwargs={'bypass': args.bypass}))
    if not args.device:
        log.error(f'Please specify a device with the -D parameter (normally /dev/ttyACM2)')
        sys.exit(1)
    if not chathandle and not args.local and not twitch:
        log.error(f'Please run with a listener flag such as -yt or -l')
        sys.exit(1)

    for t in threads:
        t.start()
        log.debug(f'init thread: {t}')

    while True:
        try:
            time.sleep(.05)
            handle_buffer(buffer, board)
            for t in threads:
                if not t.is_alive():
                    log.error(f'thread has stopped {t}')
                    t.join()
                    sys.exit(0)
        except KeyboardInterrupt:
            break



if __name__ == "__main__":
    main()