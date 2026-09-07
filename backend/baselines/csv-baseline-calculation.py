import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import langchain_text_splitters as lc
import os
from tqdm import tqdm
os.makedirs('corp-baselines', exist_ok=True)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L12-v2")
text_splitter = lc.RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)


path = 'datasets/bias_clean.,`csv'
df = pd.read_csv(path)
df = df.dropna(subset=['bias', 'page_text'])
bias_map = {
    'left': 'left',
    'leaning-left': 'left',
    'center': 'center',
    'leaning-right': 'right',
    'right': 'right'
}
df['mapped_bias'] = df['bias'].map(bias_map)

def process_corpus(texts):
    """Chunks, embeds, mean-pools, and normalizes a list of articles."""
    article_vectors = []

    for text in tqdm(texts, desc=f"Processing corpus for {bias}"):
        chunks = text_splitter.split_text(text)
        chunk_embeddings = []
        for chunk in chunks:
            embeddings = model.encode(chunk, batch_size=32, show_progress_bar=True)
            # single string -> (dim,); batch -> (n, dim) — never mean over dim axis on 1d
            if embeddings.ndim == 1:
                vec = embeddings
            else:
                vec = np.mean(embeddings, axis=0)
            n = np.linalg.norm(vec)
            if n > 0:
                chunk_embeddings.append(vec / n)
        if chunk_embeddings:
            article_vector = np.mean(chunk_embeddings, axis=0)
            n = np.linalg.norm(article_vector)
            if n > 0:
                article_vectors.append(article_vector / n)
    corpus_vector = np.mean(article_vectors, axis=0)
    return corpus_vector / np.linalg.norm(corpus_vector)
    
for bias in ['left', 'right', 'center']:
    category_texts = df[df['mapped_bias'] == bias]['page_text'].tolist()
    corpus_vector = process_corpus(category_texts)
    if corpus_vector is not None:
        np.save(f'corp-baselines/{bias}-corpus-vector.npy', corpus_vector)
        print(f'Saved {bias} corpus vector')
    else:
        print(f'No corpus vector found for {bias}')
print('All corpus vectors saved')