from gensim.models import KeyedVectors
import MeCab
import os
import glob
import collections
from tika import parser

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


def getSamples(sources):
    hinshi = ["名詞", "動詞", "形容詞"]
    p = MeCab.Tagger("-Ochasen")
    splited_sources = []

    for source in sources:
        splited_source = []
        node = p.parseToNode(source)
        while node:
            sp = node.feature.split(",")
            pos = sp[0]
            if pos in hinshi:
                splited_source.append(sp[6])
            node = node.next
        most_common_words = collections.Counter(splited_source).most_common(20)
        splited_sources.append(most_common_words)

    return splited_sources


def main():
    print("model loading...")
    model = KeyedVectors.load(os.path.join('model', 'wiki_word2vec.model')).wv

    print("file searching...")
    dirpath = os.path.join(os.environ['HOME'], "Downloads", "docs")
    file_names = []
    for f in glob.glob(os.path.join(dirpath, "*.pdf")):
        if os.path.isfile(os.path.join(dirpath, f)):
            file_names.append(f)

    print("file parsing...")
    file_contents = []
    for file_name in file_names:
        fp = os.path.join(dirpath, file_name)
        print(fp)
        content = loadWithMiner(fp)
        file_contents.append(content)
    print("sample getting...")
    samples = getSamples(file_contents)
    print("categories checking...")

    subject_candidates_list = [
        ["課題", "学校", "レポート", "提出"],
        ["伺か", "創作", "ゴースト", "キャラクター"],
    ]
    subjects_list = []
    for subject_candidates in subject_candidates_list:
        subjects = []
        for subject_candidate in subject_candidates:
            if subject_candidate in model:
                subjects.append(subject_candidate)
            else:
                print(subject_candidates +
                      " do not exist in the model: skipped.")
        subjects_list.append(subjects)

    print(subjects_list)
    print("file categorizing...")

    similarities = []
    identifiers = []
    for sample in samples:
        max_similarity = 0
        max_index = -1
        for i in range(len(subjects_list)):
            subjects = subjects_list[i]
            similarity_sum = 0
            for subject in subjects:
                for word in sample:
                    if word[0] in model:
                        similarity_sum += model.similarity(
                            word[0], subject) * word[1]
                if max_similarity < similarity_sum:
                    max_similarity = similarity_sum
                    max_index = i
        similarities.append(max_similarity)
        if max_similarity > 200:
            identifiers.append(max_index)
        else:
            identifiers.append(-1)

    for i in range(len(identifiers)):
        if identifiers[i] != -1:
            print(str(similarities[i])+":"+str.ljust(",".join(subjects_list[identifiers[i]]),
                  20, " ") + ": " + file_names[i])
        else:
            print(str.ljust("error",
                  20, " ") + ": " + file_names[i])


if __name__ == '__main__':
    main()
