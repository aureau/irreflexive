# using existing logic to download html files using links
import requests

def dl_html(link):
    try:
        filename = 'test-article.html'
        response = requests.get(link)
        if response.status_code == 200:
            html = response.text
            print("grabbed html")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"HTML file saved to {filename}")
            return filename
        else:
            print(f"Failed to retrieve the page. Status code: {response.status_code}")
    except Exception as e:
        print({e})