__module_name__ = "ChaffWinnowHexChat"
__module_version__ = "1.0"
__module_description__ = "Chaff and Winnow for HexChat"

import hashlib
import random
import hexchat
import argparse

class Chaffer:

    def __init__(self, authentication_key, mac_algorithm='sha512'):
        self._authentication_key = authentication_key
        self._mac_algorithm = mac_algorithm

    def authenticate(self, serial, message):
        h = hashlib.new(self._mac_algorithm)
        h.update(f'{serial}{message}{self._authentication_key}'.encode())
        return h

    def chaff(self, serial, count, mac_bytes):
        chaff = []
        for i in range(count):
            chaff.append((serial, random.getrandbits(1), hashlib.sha256(str(random.getrandbits(mac_bytes)).encode()).hexdigest()))
        return chaff

class Decoder:

    def __init__(self, key, mac_algorithm):
        self._serial = 0
        self._chaffer = Chaffer(key, mac_algorithm)

    def authentic(self, serial, bit, mac):
        actual_mac = self._chaffer.authenticate(serial, bit)
        return mac == actual_mac.hexdigest()

class Encoder:

    def __init__(self, key, multiplier, mac_algorithm):
        self._serial = 0
        self._chaffer = Chaffer(key, mac_algorithm)
        self._multiplier = multiplier

    def encode(self, message):
        for bit in bits(message):
            mac = self._chaffer.authenticate(self._serial, bit)

            signed_message = (self._serial, bit, mac.hexdigest())
            chaff = self._chaffer.chaff(self._serial, self._multiplier, len(mac.digest()))
            chaff.append(signed_message)
            random.SystemRandom().shuffle(chaff)
            for c in chaff:
                yield c

            self._serial += 1

def bits(message):
    for char in message:
        for bit in map(int, '{:08b}'.format(ord(char))):
            yield bit

def decode_callback(word, word_eol, userdata):
    global decoder
    serial, bit, mac = map(str.strip, word_eol[1].split(','))
    if decoder.authentic(serial, bit, mac):
        global byte
        byte += bit
        if len(byte) == 8:
            hexchat.command(f"say {chr(int(byte, 2))}")
            byte = ''
    return hexchat.EAT_ALL

def encode_callback(word, word_eol, userdata):
    global encoder
    line = word_eol[1]
    for result in encoder.encode(line):
        hexchat.command(f"say {','.join(map(str, result))}")
    return hexchat.EAT_ALL

if __name__ == '__main__':
    decoder = Decoder("your_secret_key", "sha512")
    byte = ''
    hexchat.hook_print("Channel Message", decode_callback)

    encoder = Encoder("your_secret_key", 10, "sha512")
    hexchat.hook_command("CHAFF", encode_callback)
