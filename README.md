# jumperless_streamchat_control
Some code to control a jumperless breadboard through stream chat commands

JumperlessV5: https://jumperless-docs.readthedocs.io/en/latest/

# Syntax:

chat commands start with an exclamation point `!` and are followed by the `{action}{node}-{node}` formatted command

actions can be one of:
- (`c`)onnect
- (`d`)isconnect

nodes or constants can be:
- (`t`)op_rail
- (`b`)ottom_rail
- (`g`)round
- any row by numbers `1`-`60`

## Syntax Examples:
### connect GND to row 1
`!cg-1`

### disconnect TOP_RAIL from row 5
`!dt-5`

### connect BOTTOM_RAIL to row 6
`!cb-6`

### connect row 7 to TOP_RAIL
`!c7-t`

### invalid - only one constant allowed on either side
`!cg-t `

# how to run

currently it's two functions:

`start_term_listen()` - takes input from the terminal as if it was a chat command, you know, for debugging

`start_chat_listen("tFMVXBqy6nU")` - pass it a youtube stream ID and every message will be parsed every X seconds for commands

## What if I want to restrict chat to certain features or something?

there is a config dictionary used to allow/disallow certain constants or rows. Either set the constant to False or remove the row from the row list to disable them
