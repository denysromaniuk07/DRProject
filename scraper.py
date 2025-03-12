from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import json
import csv
import matplotlib.pyplot as plt

app = Flask(__name__)

def get_product_reviews(product_id):
    """Fetches all reviews for a given product ID from Ceneo.pl."""
    base_url = f"https://www.ceneo.pl/{product_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    all_reviews = []
    response = requests.get(base_url + "#tab=reviews", headers=headers)
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    page_numbers = [int(a.text) for a in soup.select(".pagination__item") if a.text.isdigit()]
    max_page = max(page_numbers) if page_numbers else 1
    
    for page in range(1, max_page + 1):
        url = f"{base_url}/opinie-{page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
        
        soup = BeautifulSoup(response.text, "html.parser")
        reviews = soup.select(".js_product-review")
        if not reviews:
            break
        
        for review in reviews:
            review_data = {
                "opinion_id": review.get("data-entry-id", ""),
                "author": review.select_one(".user-post__author-name").text.strip() if review.select_one(".user-post__author-name") else "",
                "score": float(review.select_one(".user-post__score-count").text.replace(",", ".").replace("/5", "").strip()) if review.select_one(".user-post__score-count") else 0.0,
                "content": review.select_one(".user-post__text").text.strip() if review.select_one(".user-post__text") else "",
                "publish_date": review.select_one(".user-post__published > time:nth-of-type(1)")['datetime'] if review.select_one(".user-post__published > time:nth-of-type(1)") else ""
            }
            all_reviews.append(review_data)
    
    return all_reviews

@app.route("/", methods=["GET", "POST"])
def index():
    reviews = []
    if request.method == "POST":
        product_id = request.form.get("product_id")
        reviews = get_product_reviews(product_id)
    return render_template("index.html", reviews=reviews)

if __name__ == "__main__":
    app.run(debug=True)
