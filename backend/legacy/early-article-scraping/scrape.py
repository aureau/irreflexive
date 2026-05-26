from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
from model import embed_article

def getArticleSelectors(url):
        title = None
        date = None
        content = None

        # seeing if web is even accessible
        ri = requests.get(url)
        print("Status Code: ", ri.status_code)
        if ri.status_code != 200:
            raise ValueError(f"Failed to fetch URL {url}")
        soup = BeautifulSoup(ri.text, "html.parser")

        # loading
        with open("article-selector.json", "r") as file:
            article_selector = json.load(file)
        
        # domain logic / catch
        domain = url.split("/")[2]
        if domain not in article_selector:
            raise ValueError(f"Domain {domain} not found in article-selector.json")


        # all selectors logic (title, date, content)
        article_selector = article_selector[domain]
        selectors = article_selector["main"]["title"]
        for sel in selectors:
            node = soup.select_one(sel)
            if node:
                title = node.get_text(" ", strip=True)
                break
        
        selectors = article_selector["main"]["date"]
        for sel in selectors:
            node = soup.select_one(sel)
            if node and domain == "apnews.com":
                date = node.get("data-timestamp")
                date = datetime.fromtimestamp(int(date) / 1000).strftime('%B %d, %Y %I:%M %p')
                break
            elif node and domain != "apnews.com":
                date = node.get_text(" ", strip=True)
                break
            else:
                raise ValueError(f"Date not found for domain {domain}")

        selectors = article_selector["main"]["content"]["inline-paragraph-selectors"]
        for sel in selectors:
            nodes = soup.select(sel)
            for node in nodes:
                if node:
                    text = node.get_text(" ", strip=True)
                    content.append(text)
                    break
        return title, date, content
def printArticles(url):
    title, date, content = getArticleSelectors(url)
    print("Title: ", title)
    print("--------------------------------")
    print("Date: ", date)
    print("--------------------------------")
    print("Content: ", content)



# printArticles("https://apnews.com/article/us-iran-war-pakistan-april-21-2026-177a2d0701ef172c3e51686bc1f18f30")


def showArticleEmbeddings(article):
    embeddings = embed_article(article)
    print(embeddings)

# number = 1
# with open("articles.txt", 'r') as file:
#     urls = file.readlines()
#     for url in urls:
#         if url.strip() == "":
#             continue
#         print("--------------------------------")
#         print("ARTICLE: ", number)
#         print("URL: ", url.strip())
#         number += 1
#         printArticles(url.strip())
#         print("--------------------------------")
#         print("")
