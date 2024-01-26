from png import PngEncoder
import random as rd

class Image :
    def __init__(self, arr) :
        self.data = arr

    def save(self, file_name, debug=False) :
        PngEncoder(self.data, debug=debug).save(file_name)

def rd_rgba_pixel() :
    return tuple(rd.randint(0, 255) for _ in range(4))

def rd_rgba_image(width, height) :
    img = []
    for _ in range(height) :
        img.append([rd_rgba_pixel() for _ in range(width)])
        
    return img


if __name__ == '__main__' :
    # print([hex(int(e)) for e in  Image([[255]])._get_content()])
    Image([[(255, 0, 0, 100)]*20]*20).save('img.png', debug=True)
    # Image(rd_rgba_image(2, 2)).save('img.png', debug=True)
