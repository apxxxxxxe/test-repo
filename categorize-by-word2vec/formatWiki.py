import MeCab
import codecs
import glob
from bs4 import BeautifulSoup
from datetime import datetime

tagger = MeCab.Tagger('-Owakati')


def save(src):
    with codecs.open(src, 'r', 'utf-8') as f:
        soup = BeautifulSoup(f.read(), "lxml")
        doc_tags = soup.find_all("doc")
        sentences = []
        dst = "text/wiki{}".format(len(glob.glob("contents/wiki*"))+1)
        for doc in doc_tags:
            content = "".join(doc.text.splitlines()[3:])
            content = " ".join(tagger.parse(content).split())
            sentences.append(content)
        print(*sentences, sep="\n", file=codecs.open(dst, 'w', 'utf-8'))


# 1. globを使ってarticlesにある３つのフォルダのパスを取得。
dirlist = glob.glob("text/*")
# dirlist = ["articles/AA", "articles/AB", "articles/AC"]
for dirname in dirlist:
    # 2. AA, AB, ACの中の全てのファイルのパスを取得。
    for src in glob.glob(dirname+"/*"):
        # 3. ファイルをひとつずつ処理していく。
        # src = "articles/AA/wiki_00"
        print("{}:\t{}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), src))
        save(src)
