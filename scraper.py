from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import json
import csv
import matplotlib.pyplot as plt

app = Flask(__name__)

class Opinion:
    """Represents a single product review."""
    def __init__(self, opinion_id, author, score, content, publish_date):
        self.opinion_id = opinion_id
        self.author = author
        self.score = score
        self.content = content
        self.publish_date = publish_date

class Product:
    """Represents a product with its reviews."""
    def __init__(self, product_id):
        self.product_id = product_id
        self.reviews = []
    
    def fetch_reviews(self):
        base_url = f"https://www.ceneo.pl/{self.product_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }
        response = requests.get(base_url + "#tab=reviews", headers=headers)
        if response.status_code != 200:
            print("Error: Unable to fetch reviews")
            return
        
        soup = BeautifulSoup(response.text, "html.parser")
        page_numbers = [int(a.text) for a in soup.select(".pagination__item") if a.text.isdigit()]
        max_page = max(page_numbers) if page_numbers else 1
        
        for page in range(1, max_page + 1):
            url = f"{base_url}/opinie-{page}"
            print(f"Fetching: {url}")
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                break
            
            soup = BeautifulSoup(response.text, "html.parser")
            reviews = soup.select(".js_product-review")
            if not reviews:
                break
            
            for review in reviews:
                author_elem = review.select_one(".user-post__author-name")
                score_elem = review.select_one(".user-post__score-count")
                content_elem = review.select_one(".user-post__text")
                publish_date_elem = review.select_one(".user-post__published > time:nth-of-type(1)")
                
                opinion = Opinion(
                    opinion_id=review.get("data-entry-id", ""),
                    author=author_elem.text.strip() if author_elem else "Unknown",
                    score=float(score_elem.text.replace(",", ".").replace("/5", "").strip()) if score_elem else 0.0,
                    content=content_elem.text.strip() if content_elem else "No content",
                    publish_date=publish_date_elem['datetime'] if publish_date_elem else "Unknown"
                )
                self.reviews.append(opinion)
        
        print(f"Total reviews fetched: {len(self.reviews)}")

@app.route("/", methods=["GET", "POST"])
def index():
    product = None
    if request.method == "POST":
        product_id = request.form.get("product_id")
        if product_id:
            product = Product(product_id)
            product.fetch_reviews()
    return render_template("index.html", product=product)

if __name__ == "__main__":
    app.run(debug=True)
