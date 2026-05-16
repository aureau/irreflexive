import os
import requests
import sys

# links_path = 'left-links.txt'
links_path = 'right-links.txt'
# output_folder = '../webpages/left-webpages'
output_folder = '../webpages/right-webpages'
if os.path.exists(output_folder):
    files = os.listdir(output_folder)
    if files:
        print("already existing dir, deleting...")
        for fn in files:
            path = os.path.join(output_folder, fn)
            try:
                # gemini wanted me to check if file isnt a subdir???? lol
                if os.path.isfile(path):
                    os.remove(path)
                    print("removed files")
            except Exception as e:
                print({e})    
else:
    print("doesnt exist")
    sys.exit()    

with open(links_path, 'r') as file:
    for l, link in enumerate(file):
        url = link.strip()        
        if not url:
            continue
        try: 
            response = requests.get(url)
            if response.status_code == 200:
                html = response.text
                filename = f"healthcare-article_{l + 1}.html"
                file_save_path = os.path.join(output_folder, filename)
                with open(file_save_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"Saved filename {filename} to {file_save_path}")

            else:
                print(f"{response.status_code}. Failed to retrieve article.")
        except Exception as e:
            print(f"Failed for {url}: {e}")