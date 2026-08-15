import hexchat

__module_name__ = "auto_on"
__module_version__ = "1.0"
__module_description__ = "Automatyczne ,on po wyłączeniu Ananasika"

TARGET = "Ananasik"

def on_message(word, word_eol, userdata):
    nick = word[0]
    message = word_eol[1]

    print("DEBUG:", repr(nick), repr(message))

    if nick == TARGET and message == "bot wyłączony; nadal zapisuję historię":
        print("=== ANANASIK OFF -> WYSYŁAM ,on ===")
        hexchat.command("say ,on")

    return hexchat.EAT_NONE

hexchat.hook_print("Channel Message", on_message)

print("=== auto_on READY ===")
