# Assume python 2.7

import wimp
import sys

def test_encrypt_decrypt(password, message):
    if message != wimp.decrypt(password, wimp.encrypt(password, message)):
        return 1
    return 0

def test_hash():
    message = "hello"
    digest_sha1 = "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d"
    if digest_sha1 != wimp.hash(message):
        return 1
    return 0

def T(name, rc):
    if rc != 0:
        print name, '[ERROR], rc', rc
        sys.exit(rc)
    print name, '[OK]'

def main(argv):
    T('encrypt/decrypt', test_encrypt_decrypt("password", "hello"))
    T('hash', test_hash())

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
