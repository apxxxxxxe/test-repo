import numpy as np
from PIL import Image, ImageDraw
import scipy.cluster
import sys
import colorsys
from PySide6.QtWidgets import QApplication, QLabel
import re

from sklearn.cluster import KMeans
import cv2

VARIATION = 3
NUM = int(sys.argv[2])
IMG_PATH = sys.argv[1]


def main():
    img = Image.open(IMG_PATH).convert("RGB")

    color_arr = np.array(img)
    w_size, h_size, n_color = color_arr.shape
    color_arr_one = color_arr.reshape(w_size * h_size, n_color)
    print('img:')
    print(color_arr_one)
    # hls_arr_one = [colorsys.rgb_to_hls(*color_arr_one[i]) for i in range(color_arr_one.shape[0])]

    colors = np.array(kmeans_image(img, NUM))
    print()
    print('4pallet:')
    print(colors)
    print()

    pallet_16s = [gain_lightness(tuple(colors[j])) for j in range(NUM)]
    pallet_16s_arr = np.array(pallet_16s)
    pallet_16s_arr = pallet_16s_arr.reshape(NUM*VARIATION, 3)

    print()
    print('16pallet:')
    print(pallet_16s_arr)

    ran = color_arr_one.shape[0]
    print(ran)
    for index in range(ran):
        print("\rprogress:{}%".format(index*100//ran+1), end="")
        color_arr_one[index] = getNearestValue(pallet_16s_arr, color_arr_one[index])

    result_arr = color_arr_one.reshape(w_size, h_size, n_color)
    reduced_img = Image.fromarray(result_arr, 'RGB')
    pallet_img = make_pallet_img(pallet_16s_arr, img)
    dest_img = get_concat_v(reduced_img, pallet_img)
    dest_img.save('result.png')

    # for i in range(NUM):
    #     light = img.getpixel(i*50, 0)
    #     img.putpixel
    # app = QApplication(sys.argv)
    # label = QLabel("Hello World")
    # label.show()
    # sys.exit(app.exec_())


def make_pallet_img(colors, img):
    palletsize = round(img.width / (NUM*VARIATION))
    pallet_img = Image.new('RGB', (img.width, palletsize))
    draw = ImageDraw.Draw(pallet_img)

    lim = NUM*VARIATION
    for i in range(lim):
        draw.rectangle(((i%lim)*palletsize, (i//lim)*palletsize, (i%lim+1)*palletsize, (i//lim+1)*palletsize), fill=tuple(colors[i]))

    return pallet_img


def kmeans_image(img, n_cluster):
    SUMPLE_SIZE = 100

    if img.width > SUMPLE_SIZE or img.height > SUMPLE_SIZE:
        img = img.resize((SUMPLE_SIZE, SUMPLE_SIZE), Image.NEAREST)

    color_arr = np.array(img)
    w_size, h_size, n_color = color_arr.shape
    color_arr = color_arr.reshape(w_size * h_size, n_color)
    color_arr = color_arr.astype(float)

    codebook, distortion = scipy.cluster.vq.kmeans(color_arr, n_cluster)  # ??????????????????
    code, _ = scipy.cluster.vq.vq(color_arr, codebook)  # ??????????????????????????????????????????????????????

    n_data = []  # ??????????????????????????????
    for n in range(n_cluster):
        n_data.append(len([x for x in code if x == n]))

    desc_order = np.argsort(n_data)[::-1]  # ????????????????????????

    return [codebook[elem].astype(int) for elem in desc_order]


def getNearestValue(list, num):
    """
    ??????: ???????????????????????????????????????????????????????????????
    @param list: ???????????????
    @param num: ?????????
    @return ???????????????????????????
    """

    # ???????????????????????????????????????????????????????????????????????????????????????
    res = np.abs(list - num)
    # print(res)
    #res = res * np.array([10, 1, 1])
    res = np.sum(res, axis=1)
    # print(res)
    idx = res.argmin()
    return list[idx]


def kmeans_hls_image(img, n_cluster):
    SUMPLE_SIZE = 500

    if img.width > SUMPLE_SIZE or img.height > SUMPLE_SIZE:
        img = img.resize((SUMPLE_SIZE, SUMPLE_SIZE), Image.NEAREST)

    color_arr = np.array(img)
    w_size, h_size, n_color = color_arr.shape
    color_arr = color_arr.reshape(w_size * h_size, n_color)
    color_arr = color_arr.astype(float)

    codebook, distortion = scipy.cluster.vq.kmeans(color_arr, n_cluster)  # ??????????????????
    code, _ = scipy.cluster.vq.vq(color_arr, codebook)  # ??????????????????????????????????????????????????????

    n_data = []  # ??????????????????????????????
    for n in range(n_cluster):
        n_data.append(len([x for x in code if x == n]))

    desc_order = np.argsort(n_data)[::-1]  # ????????????????????????

    return [colorsys.hls_to_rgb(*codebook[elem].astype(int)) for elem in desc_order]


def hex_to_rgb(hex):
    pattern = '# ?[0-9A-Za-z]{6}'
    if not(re.match(pattern, hex)):
        print('args must be a Hex Code.(eg.# ffAA00 or ffAA00)')
        return None
    h = hex.lstrip('# ')
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))


def gain_lightness(rgb):
    #gain_nums = [0.5, 0.75, 1.0, 1.25]
    gain_nums = [0.75, 1.0, 1.25]
    #gain_nums = [0.50, 1.0]
    hls_list = list(colorsys.rgb_to_hls(*rgb))
    return list(list(map(lambda x: round(x*1), list(colorsys.hls_to_rgb(hls_list[0], hls_list[1]*gain, hls_list[2])))) for gain in gain_nums)


def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def get_main_color_list_img(img_path, width, num):
    """
    ???????????????????????????????????????????????????????????????????????????PIL???????????????????????????

    Parameters
    ----------
    img_path : str
        ???????????????????????????

    Returns
    -------
    tiled_color_img : Image
        ????????????????????????PIL????????????
    """
    cv2_img = cv2.imread(img_path)
    cv2_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
    cv2_img = cv2_img.reshape(
        (cv2_img.shape[0] * cv2_img.shape[1], 3))

    cluster = KMeans(n_clusters=4)
    cluster.fit(X=cv2_img)
    cluster_centers_arr = cluster.cluster_centers_.astype(
        int, copy=False)

    IMG_SIZE = width // num
    height = IMG_SIZE

    tiled_color_img = Image.new(
        mode='RGB', size=(width, height), color='# 333333')

    for i, rgb_arr in enumerate(cluster_centers_arr):
        color_hex_str = '# %02x%02x%02x' % tuple(rgb_arr)
        color_img = Image.new(
            mode='RGB', size=(IMG_SIZE, IMG_SIZE),
            color=color_hex_str)
        tiled_color_img.paste(
            im=color_img,
            box=(MARGIN + IMG_SIZE * i, MARGIN))
    return tiled_color_img


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
