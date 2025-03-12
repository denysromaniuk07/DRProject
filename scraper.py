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
    print("Error loading the page")
    exit()

soup = BeautifulSoup(response.text, "html.parser")

reviews = soup.select(".js_product-review")
if not reviews:
    print("No reviews found")
    exit()

reviews_data = []
for review in reviews:
    review_data = {
        "opinion_id": review.get("data-entry-id", ""),
        "author": review.select_one(".user-post__author-name").text.strip() if review.select_one(".user-post__author-name") else "",
        "score": review.select_one(".user-post__score-count").text.strip() if review.select_one(".user-post__score-count") else "",
        "content": review.select_one(".user-post__text").text.strip() if review.select_one(".user-post__text") else "",
        "advantages": [li.text.strip() for li in review.select(".review-feature__title--positives ~ .review-feature__item")] if review.select(".review-feature__title--positives ~ .review-feature__item") else [],
        "disadvantages": [li.text.strip() for li in review.select(".review-feature__title--negatives ~ .review-feature__item")] if review.select(".review-feature__title--negatives ~ .review-feature__item") else [],
        "helpful": review.select_one(".vote-yes .js_product-review-vote")['data-total-vote'] if review.select_one(".vote-yes .js_product-review-vote") else "0",
        "unhelpful": review.select_one(".vote-no .js_product-review-vote")['data-total-vote'] if review.select_one(".vote-no .js_product-review-vote") else "0",
        "publish_date": review.select_one(".user-post__published > time:nth-of-type(1)")['datetime'] if review.select_one(".user-post__published > time:nth-of-type(1)") else "",
        "purchase_date": review.select_one(".user-post__published > time:nth-of-type(2)")['datetime'] if review.select_one(".user-post__published > time:nth-of-type(2)") else ""
    }
    reviews_data.append(review_data)


with open("reviews.json", "w", encoding="utf-8") as f:
    json.dump(reviews_data, f, ensure_ascii=False, indent=4)

print("All reviews from the first page have been saved to 'reviews.json'")
