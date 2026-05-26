import sys
import os
sys.path.append('../')
import glob
from backend.scripts.chunking import extract_chunk_and_clean_article
from backend.scoring.model import embed_article
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
    
left_leaning_articles = glob.glob('webpages/left-webpages/*.html')
right_leaning_articles = glob.glob('webpages/right-webpages/*.html')

try:
    left_leaning_chunks = []
    for i, left_leaning_article in enumerate(left_leaning_articles):
        left_chunks = extract_chunk_and_clean_article(left_leaning_article, isFile=True)
        left_leaning_chunks.extend(left_chunks)
        print(f"left chunk count: {i + 1}")

    right_leaning_chunks = []
    for i, right_leaning_article in enumerate(right_leaning_articles):
        right_chunks = extract_chunk_and_clean_article(right_leaning_article, isFile=True)
        right_leaning_chunks.extend(right_chunks)
        print(f"right chunk count: {i + 1}")
    left_baseline = calculate_baseline(left_leaning_chunks)
    right_baseline = calculate_baseline(right_leaning_chunks)
except Exception as e:
    print({e})
    sys.exit(1)


def nps(npy, baseline):
    np.save(npy, baseline)
    return

left_npy = 'left-baseline.npy'
right_npy = 'right-baseline.npy'
# check if file exists – if so then overwrite with np.save 
if os.path.isfile(left_npy):
    nps(left_npy, left_baseline)
    print("overwrote left npy")
else:
    nps(left_npy, left_baseline)
print("left baseline saved")
if os.path.isfile(right_npy):
    nps(right_npy, right_baseline)
    print("overwrote right npy")
else:
    nps(right_npy, right_baseline)
print("right baseline saved")