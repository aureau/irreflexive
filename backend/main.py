from chunking import extract_chunk_and_clean_article
from model import embed_article, bias_axis, score_article
import numpy as np
from downloader import dl_html
from kagglehub import KaggleDatasetAdapter
import os
import sys
def main():
    test_articles_path = 'test-articles/'
    # title, date, content = getArticleSelectors("https://abcnews.com/US/d4vd-murder-case-timeline-investigation-14-year-girls/story?id=132319472")
    # print("Title: ", title)
    # print("Date: ", date)
    # print("Embeddings: ", embed_article(content))
    # print("Embeddings count: ", len(embed_article(content)))
    # article = 'gothamist.html'
    # link = 'https://archive.is/20260420190459/https://www.nytimes.com/2026/04/20/opinion/trump-birth-control.html'
    # try:    
    #     article = dl_html(link)
    # except Exception as e:
    #     print({e})
    article = os.path.join(test_articles_path, 'mjn.html')
    if not os.path.exists(article):
        print("no article: ", article)
        sys.exit()
    article_chunks = extract_chunk_and_clean_article(article, True)

    # sentence = "The administrations reckless thirst for conflict is a blatant violation of international law and a betrayal of American values."
    # left = np.load('baselines/left-baseline.npy')
    # right = np.load('baselines/right-baseline.npy')
    v_left = np.load('baselines/corp-baselines/left-corpus-vector.npy')
    v_right = np.load('baselines/corp-baselines/right-corpus-vector.npy')
    v_center = np.load('baselines/corp-baselines/center-corpus-vector.npy')
    v_left_shifted = v_left - v_center
    v_right_shifted = v_right - v_center

    # Define the normalized bias axis
    raw_axis = v_right_shifted - v_left_shifted
    bias_axis = raw_axis / np.linalg.norm(raw_axis) # used if want to use center
    # baseline_bias_axis = bias_axis(v_left, v_right) # used if want to use baseline (left and right)

    score = score_article(article_chunks, bias_axis, True)
    print("Sentence: ")
    print(article_chunks)
    # print("Chunks: ")
    # print(article_chunks)
    print("Score: ")
    print(score)

if __name__ == "__main__":
    main()