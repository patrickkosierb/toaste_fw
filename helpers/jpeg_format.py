from frames import f
from PIL import Image
import io

intf = [int(x) for x in f]
file = open('frames.py', 'r')


def jpeg_marker_array_to_image(marker_array):
    # Convert the marker array to bytes
    marker_bytes = bytes(marker_array)
    
    # Create a PIL Image from the bytes
    img = Image.open(io.BytesIO(marker_bytes))
    
    return img
    

crisp = jpeg_marker_array_to_image(intf)
print(crisp)
crisp.save("lol.jpg")
