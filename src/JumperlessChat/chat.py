import argparse
import pytchat
import serial
import threading
import time
import logging
import sys

from JumperlessChat.handlers import start_term_listen, start_yt_listen, handle_buffer, exit_gracefully


log = logging.getLogger(__name__)
log.setLevel(logging.WARN)
log.addHandler(logging.FileHandler('breadboardchat.log'))
log.addHandler(logging.StreamHandler(sys.stdout))
lf = logging.Formatter("%(asctime)s %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")
log.handlers[0].setFormatter(lf)


parser = argparse.ArgumentParser(prog='JumperlessV5 chat handler', description='Connect JumperlessV5 to your stream chat!')
parser.add_argument('-yt', '--youtubeid', help='connect to a YouTube stream, provide on the ID portion of the URL')
parser.add_argument('-l',  '--local', help='run a local prompt for testing and control', action='store_true')
args = parser.parse_args()


def main():
    chathandle = None if not args.youtubeid else pytchat.create(args.youtubeid)
    board = serial.Serial('/dev/ttyACM3', baudrate=115200)
    buffer = []
    threads = []

    if chathandle:
        threads.append(threading.Thread(target=start_yt_listen, args=(buffer, chathandle, args.youtubeid,)))
    if args.local:
        threads.append(threading.Thread(target=start_term_listen, args=(buffer,)))
    if not chathandle and not args.local:
        log.error(f'Please run with a listener flag such as -yt or -l')
        sys.exit(0)

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