# jumperless_streamchat_control

Some code to control a jumperless breadboard through stream chat commands

# Install

clone the repo, configure a virtual environment with `python -m venv ./venv` and activate it with `source ./venv/bin/activate`

install the requirements with `pip install -r requirements.txt`

# Run

run `jumperlesschat` which should be on the venv PATH or run `python chat.py` with at least one following service options AND the -D flag with the path to the REPL serial device from your jumperless (typically the third serial device)

```
usage: JumperlessV5 chat handler [-h] [-D DEVICE] [-l] [-b] [-yt YOUTUBEID] [-t]

Connect JumperlessV5 to your stream chat!

options:
  -h, --help            show this help message and exit
  -D, --device DEVICE   specify the serial device to use (normally /dev/ttyACM2)
  -l, --local           run a local prompt for testing and control
  -b, --bypass          bypass the ACL in the local session
  -yt, --youtubeid YOUTUBEID
                        connect to a YouTube stream, provide the ID portion of the URL
  -t, --twitchchannel   connect to the twitch API with token in environment
```

# Usage

[JumperlessV5 API Reference](https://jumperless-docs.readthedocs.io/en/latest/09.5-micropythonAPIreference/)

The Jumperless Streamchat application can be used with a local terminal prompt input, connected to a youtube livestream chat, or connected to Twitch chat. All three can be done simultaneously simply ensure you have the correct environment variables set and then pass the required parameters at runtime.

## Connecting to Twitch
Follow the directions [here](https://dev.twitch.tv/docs/authentication/register-app/) to register a twitch app, ensure the `OAuth Redirect URLs` is set to `http://localhost:17563`

export your twitch AppID, API key and Channel name to the following environment variables prior to launching the application
```
TTV_APPID={client_id}
TTV_AUTH={client_secret}
TTV_CHANNEL={channel_name}
```

Launch the application with the -t flag

## Connecting to Youtube
Considerably easier, simply pass the ID of a youtube livestream to the -yt flag like so:

`jumperlesschat -yt '5ZSY4MIg0Iw' -D /dev/ttyACM2`

## Command Syntax:

chat commands start with an exclamation point `!` and are followed by the function and parameters as specified in the jumperless documentation.

actions can be mostly any function from the jumperless micropython API

refer to the `available_commands.txt` file to see a complete list of allowed functions, constants, and rows.

### Syntax Examples:
#### connect GND to row 1
`!connect(GND, 1)`

#### disconnect TOP_RAIL from row 5
`!disconnect(T_RAIL, 5)`

#### connect BOTTOM_RAIL to row 6
`!connect(6, B_RAIL)`

#### connect row 7 to TOP_RAIL
`!connect(7,TOP_RAIL)`

#### disconnect T_RAIL from all, the `-1` all connections constant can be disabled via ACL
`!connect(T_RAIL, -1) `

### What if I want to restrict chat to certain features or something?

there is a dictionary in the acl.py which will allow any item within to be handled by the jumperless via chat commands. If you wish to prevent a certain function, constant, or row from being used then be sure to remove it from the acl definition
