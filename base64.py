import base64
import hexchat
import os

__module_name__ = "Base64 File Transfer"
__module_version__ = "1.0"
__module_description__ = "Send and receive files in base64 encoding"

# Change these values to match your preferences
SAVE_DIRECTORY = "C:/HexChat/ReceivedFiles/"

def save_file(filename, data):
    save_path = os.path.join(SAVE_DIRECTORY, filename)
    with open(save_path, "wb") as file:
        file.write(data)
    print("File saved as:", save_path)

def send_file(word, word_eol, userdata):
    if len(word) < 2:
        print("Usage: /sendfile <filename>")
        return hexchat.EAT_ALL

    filename = word[1]
    if not os.path.isfile(filename):
        print("File not found:", filename)
        return hexchat.EAT_ALL

    with open(filename, "rb") as file:
        file_data = file.read()

    encoded_data = base64.b64encode(file_data).decode("utf-8")

    hexchat.command("SAY \x02File transfer: {}\x02".format(os.path.basename(filename)))
    hexchat.command("SAY \x0310[START BASE64]\x03")

    # Split the base64-encoded data into smaller chunks to fit within IRC limits
    chunk_size = 400  # Adjust as needed
    chunks = [encoded_data[i:i+chunk_size] for i in range(0, len(encoded_data), chunk_size)]

    for chunk in chunks:
        hexchat.command("SAY {}".format(chunk))

    hexchat.command("SAY \x0310[END BASE64]\x03")
    print("File sent:", filename)

    return hexchat.EAT_ALL

def process_message(word, word_eol, userdata):
    message = word[1]
    if message.startswith("\x0310[START BASE64]\x03"):
        print("Receiving file...")
        hexchat.command("NOTICE Received file in base64 encoding. Saving...")
        file_data = ""
        while True:
            word = hexchat.recv_irc()
            message = word[1]
            if message.startswith("\x0310[END BASE64]\x03"):
                break
            file_data += message

        try:
            decoded_data = base64.b64decode(file_data)
            filename = "received_file"
            save_file(filename, decoded_data)
        except Exception as e:
            print("Failed to decode and save file:", str(e))

    return hexchat.EAT_NONE

hexchat.hook_command("SENDFILE", send_file, help="/sendfile <filename> - Send a file in base64 encoding")
hexchat.hook_print("Channel Message", process_message)

