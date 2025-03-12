import requests
from bs4 import BeautifulSoup
import json

PRODUCT_ID = "99105003"
URL = f"https://www.ceneo.pl/{PRODUCT_ID}#tab=reviews"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

response = requests.get(URL, headers=HEADERS)
if response.status_code != 200:
    print("Помилка завантаження сторінки")
    exit()

soup = BeautifulSoup(response.text, "html.parser")

first_review = soup.select_one(".js_product-review")
if not first_review:
    print("No reviews found")
    exit()

review_data = {
    "opinion_id": first_review.get("data-entry-id", ""),
    "author": first_review.select_one(".user-post__author-name").text.strip() if first_review.select_one(".user-post__author-name") else "",
    "score": first_review.select_one(".user-post__score-count").text.strip() if first_review.select_one(".user-post__score-count") else "",
    "content": first_review.select_one(".user-post__text").text.strip() if first_review.select_one(".user-post__text") else "",
    "advantages": [li.text.strip() for li in first_review.select(".review-feature__title--positives ~ .review-feature__item")] if first_review.select(".review-feature__title--positives ~ .review-feature__item") else [],
    "disadvantages": [li.text.strip() for li in first_review.select(".review-feature__title--negatives ~ .review-feature__item")] if first_review.select(".review-feature__title--negatives ~ .review-feature__item") else [],
    "helpful": first_review.select_one(".vote-yes .js_product-review-vote")['data-total-vote'] if first_review.select_one(".vote-yes .js_product-review-vote") else "0",
    "unhelpful": first_review.select_one(".vote-no .js_product-review-vote")['data-total-vote'] if first_review.select_one(".vote-no .js_product-review-vote") else "0",
    "publish_date": first_review.select_one(".user-post__published > time:nth-of-type(1)")['datetime'] if first_review.select_one(".user-post__published > time:nth-of-type(1)") else "",
    "purchase_date": first_review.select_one(".user-post__published > time:nth-of-type(2)")['datetime'] if first_review.select_one(".user-post__published > time:nth-of-type(2)") else ""
}

with open("review.json", "w", encoding="utf-8") as f:
    json.dump(review_data, f, ensure_ascii=False, indent=4)

print("Firts review saved in 'review.json'")
