from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from os import urandom

key = urandom(32)
data = open("flag.bmp", "rb").read()

def read(d):
    return int.from_bytes(d, "little")

# I'm not trying to mess with you
assert data[0:2] == b"BM"                           # BMP magic
assert read(data[ 6: 8]) == 0                       # MBZ
assert read(data[ 8:10]) == 0                       # MBZ
assert read(data[10:14]) == 54                      # image data starts at file offset 54
assert read(data[14:18]) == 40                      # normal BITMAPINFOHEADER header
assert read(data[18:22]) > 16 * read(data[22:26])    # landscape text
assert read(data[26:28]) == 1                       # just 1 plane
assert read(data[46:50]) == 0                       # no fancy color table stuff
assert read(data[50:54]) == 0                       # no fancy color table stuff

cipher = AES.new(key, AES.MODE_ECB)
data = cipher.encrypt(pad(data, 128))
open("flag.bmp.enc", "wb").write(data)