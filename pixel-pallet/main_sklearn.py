import numpy as np
from PIL import Image, ImageDraw
import sys
import colorsys
from PySide6.QtWidgets import QApplication, QLabel
import re

from sklearn.cluster import KMeans
import cv2

IMG_PATH = sys.argv[1]
NUM = int(sys.argv[2])
VARIATION = 4

GAIN_LIGHTNESS = [0.4, 0.7, 1.0, 1.3]
#GAIN_LIGHTNESS = [0.75, 1.0, 1.25]
#GAIN_LIGHTNESS = [0.50, 1.0]

def main():
    omomi = np.array([1.0, 1.0, 1.0])
    #img = Image.open(IMG_PATH).convert("RGB")
    img = cv2.imread(IMG_PATH)
    img = cv2.resize(img, dsize=None, fx=0.5, fy=0.5)
    cv2.imwrite('x05.png', img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)

    color_arr = np.array(img)
    w_size, h_size, n_color = color_arr.shape
    shape = img.shape
    #X = color_arr.reshape(w_size * h_size, n_color)
    X = img.reshape(shape[0] * shape[1], shape[2]).astype(np.float64)
    print('img:')
    print(X)
    X *= omomi

    # hls_arr_one = [colorsys.rgb_to_hls(*X[i]) for i in range(X.shape[0])]

    initial_model = KMeans(n_clusters=NUM, init='k-means++')
    initial_model.fit(X)

    colors = initial_model.cluster_centers_
    colors /= omomi
    colors /= 255
    colors = np.array([colorsys.hls_to_rgb(*colors[i]) for i in range(colors.shape[0])])
    colors *= 255
    print(colors)

    print()
    print('4pallet:')
    print(colors)
    print()

    pallet_16s_arr = np.array(
            [gain_lightness(tuple(colors[j]), GAIN_LIGHTNESS) for j in range(NUM)]
            )
    pallet_16s_arr = pallet_16s_arr.reshape(NUM*VARIATION, 3)
    pallet_16s_arr = np.abs(pallet_16s_arr.round())

    print()
    print('16pallet:')
    print(pallet_16s_arr)
    print()

    #second_model = KMeans(n_clusters=NUM*VARIATION, init=pallet_16s_arr, n_init=1, max_iter=1)
    #second_model.fit(X)

    #colors = second_model.cluster_centers_
    #print()
    #print('colors:')
    #print(colors)
    #print()

    #Y = second_model.predict(X)

    #img_cnv = np.empty((0, 3), dtype = np.uint8)
    #ran = Y.shape[0]
    #print(ran)
    #for i in range(0, ran):
    #    print("\rprogress:{}%".format(i*100//ran+1), end="")
    #    rgb = colors[Y[i]]
    #    img_cnv = np.append(img_cnv, np.array([rgb]), axis = 0)
    ##img_cnv.reshape(w_size, h_size, n_color)
    #img_cnv = img_cnv.reshape(shape)
    ##img_cnv_img = Image.fromarray(img_cnv, 'RGB')
    ##img_cnv_img.save('sk_reduced.png')
    #img_cnv = cv2.cvtColor(img_cnv.astype(np.float32), cv2.COLOR_RGB2BGR)
    #cv2.imwrite('cv2_pic.png', img_cnv)

    #reduced_img = Image.open('cv2_pic.png').convert("RGB")
    #pallet_img = make_pallet_img(colors, reduced_img)
    #last_img = get_concat_v(reduced_img, pallet_img)
    #last_img.save('cv2_pic.png')

    img = Image.open(IMG_PATH).convert("RGB")
    img_arr = np.array(img)
    w_size, h_size, n_color = img_arr.shape
    img_arr = img_arr.reshape(w_size * h_size, n_color)

    ran = img_arr.shape[0]
    print(ran)
    for index in range(ran):
        print("\rprogress:{}%".format(index*100//ran+1), end="")
        img_arr[index] = getNearestValue(pallet_16s_arr, img_arr[index])

    result_arr = img_arr.reshape(w_size, h_size, n_color)
    reduced_img = Image.fromarray(result_arr, 'RGB')
    pallet_img = make_pallet_img(pallet_16s_arr, np.array(img).shape[1])
    dest_img = get_concat_v(reduced_img, pallet_img)
    dest_img.save('result.png')


def make_pallet_img(colors, width):
    """
    概要: 色情報の入った配列をもとに横並びのパレット画像を作成して返す関数
    @param colors: 1つ以上のRGB値が格納された二次元配列
    @param width: 作成する画像の全体の横幅
    @return PIL画像
    """

    lim = NUM * VARIATION  # 1行あたりのパレット数
    palletsize = round(width / lim)
    pallet_img = Image.new('RGB', (width, palletsize))
    draw = ImageDraw.Draw(pallet_img)

    for i in range(lim):
        draw.rectangle(
                ((i % lim) * palletsize, (i // lim) * palletsize,
                    (i % lim + 1) * palletsize, (i // lim + 1) * palletsize),
                fill=tuple(colors[i].astype(int))
                )

    return pallet_img


def getNearestValue(list, num):
    """
    概要: リストからある値に最も近い値を返却する関数
    @param list: データ配列(ndarray)
    @param num: 対象値(ndarray)
    @return 対象値に最も近い値
    """

    # リスト要素と対象値の差分を計算し最小値のインデックスを取得
    #res = np.abs(list - num + np.array([1, 1, 1]))
    idx = np.linalg.norm(list - num, axis=1).argmin()
    # print(res)
    #res = res * np.array([10, 1, 1])
    #res = np.sum(res, axis=1)
    # print(res)
    return list[idx]


def hex_to_rgb(hex):
    """
    概要: 16進数表記の文字列をRGB値の配列に変換する関数
    @param : 16進数表記の文字列
    @return RGB値の一次元配列
    """

    pattern = '# ?[0-9A-Za-z]{6}'
    if not(re.match(pattern, hex)):
        print('args must be a Hex Code.(eg.# ffAA00 or ffAA00)')
        return None
    h = hex.lstrip('# ')
    return tuple(int(h[i:i+2], 16)/255 for i in (0, 2, 4))


def gain_lightness(rgb, gain_nums):
    """
    概要: 渡されたRGB値をHLSに変換し、指定の倍率を輝度に掛けたあとRGB値として返す
    @param rgb: RGB値が格納された一次元配列
    @param gain_num: 倍率が格納された一次元配列
    @return 輝度倍率が適用されたRGB値が格納された一次元配列
    """

    hls_list = list(colorsys.rgb_to_hls(*rgb))
    return list(colorsys.hls_to_rgb(hls_list[0], hls_list[1]*gain, hls_list[2]) for gain in gain_nums)


def get_concat_v(im1, im2):
    """
    概要: PILライブラリの画像アイテムを縦に結合する
    @param : 上に来る画像アイテム
    @param : 下に来る画像アイテム
    @return 結合された画像アイテム
    """

    dst = Image.new('RGB', (im1.width, im1.height + im2.height))
    dst.paste(im1, (0, 0))
    dst.paste(im2, (0, im1.height))
    return dst


if __name__ == "__main__":
    main()
