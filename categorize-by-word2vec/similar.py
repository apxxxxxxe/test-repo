from gensim.models import KeyedVectors
import os
import sys


def vim():
    words = sys.argv[1:]
    print("loading model...")
    model = KeyedVectors.load(os.path.join('model', 'wiki_word2vec.model')).wv
    dic = {}
    for word in words:
        sim = model.most_similar(word)
        for si in sim:
            if si[0] in dic:
                dic[si[0]] += si[1]
            else:
                dic[si[0]] = si[1]
    for key in dic:
        print(key + ": " + str(dic[key]))


def main():
    argv = sys.argv[1:]
    if len(argv) != 2:
        print("error: 2 args required")
        exit()
    print("loading model...")
    model = KeyedVectors.load(os.path.join('model', 'wiki_word2vec.model')).wv
    foo = argv[0]
    bar = argv[1]
    print(foo)
    for line in model.most_similar(foo):
        print(line)
    print("---")
    print(bar)
    for line in model.most_similar(bar):
        print(line)
    print("---")
    print(model.similarity(foo, bar))


if __name__ == '__main__':
    main()
