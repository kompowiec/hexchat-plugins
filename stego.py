import hexchat
import re

__module_name__ = "StegoIRC"
__module_author__ = "ChatGPT"
__module_version__ = "1.0"
__module_description__ = "Steganography for IRC"

# Define the color scheme or key
COLORS = {
        "a": "\x03\x0300",
        "b": "\x03\x0301",
        "c": "\x03\x0302",
        "d": "\x03\x0303",
        "e": "\x03\x0304",
        "f": "\x03\x0305",
        "g": "\x03\x0306",
        "h": "\x03\x0307",
        "i": "\x03\x0308",
        "j": "\x03\x0309",
        "k": "\x03\x0310",
        "l": "\x03\x0311",
        "m": "\x03\x0312",
        "n": "\x03\x0313",
        "o": "\x03\x0314",
        "p": "\x03\x0315",
        "q": "\x03\x0300,01",
        "r": "\x03\x0300,02",
        "s": "\x03\x0300,03",
        "t": "\x03\x0300,04",
        "u": "\x03\x0300,05",
        "v": "\x03\x0300,06",
        "w": "\x03\x0300,07",
        "x": "\x03\x0300,08",
        "y": "\x03\x0300,09",
        "z": "\x03\x0300,10"
}

def encode_message(message, cover_message):
    encoded = ""
    is_color = False
    cover_idx = 0

    for char in message:
        if char == "\x03":
            is_color = True
        elif is_color:
            is_color = False
        elif char in COLORS:
            if cover_idx < len(cover_message):
                encoded += COLORS[char] + cover_message[cover_idx]
                cover_idx += 1
            else:
                encoded += COLORS[char] + char
        else:
            encoded += char
    return encoded

# Command to encode a message
def encode_command(word, word_eol, userdata):
    if len(word) < 3:
        hexchat.prnt("Usage: /encode_message <cover_message> <message>")
        return hexchat.EAT_ALL
    cover_message = word[1]
    message = ' '.join(word_eol[2:])
    encoded_message = encode_message(message, cover_message)
    hexchat.command("say {}".format(encoded_message))
    try:
        if len(COLORS) < len(cover_message):
            raise ValueError("Cover message is longer than the key")
        encoded_message = encode_message(message, cover_message)
        hexchat.command("say {}".format(encoded_message))  # Only output the encoded message
    except ValueError as e:
        hexchat.prnt(str(e))  # Print the error message in HexChat
    return hexchat.EAT_ALL

# Hook the encode command to HexChat
def load_plugin():
    hexchat.command("command -python encode /encode_message %s %s")
    hexchat.hook_command("encode_message", encode_command, help="/encode_message <cover_message> <message>: Encode a message")

# Run the plugin
load_plugin()
