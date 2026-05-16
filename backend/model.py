from sre_compile import isstring

from numpy.char import isalpha
from chunking import extract_chunk_and_clean_article
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")

def embed_article(article):
    embeddings = model.encode(article)
    # print(embeddings)
    return embeddings

def bias_axis(left_vecor, right_vector):
    # subtracting left from right
    bias_axis = right_vector - left_vecor
    bias_axis = bias_axis / np.linalg.norm(bias_axis)
    return bias_axis

def score_article(article, bias_axis, isTest=False):
    # checking if article is already in chunks or not
    if isinstance(article, list):
        article_chunks = article
    elif isTest:
        article_chunks = [article]
    else:
        article_chunks = extract_chunk_and_clean_article(article, False)
    
    embedding_article_chunks = embed_article(article_chunks)
    article_vector = np.mean(
        embedding_article_chunks,
        axis=0
        )
    article_vector = article_vector / np.linalg.norm(article_vector)
    score = np.dot(article_vector, bias_axis)
    return score

# touch on more later
# def query_article_biases(article):
#     query_embeddings = model.encode_query([
#         "Find the initial bias of the article. (Left, Right, Center, etc.)"
#     ])