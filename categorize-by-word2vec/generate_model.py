from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence
import logging
logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

sentences = LineSentence('./wikidata_all.wakati.txt')
model = Word2Vec(sentences, vector_size=200, window=20, min_count=5, workers=4)
model.save('./wiki_word2vec.model')
