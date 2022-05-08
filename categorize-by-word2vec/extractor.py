import os
import sys

from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from io import StringIO


def readFileText(path):
    try:
        reader = open(path, 'r', encoding='utf-8')
    except:
        return ""
    else:
        result = reader.read()
        reader.close()
        return result


def writeFileText(path, text):
    try:
        writer = open(path, 'w+', encoding='utf-8')
    except:
        return False
    else:
        writer.write(text)
        writer.close()
        return True


def loadWithMiner(path):
    filename = os.path.basename(path)
    destpath = os.path.join("cache", filename)

    text = readFileText(destpath)
    if text == "":
        # 標準組込み関数open()でモード指定をbinaryでFileオブジェクトを取得
        fp = open(path, 'rb')
        # 出力先をPythonコンソールするためにIOストリームを取得
        outfp = StringIO()
        # 各種テキスト抽出に必要なPdfminer.sixのオブジェクトを取得する処理
        rmgr = PDFResourceManager()  # PDFResourceManagerオブジェクトの取得
        lprms = LAParams()          # LAParamsオブジェクトの取得
        # TextConverterオブジェクトの取得
        device = TextConverter(rmgr, outfp, laparams=lprms)
        # PDFPageInterpreterオブジェクトの取得
        iprtr = PDFPageInterpreter(rmgr, device)

        # PDFファイルから1ページずつ解析(テキスト抽出)処理する
        for page in PDFPage.get_pages(fp):
            iprtr.process_page(page)
        text = outfp.getvalue()
        writeFileText(destpath, text)

        outfp.close()
        device.close()  # TextConverterオブジェクトの解放
        fp.close()  # Fileストリームを閉じる

    return text


def main(path):
    print(loadWithMiner(path))


if __name__ == '__main__':
    main(sys.argv[1])
