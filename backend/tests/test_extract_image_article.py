from backend.rss_config import load_outlets
from backend.scripts.extract_image_article import extract_article


BBC_HTML = """<html>
  <head>
    <meta property="og:title" content="BBC Story Title">
    <link rel="canonical" href="https://www.bbc.com/news/example-story">
  </head>
  <body>
    <article>
      <img
        sizes="(min-width: 1280px) 50vw, (min-width: 1008px) 66vw, 96vw"
        srcset="https://ichef.bbci.co.uk/news/240/cpsprodpb/cf4d/live/9b03db00-537b-11f1-a9c1-691d150de147.jpg.webp 240w,https://ichef.bbci.co.uk/news/320/cpsprodpb/cf4d/live/9b03db00-537b-11f1-a9c1-691d150de147.jpg.webp 320w,https://ichef.bbci.co.uk/news/480/cpsprodpb/cf4d/live/9b03db00-537b-11f1-a9c1-691d150de147.jpg.webp 480w,https://ichef.bbci.co.uk/news/640/cpsprodpb/cf4d/live/9b03db00-537b-11f1-a9c1-691d150de147.jpg.webp 640w,https://ichef.bbci.co.uk/news/800/cpsprodpb/cf4d/live/9b03db00-537b-11f1-a9c1-691d150de147.jpg.webp 800w,https://ichef.bbci.co.uk/news/1024/cpsprodpb/cf4d/live/9b03db00-537b-11f1-a9c1-691d150de147.jpg.webp 1024w,https://ichef.bbci.co.uk/news/1536/cpsprodpb/cf4d/live/9b03db00-537b-11f1-a9c1-691d150de147.jpg.webp 1536w"
        src="https://ichef.bbci.co.uk/news/480/cpsprodpb/cf4d/live/9b03db00-537b-11f1-a9c1-691d150de147.jpg.webp"
        alt="BBC image"
      >
    </article>
  </body>
</html>"""


def test_bbc_article_extractor_uses_largest_srcset_image(monkeypatch):
    outlet = None
    for candidate in load_outlets():
        if candidate.outlet_id == "bbc_world":
            outlet = candidate
            break

    assert outlet is not None

    def fake_fetch_html(url: str) -> str:
        assert url == "https://www.bbc.com/news/example-story"
        return BBC_HTML

    monkeypatch.setattr(
        "backend.scripts.extract_image_article.fetch_html",
        fake_fetch_html,
    )
    monkeypatch.setattr(
        "backend.scripts.extract_image_article.tf.extract",
        lambda html, output_format="markdown": "BBC body text",
    )

    article = extract_article("https://www.bbc.com/news/example-story", outlet)

    assert article.title == "BBC Story Title"
    assert article.canonical_url == "https://www.bbc.com/news/example-story"
    assert article.image_url == "https://ichef.bbci.co.uk/news/1536/cpsprodpb/cf4d/live/9b03db00-537b-11f1-a9c1-691d150de147.jpg.webp"
    assert article.image_source == "img[srcset]"
    assert article.outlet_uses_article_image_extraction is True
