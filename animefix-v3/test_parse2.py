import requests
from bs4 import BeautifulSoup

url = "https://meusanimes.blog/e/avatar-aang-the-last-airbender-2026/"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.text, 'lxml')

print("Player Sist:")
print(soup.select_one('.player_sist'))
