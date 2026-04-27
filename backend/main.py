from chunking import extract_chunk_and_clean_article
from model import embed_article, bias_axis, score_article
from scrape import getArticleSelectors
import numpy as np

def main():
    # title, date, content = getArticleSelectors("https://abcnews.com/US/d4vd-murder-case-timeline-investigation-14-year-girls/story?id=132319472")
    # print("Title: ", title)
    # print("Date: ", date)
    # print("Embeddings: ", embed_article(content))
    # print("Embeddings count: ", len(embed_article(content)))
    # article = 'gothamist.html'
    article = 'mas.html'
    article_chunks = extract_chunk_and_clean_article(article)
    # sentence = "The administrations reckless thirst for conflict is a blatant violation of international law and a betrayal of American values."
    left = np.load('baselines/left-baseline.npy')
    right = np.load('baselines/right-baseline.npy')
    baseline_bias_axis = bias_axis(left, right)

    score = score_article(article_chunks, baseline_bias_axis, True)
    print("Sentence: ")
    print(article_chunks)
    # print("Chunks: ")
    # print(article_chunks)
    print("Score: ")
    print(score)

if __name__ == "__main__":
    main()