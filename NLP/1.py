import nltk
from nltk.corpus import treebank
t = treebank.parsed_sents('wsj_0001.mrg')[0]

sentence = """At eight o'clock on Thursday morning
... Arthur didn't feel very good."""

tokens = nltk.word_tokenize(sentence)
print(f"tokens:{tokens}")

tagged = nltk.pos_tag(tokens)
print(f"tagged[0:6]:{tagged[0:6]}")

entities = nltk.chunk.ne_chunk(tagged)
print(f"entities:{entities}")

t.draw()