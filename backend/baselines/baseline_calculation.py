import sys
sys.path.append('../')
from chunking import extract_chunk_and_clean_article
from model import embed_article
import numpy as np
'''
Pass every chunk from your "Baseline Left" article through all-MiniLM-L6-v2 to get a list of vectors.
Take the mathematical average (mean) of all those vectors to create a single, unified 384-dimensional vector that represents the whole article.
Average the vectors of your 3–5 different "Left" articles together to create one massive, highly stable Super-Anchor Left Vector. Repeat the exact same process for the Right side.

DO NOT RUN THIS FILE MORE THAN ONCE, THE GOAL IS TO RECIEVE YOUR LEFT AND RIGHT BASELINE FILES

'''

def calculate_baseline(chunks) -> np.array:
    embeddings = []
    for chunk in chunks:
        embeddings.append(embed_article(chunk))
    baseline_vector = np.mean(
        embeddings,
        axis=0
    )
    baseline_vector = baseline_vector / np.linalg.norm(baseline_vector)
    return baseline_vector
    
left_leaning_articles = 'webpages/mamdani-nyt.html'
right_leaning_articles = 'webpages/mamdani-fox.html'

left_leaning_chunks = extract_chunk_and_clean_article(left_leaning_articles, isFile=True)
right_leaning_chunks = extract_chunk_and_clean_article(right_leaning_articles, isFile=True)

left_baseline = calculate_baseline(left_leaning_chunks)
right_baseline = calculate_baseline(right_leaning_chunks)

np.save('left-baseline.npy', left_baseline)
np.save('right-baseline.npy', right_baseline)