from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import requests
from bs4 import BeautifulSoup
import os
import json
import csv

app = Flask(__name__)
app.secret_key = "supersecretkey"

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
                opinion = Opinion(
                    opinion_id=review.get("data-entry-id", ""),
                    author=review.select_one(".user-post__author-name").text.strip() if review.select_one(".user-post__author-name") else "Unknown",
                    score=float(review.select_one(".user-post__score-count").text.replace(",", ".").replace("/5", "").strip()) if review.select_one(".user-post__score-count") else 0.0,
                    content=review.select_one(".user-post__text").text.strip() if review.select_one(".user-post__text") else "No content",
                    publish_date=review.select_one(".user-post__published > time:nth-of-type(1)")['datetime'] if review.select_one(".user-post__published > time:nth-of-type(1)") else "Unknown"
                )
                self.reviews.append(opinion)
        
        print(f"Total reviews fetched: {len(self.reviews)}")

products = []

def save_to_json(product):
    filename = f"reviews_{product.product_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([review.__dict__ for review in product.reviews], f, ensure_ascii=False, indent=4)
    return filename

def save_to_csv(product):
    filename = f"reviews_{product.product_id}.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["opinion_id", "author", "score", "content", "publish_date"])
        writer.writeheader()
        writer.writerows([review.__dict__ for review in product.reviews])
    return filename

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/products")
def product_list():
    return render_template("products.html", products=products)

@app.route("/product/<product_id>")
def product_page(product_id):
    product = next((p for p in products if p.product_id == product_id), None)
    if not product:
        product = Product(product_id)
        product.fetch_reviews()
        products.append(product)
    return render_template("product.html", product=product)

@app.route("/search", methods=["POST"])
def search():
    product_id = request.form.get("product_id")
    if not product_id:
        flash("Please enter a product ID.")
        return redirect(url_for("home"))
    return redirect(url_for("product_page", product_id=product_id))

@app.route("/download/json/<product_id>")
def download_json(product_id):
    product = next((p for p in products if p.product_id == product_id), None)
    if product:
        filename = save_to_json(product)
        return send_file(filename, as_attachment=True)
    flash("Product not found.")
    return redirect(url_for("home"))

@app.route("/download/csv/<product_id>")
def download_csv(product_id):
    product = next((p for p in products if p.product_id == product_id), None)
    if product:
        filename = save_to_csv(product)
        return send_file(filename, as_attachment=True)
    flash("Product not found.")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
