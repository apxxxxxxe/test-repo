import numpy as np
from PIL import Image, ImageDraw
import scipy.cluster
import sys
import colorsys
from PySide6.QtWidgets import QApplication, QLabel
import re

from sklearn.cluster import KMeans
import cv2

def main():
    VARIATION = 4
    NUM = int(sys.argv[2])

    imgpath = sys.argv[1]

    img = Image.open(imgpath).convert("RGB")

    color_arr = np.array(img)
    w_size, h_size, n_color = color_arr.shape
    color_arr = color_arr.reshape(w_size * h_size, n_color)

    colors = kmeans_hls_image(img, NUM)

    palletsize = round(img.width / (NUM*VARIATION))
    pallet_img = Image.new('RGB', (img.width, palletsize))
    draw = ImageDraw.Draw(pallet_img)

    gain_colors = [gain_lightness(tuple(colors[j])) for j in range(NUM)]
    #gain_colors = np.abs(gain_colors)
    gain_colors_arr = np.array(gain_colors)
    gain_colors_arr = gain_colors_arr.reshape(NUM*VARIATION, 3)

    lim = NUM*VARIATION
    for i in range(lim):
        draw.rectangle(((i%lim)*palletsize, (i//lim)*palletsize, (i%lim+1)*palletsize, (i//lim+1)*palletsize), fill=tuple(gain_colors_arr[i]))

    print(gain_colors_arr)

    ran = color_arr.shape[0]
    print(ran)
    for index in range(ran):
        print("\rprogress:{}%".format(index*100//ran+1), end="")
        color_arr[index] = getNearestValue(gain_colors_arr, color_arr[index])

    result_arr = color_arr.reshape(w_size, h_size, n_color)
    reduced_img = Image.fromarray(result_arr)
    dest_img = get_concat_v(reduced_img, pallet_img)
    dest_img.save('result.png')

    # for i in range(NUM):
    #     light = img.getpixel(i*50, 0)
    #     img.putpixel
    # app = QApplication(sys.argv)
    # label = QLabel("Hello World")
    # label.show()
    # sys.exit(app.exec_())


def kmeans_image(img, n_cluster):
    SUMPLE_SIZE = 100

    if img.width > SUMPLE_SIZE or img.height > SUMPLE_SIZE:
        img = img.resize((SUMPLE_SIZE, SUMPLE_SIZE), Image.NEAREST)

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

def kmeans_hls_image(img, n_cluster):
    SUMPLE_SIZE = 100

    if img.width > SUMPLE_SIZE or img.height > SUMPLE_SIZE:
        img = img.resize((SUMPLE_SIZE, SUMPLE_SIZE), Image.NEAREST)

    color_arr = np.array(img)
    w_size, h_size, n_color = color_arr.shape
    color_arr = color_arr.reshape(w_size * h_size, n_color)
    print(color_arr)
    color_arr = color_arr.astype(float)

    hls_arr_one = [colorsys.rgb_to_hls(*color_arr[i]/255) for i in range(len(color_arr))]
    #color_arr = [colorsys.hls_to_rgb(*hls_arr_one[i]) for i in range(len(hls_arr_one))]
    #hls_arr_one = color_arr
    print(np.array(hls_arr_one))
    #hls_arr_one = np.delete(hls_arr_one, 1, 1)  # Lwosakujo
    #hls_arr_one *= np.array([1, 0, 1])
    #hls_arr_one += np.array([0, 0.5, 0])
    #hls_arr_one = hls_arr_one.astype(float)

    codebook, distortion = scipy.cluster.vq.kmeans(hls_arr_one, n_cluster)  # クラスタ中心
    code, _ = scipy.cluster.vq.vq(hls_arr_one, codebook)  # 各データがどのクラスタに属しているか

    n_data = []  # 各クラスタのデータ数
    for n in range(n_cluster):
        n_data.append(len([x for x in code if x == n]))

    desc_order = np.argsort(n_data)[::-1]  # データ数が多い順

    print(np.array([codebook[elem] for elem in desc_order]))

    ret = np.array([colorsys.hls_to_rgb(*codebook[elem]) for elem in desc_order])*255
    return ret.tolist()
    #return [colorsys.hls_to_rgb(*codebook[elem].astype(int)) for elem in desc_order]
    #return [codebook[elem].astype(int) for elem in desc_order]

def getNearestValue(list, num):
    """
    概要: リストからある値に最も近い値を返却する関数
    @param list: データ配列
    @param num: 対象値
    @return 対象値に最も近い値
    """

    # リスト要素と対象値の差分を計算し最小値のインデックスを取得
    res = np.abs(list - num)
    # print(res)
    res = res * np.array([10, 1, 1])
    res = np.sum(res, axis=1)
    # print(res)
    idx = res.argmin()
    return list[idx]


def hex_to_rgb(hex):
    pattern = '# ?[0-9A-Za-z]{6}'
    if not(re.match(pattern, hex)):
        print('args must be a Hex Code.(eg.# ffAA00 or ffAA00)')
        return None
    h = hex.lstrip('# ')
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))


def gain_lightness(rgb):
    gain_nums = [0.5, 0.75, 1.0, 1.25]
    #gain_nums = [50, 75, 100, 125]
    # gain_nums = [0.75, 1.0]
    hls_list = list(colorsys.rgb_to_hls(*rgb))
    return list(list(map(lambda x: round(x*1), list(colorsys.hls_to_rgb(hls_list[0], hls_list[1]*gain, hls_list[2])))) for gain in gain_nums)
    #return list(list(map(lambda x: round(x*1), list(colorsys.hls_to_rgb(hls_list[0], hls_list[1]+gain, hls_list[2])))) for gain in gain_nums)


def get_concat_v(im1, im2):
    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


def get_main_color_list_img(img_path, width, num):
    """
    対象の画像のメインカラーを算出し、色を横並びにしたPILの画像を取得する。

    Parameters
    ----------
    img_path : str
        対象の画像のパス。

    Returns
    -------
    tiled_color_img : Image
        色を横並びにしたPILの画像。
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
