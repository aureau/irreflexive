'''
1. Extract and Clean
    - Remove: Navigation bars, sidebars, footers, and advertisement blocks.
    - Keep: The main article or body content, preserving the header tags (<h1> through <h6>) and paragraph tags (<p>).
2. Apply "Markdown-Header" Chunking
    - Converting the cleaned HTML into Markdown is a highly effective industry standard. Markdown is lightweight and clearly retains document hierarchy.
    - Split by Header: Break the text whenever a new # (H1), ## (H2), or ### (H3) appears.
    - Keep Context: If a section under a ## header is too long, sub-divide it by paragraphs (<p>).
    - Why it works: It ensures that a table or a list under a specific heading stays grouped together with that heading.
3. Enforce Token Limits (For all-MiniLM-L6-v2)
    - Because your model has a strict 256-token limit, you must ensure no chunk exceeds this size.
    - Target Size: Aim for chunks of roughly 100 to 150 words (about 150–200 tokens). This leaves a safety buffer for the model.
    - Add Overlap: When a long section must be split into two chunks, overlap them by 20 to 30 words. This ensures that a sentence or concept cut in half can still be understood by the model in at least one of the chunks.
'''
from bs4 import BeautifulSoup
import requests
import os
import trafilatura as tf
import langchain_text_splitters as lc



fox = 'webpages/mamdani-fox.html'
nyt = 'webpages/mamdani-nyt.html'

def extract_chunk_and_clean_article(article, isFile=True):
    if isFile:
        with open(article, 'r', encoding='utf-8') as file:
            article = file.read()
        article = tf.extract(article, output_format="markdown")
    if not isFile:
        # fix later and see what use case is going to be
        article = tf.extract(article, output_format="markdown")
    
    splitter = lc.RecursiveCharacterTextSplitter(
        chunk_size=180,
        chunk_overlap=24
    )
    chunks = splitter.split_text(article)
    return chunks