from hashlib import md5
from Crypto.Cipher import AES
from Crypto import Random
import argparse


def derive_key_and_iv(password, salt, key_length, iv_length):
    d = d_i = ''
    while len(d) < key_length + iv_length:
        d_i = md5(d_i + password + salt).digest()
        d += d_i
    return d[:key_length], d[key_length:key_length+iv_length]


def encrypt(in_file, out_file, password, key_length=32):
    bs = AES.block_size
    salt = Random.new().read(bs - len('Salted__'))
    key, iv = derive_key_and_iv(password, salt, key_length, bs)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    out_file.write('Salted__' + salt)
    finished = False
    while not finished:
        chunk = in_file.read(1024 * bs)
        if len(chunk) == 0 or len(chunk) % bs != 0:
            padding_length = (bs - len(chunk) % bs) or bs
            chunk += padding_length * chr(padding_length)
            finished = True
        out_file.write(cipher.encrypt(chunk))


def decrypt(in_file, out_file, password, key_length=32):
    bs = AES.block_size
    salt = in_file.read(bs)[len('Salted__'):]
    key, iv = derive_key_and_iv(password, salt, key_length, bs)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    next_chunk = ''
    finished = False
    while not finished:
        chunk, next_chunk = next_chunk, cipher.decrypt(in_file.read(1024 * bs))
        if len(next_chunk) == 0:
            padding_length = ord(chunk[-1])
            chunk = chunk[:-padding_length]
            finished = True
        out_file.write(chunk)


if __name__ == "__main__":
    # Collect command line arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--encrypt", help="Encrypt the specified file with the given password")
    ap.add_argument("-d", "--decrypt", help="Decrypt the specified file with the given password")
    args = vars(ap.parse_args())

    if args['encrypt'] is not None:
        password = input("Password:\n")
        filename = args['encrypt']
        if '_decrypted' in filename:
            output_filname = filename.replace('_decrypted', '')
        else:
            filename_split = filename.split('.')
            output_filename = filename_split[:-1].join('.') + "_encrypted.json"
        encrypt(filename, output_filename, password)
    elif args['decrypt'] is not None:
        password = input("Password:\n")
        filename = args['decrypt']
        if '_encrypted' in filename:
            output_filename = filename.replace('_encrypted', '')
        else:
            filename_split = filename.split('.')
            output_filename = filename_split[:-1].join('.') + "_decrypted.json"
        decrypt(filename, output_filename, password)
    else:
        print("No option selected between encrypt or decrypt...")
