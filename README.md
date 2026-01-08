# jumperless_streamchat_control
Some code to control a jumperless breadboard through stream chat commands

JumperlessV5: https://jumperless-docs.readthedocs.io/en/latest/

# Syntax:

chat commands start with an exclamation point `!` and are followed by the `{action}{node}-{node}` formatted command

actions can be mostly any function from the jumperless micropython API

refer to the `acl.py` file to see a complete list of allowed functions, constants, and rows.

## Syntax Examples:
### connect GND to row 1
`!connect(GND, 1)`

### disconnect TOP_RAIL from row 5
`!disconnect(T_RAIL, 5)`

### connect BOTTOM_RAIL to row 6
`!connect(6, B_RAIL)`

### connect row 7 to TOP_RAIL
`!connect(7,TOP_RAIL)`

### invalid - by default the `-1` all connections is disabled via ACL
`!connect(T_RAIL, -1) `

# how to run

currently it's two functions:

`start_term_listen()` - takes input from the terminal as if it was a chat command, you know, for debugging

`start_chat_listen("tFMVXBqy6nU")` - pass it a youtube stream ID and every message will be parsed every X seconds for commands

## What if I want to restrict chat to certain features or something?

there is a dictionary in the acl.py which will allow any item within to be handled by the jumperless via chat commands. If you wish to prevent a certain function, constant, or row from being used then be sure to remove it from the acl definition
