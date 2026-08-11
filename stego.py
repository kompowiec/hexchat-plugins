import hexchat
import re

__module_name__ = "StegoIRC"
__module_author__ = "ChatGPT"
__module_version__ = "2.0"
__module_description__ = "IRC formatting steganography for HexChat"


# IRC foreground colors 00-15.
#
# We use the 16 standard foreground colors to encode hexadecimal
# nibbles. This gives us a clean 4-bit symbol alphabet.
#
# Each secret byte is represented as two color codes:
#
#     byte 0xAB -> color A + color B
#
# The visible cover text is left unchanged.
#
# This is deliberately not encryption. Anyone who knows the encoding
# scheme can recover the message.

IRC_COLORS = {
    0: "\x0300",
    1: "\x0301",
    2: "\x0302",
    3: "\x0303",
    4: "\x0304",
    5: "\x0305",
    6: "\x0306",
    7: "\x0307",
    8: "\x0308",
    9: "\x0309",
    10: "\x0310",
    11: "\x0311",
    12: "\x0312",
    13: "\x0313",
    14: "\x0314",
    15: "\x0315",
}

COLOR_TO_NIBBLE = {
    value: key for key, value in IRC_COLORS.items()
}


def encode_message(secret, cover):
    """
    Encode secret data into IRC color formatting while preserving
    the visible cover message.

    Each byte of UTF-8 encoded secret data becomes two IRC color
    codes. The color codes are inserted immediately before successive
    cover characters.

    Returns:
        str: IRC-formatted message

    Raises:
        ValueError: if the cover is too short.
    """

    secret_bytes = secret.encode("utf-8")

    # Two color codes are required for every byte.
    required_positions = len(secret_bytes) * 2

    if required_positions > len(cover):
        raise ValueError(
            "Cover message is too short. "
            "The cover needs at least {} characters for this secret."
            .format(required_positions)
        )

    output = []
    cover_index = 0

    for byte in secret_bytes:
        high = (byte >> 4) & 0x0F
        low = byte & 0x0F

        # Encode the two nibbles using IRC colors.
        output.append(IRC_COLORS[high])
        output.append(cover[cover_index])
        cover_index += 1

        output.append(IRC_COLORS[low])
        output.append(cover[cover_index])
        cover_index += 1

    # Append the remainder of the cover unchanged.
    output.append(cover[cover_index:])

    return "".join(output)


def strip_irc_color_codes(message):
    """
    Remove IRC color codes from a message.

    Supports:
        \x03
        \x03NN
        \x03NN,MM

    Returns:
        str: message without IRC color formatting.
    """

    return re.sub(
        r"\x03(?:\d{1,2}(?:,\d{1,2})?)?",
        "",
        message
    )


def decode_message(message):
    """
    Recover the hidden message from IRC color formatting.

    The decoder reads foreground color codes and combines pairs
    of hexadecimal nibbles into bytes.

    Returns:
        str: decoded UTF-8 message

    Raises:
        ValueError: if the embedded data is malformed.
    """

    nibbles = []

    i = 0

    while i < len(message):
        if message[i] != "\x03":
            i += 1
            continue

        i += 1

        # No color number means color reset.
        if i >= len(message):
            break

        # Read foreground color number.
        match = re.match(r"\d{1,2}", message[i:])

        if not match:
            continue

        color_text = match.group(0)
        color = int(color_text)

        i += len(color_text)

        # Background color, if present, is deliberately ignored.
        if i < len(message) and message[i] == ",":
            i += 1

            bg_match = re.match(r"\d{1,2}", message[i:])

            if bg_match:
                i += len(bg_match.group(0))

        if color > 15:
            continue

        nibbles.append(color)

    if len(nibbles) % 2 != 0:
        raise ValueError(
            "Malformed steganographic message: "
            "an incomplete byte was found."
        )

    data = bytearray()

    for i in range(0, len(nibbles), 2):
        byte = (nibbles[i] << 4) | nibbles[i + 1]
        data.append(byte)

    try:
        return bytes(data).decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError(
            "The embedded data is not valid UTF-8."
        )


def encode_command(word, word_eol, userdata):
    """
    /encode_message <cover message> <secret message>
    """

    if len(word_eol) < 3:
        hexchat.prnt(
            "Usage: /encode_message <cover message> <secret message>"
        )
        return hexchat.EAT_ALL

    # word_eol preserves spaces better than word.
    #
    # Syntax:
    # /encode_message cover message | secret message
    #
    # The separator makes it possible to use multi-word cover text.
    arguments = word_eol[1].split("|", 1)

    if len(arguments) != 2:
        hexchat.prnt(
            "Usage: /encode_message <cover message> | <secret message>"
        )
        hexchat.prnt(
            "Example: /encode_message Hello there everyone | attack at dawn"
        )
        return hexchat.EAT_ALL

    cover = arguments[0].strip()
    secret = arguments[1].strip()

    if not cover:
        hexchat.prnt("Error: cover message is empty.")
        return hexchat.EAT_ALL

    if not secret:
        hexchat.prnt("Error: secret message is empty.")
        return hexchat.EAT_ALL

    try:
        encoded = encode_message(secret, cover)
    except ValueError as error:
        hexchat.prnt("Error: {}".format(error))
        return hexchat.EAT_ALL

    hexchat.command("say {}".format(encoded))

    return hexchat.EAT_ALL


def decode_command(word, word_eol, userdata):
    """
    /decode_message <IRC formatted message>
    """

    if len(word_eol) < 2:
        hexchat.prnt(
            "Usage: /decode_message <encoded message>"
        )
        return hexchat.EAT_ALL

    message = word_eol[1]

    try:
        decoded = decode_message(message)
    except ValueError as error:
        hexchat.prnt("Error: {}".format(error))
        return hexchat.EAT_ALL

    hexchat.prnt("Decoded message: {}".format(decoded))

    return hexchat.EAT_ALL


def decode_received(word, word_eol, userdata):
    """
    Automatically inspect incoming IRC messages for hidden data.

    This hook is intentionally passive: it does not modify the
    received message. It only prints a decoded message if IRC
    formatting codes are present.
    """

    message = word_eol[1] if len(word_eol) > 1 else ""

    if "\x03" not in message:
        return hexchat.EAT_NONE

    try:
        decoded = decode_message(message)

        if decoded:
            hexchat.prnt(
                "[StegoIRC] Hidden message: {}".format(decoded)
            )

    except (ValueError, UnicodeDecodeError):
        pass

    return hexchat.EAT_NONE


def load_plugin():
    hexchat.hook_command(
        "encode_message",
        encode_command,
        help="/encode_message <cover> | <secret>"
    )

    hexchat.hook_command(
        "decode_message",
        decode_command,
        help="/decode_message <encoded message>"
    )


load_plugin()
