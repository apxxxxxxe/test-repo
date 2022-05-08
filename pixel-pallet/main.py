#import cv2
#from matplotlib import pyplot as plt
import numpy as np
from PIL import Image, ImageDraw
import scipy.cluster
import sys
from PySide6.QtWidgets import QApplication, QLabel


def main():
    num = 4
    imgpath = '20171208.png'
    # imgpath = 'b5fb1ea03d347b5a.jpeg'
    colors = kmeans_process(imgpath, num)

    im = Image.open(imgpath).convert("RGB")
    draw = ImageDraw.Draw(im)
    palletsize = im.width / (num*2)
    for i in range(num):
        draw.rectangle((i*palletsize, 0, (i+1)*palletsize, palletsize), fill=tuple(colors[i]))
    im.save('out.png')

    # for i in range(num):
    #     light = im.getpixel(i*50, 0)
    #     im.putpixel
    app = QApplication(sys.argv)
    label = QLabel("Hello World")
    label.show()
    sys.exit(app.exec_())


def kmeans_process(imgpath, n_cluster):
    samplesize = 100

    img = Image.open(imgpath).convert("RGB")
    if img.width > samplesize or img.height > samplesize:
        img = img.resize((samplesize, samplesize), Image.NEAREST)

    color_arr = np.array(img)
    w_size, h_size, n_color = color_arr.shape
    color_arr = color_arr.reshape(w_size * h_size, n_color)
    color_arr = color_arr.astype(float)

    codebook, distortion = scipy.cluster.vq.kmeans(color_arr, n_cluster)  # クラスタ中心
    code, _ = scipy.cluster.vq.vq(color_arr, codebook)  # 各データがどのクラスタに属しているか

    n_data = []  # 各クラスタのデータ数
    for n in range(n_cluster):
        n_data.append(len([x for x in code if x == n]))

    desc_order = np.argsort(n_data)[::-1]  # データ数が多い順

    return [codebook[elem].astype(int) for elem in desc_order]


class Pallet:
    pallet = np.zeros((1, 1))

    def __init__(self, num):
        self.pallet = np.zeros((num, 3))

    def getPalletFromImage(image):
        print()

    def setPallete(index, rgbcolor):
        print()

    def reloadPallete():
        print()

    @property
    def getPallet(self, index):
        return self.pallet[index]


class PalleteChanger:

    def __init__(self, pallet):
        self.pallet = pallet

    def generatePallete(self, num):
        self.pallet = np.zeros(num, 3)


if __name__ == "__main__":
    main()
