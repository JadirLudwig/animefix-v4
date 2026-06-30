import requests
from bs4 import BeautifulSoup

url = "https://meusanimes.blog/e/avatar-aang-the-last-airbender-2026/"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.text, 'lxml')

print("Iframes:")
for iframe in soup.find_all('iframe'):
    print(iframe.get('src'))

print("\nVideo players/options:")
for opt in soup.select('.player_nav li, .player-options li, ul#playeroptionsul li'):
    print(opt.get('data-post'), opt.get('data-nume'), opt.get('data-type'), opt.text.strip())

print("\nLinks with mp4/m3u8:")
for a in soup.find_all('a', href=True):
    if '.mp4' in a['href'] or '.m3u8' in a['href']:
        print(a['href'])
