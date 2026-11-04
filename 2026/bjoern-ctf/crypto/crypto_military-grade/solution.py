from collections import Counter
from pathlib import Path
from PIL import Image

with open("flag.bmp.enc", "rb") as enc_file:
    ciphertext = enc_file.read()

blocks = [] 
for i in range(0, len(ciphertext), 16):
    block = ciphertext[ i : i + 16]
    blocks.append(block)

background = Counter(blocks).most_common(1)[0][0]

# Replace background blocks with white, and everything else with black
data = bytearray()

for block in blocks:
    if block == background:
        data.extend(b"\xff" * 16) #white
    else:
        data.extend(b"\x00" * 16)#black

data = bytes(data)
pixels = data[54:]  # Skip the BMP header

output = Path("candidates")
output.mkdir(exist_ok=True) # create folder if it doesn't exist
saved = set()

# Guess the height and how much padding AES is added at the end (1 to 128 bytes)
for height in range(50, 300):
    for padding in range(1, 129):
        total_size = len(ciphertext) - padding - 54
        if (total_size % height): # not worth trying, height does not divide total_size
            continue
        row_size = total_size // height  # Bytes per row
        width = row_size // 3      # We assume 24-bit RGB: three bytes per pixel
        if (row_size % 4 or width <= 16 * height): # assertion from chal.py
            continue # also not worth trying, row size should be a multiple of 4 and the width
        if ((width, height) in saved):
            continue
        saved.add((width, height))
        image = Image.frombytes("RGB", (width, height), pixels[:total_size],
                                "raw", "RGB", row_size, -1)  # BMP stores row bottom to top so -1
        image.save(output / f"{width}x{height}.png")