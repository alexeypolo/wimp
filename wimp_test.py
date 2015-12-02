# Assume python 2.7

import wimp
import sys

def test_encrypt_decrypt(message):
    if message != wimp.decrypt("password", wimp.encrypt("password", message)):
        return 1
    return 0

def T(name, rc):
    if rc != 0:
        print name, 'ERROR', rc
        sys.exit(rc)
    print name, 'OK'

def main(argv):
    T('encrypt/decrypt', test_crypto("hello"))
    T('hash', test_hash("hello"))

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
