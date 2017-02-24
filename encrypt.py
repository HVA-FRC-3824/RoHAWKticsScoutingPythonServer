from simplecrypt import encrypt, decrypt
from getpass import getpass
from argparse import ArgumentParser
import os

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-d', '--decrypt', action='store_true', help="Decrypts logins file")
    parser.add_argument('-e', '--encrypt', action='store_true', help="Encrypts logins file")
    args = vars(parser.parse_args())

    if args['decrypt']:
        password = getpass()
        if os.path.isfile('logins_encrypted.json'):
            with open('logins_encrypted.json', 'rb') as logins_encrypted_file:
                ciphertext = logins_encrypted_file.read()
            plaintext = decrypt(password, ciphertext).decode('utf8')
            with open('../logins.json', 'w') as logins_file:
                logins_file.write(plaintext)
        else:
            print("logins_encrypted.json does not exist")
    elif args['encrypt']:
        password = getpass()
        if os.path.isfile('../logins.json'):
            with open('../logins.json', 'r') as logins_file:
                plaintext = logins_file.read()
            ciphertext = encrypt(password, plaintext)
            with open('logins_encrypted.json', 'wb') as logins_encrypted_file:
                logins_encrypted_file.write(ciphertext)
        else:
            print('../logins.json does not exist')
    else:
        parser.print_help()
