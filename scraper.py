import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = "supersecretkey"

PRODUCTS_FILE = "products.json"


class Opinion:
    """Represents a single product review."""
    def __init__(self, opinion_id, author, recommendation, score, content, pros, cons, helpful, unhelpful, publish_date, purchase_date):
        self.opinion_id = opinion_id
        self.author = author
        self.recommendation = recommendation
        self.score = score
        self.content = content
        self.pros = pros
        self.cons = cons
        self.helpful = helpful
        self.unhelpful = unhelpful
        self.publish_date = publish_date
        self.purchase_date = purchase_date

    def to_dict(self):
        """Convert object to dictionary for JSON storage."""
        return self.__dict__

class Product:
    """Represents a product with its reviews."""
    """Represents a product with its reviews."""
    def __init__(self, product_id, name=None, reviews=None):
        self.product_id = product_id
        self.name = name
        self.reviews = reviews if reviews else []

    def number_of_opinions(self):
        """Returns the total number of opinions."""
        return len(self.reviews)

    def advantages_count(self):
        """Returns the number of reviews that contain advantages."""
        return sum(1 for review in self.reviews if review.pros)

    def disadvantages_count(self):
        """Returns the number of reviews that contain disadvantages."""
        return sum(1 for review in self.reviews if review.cons)

    def fetch_reviews(self):
        """Fetches reviews from Ceneo.pl"""
        base_url = f"https://www.ceneo.pl/{self.product_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
        response = requests.get(base_url + "#tab=reviews", headers=headers)
        if response.status_code != 200:
            print("Error: Unable to fetch reviews")
            return
        
        soup = BeautifulSoup(response.text, "html.parser")

        # Отримуємо назву товару
        product_name_tag = soup.select_one("h1.product-top__product-info__name, h1.long-name")
        self.name = product_name_tag.text.strip() if product_name_tag else "Unknown Product"

        page_numbers = [int(a.text) for a in soup.select(".pagination__item") if a.text.isdigit()]
        max_page = max(page_numbers) if page_numbers else 1

        if not self.name or self.name == "Unknown Product":
            self.name = product_name_tag.text.strip() if product_name_tag else self.name

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
                opinion = Opinion(
                    opinion_id=review.get("data-entry-id", ""),
                    author=review.select_one(".user-post__author-name").text.strip() if review.select_one(".user-post__author-name") else "Unknown",
                    recommendation=review.select_one(".user-post__author-recommendation > em").text.strip() if review.select_one(".user-post__author-recommendation > em") else "",
                    score=float(review.select_one(".user-post__score-count").text.replace(",", ".").replace("/5", "").strip()) if review.select_one(".user-post__score-count") else 0.0,
                    content=review.select_one(".user-post__text").text.strip() if review.select_one(".user-post__text") else "No content",
                    pros=[li.text.strip() for li in review.select(".review-feature__title--positives ~ .review-feature__item")],
                    cons=[li.text.strip() for li in review.select(".review-feature__title--negatives ~ .review-feature__item")],
                    helpful=int(review.select_one(".vote-yes .js_product-review-vote").text.strip() if review.select_one(".vote-yes .js_product-review-vote") else "0"),
                    unhelpful=int(review.select_one(".vote-no .js_product-review-vote").text.strip() if review.select_one(".vote-no .js_product-review-vote") else "0"),
                    publish_date=review.select_one(".user-post__published > time:nth-of-type(1)")["datetime"] if review.select_one(".user-post__published > time:nth-of-type(1)") else "",
                    purchase_date=review.select_one(".user-post__published > time:nth-of-type(2)")["datetime"] if review.select_one(".user-post__published > time:nth-of-type(2)") else ""
                )
                self.reviews.append(opinion)
        
        print(f"Total reviews fetched: {len(self.reviews)}")
        save_products()

    def advantages_count(self):
        """Returns the number of reviews that mention advantages."""
        return sum(1 for review in self.reviews if review.pros)

    def disadvantages_count(self):
        """Returns the number of reviews that mention disadvantages."""
        return sum(1 for review in self.reviews if review.cons)

    def average_score(self):
        """Returns the average score of the product or 0 if no reviews."""
        if not self.reviews:
            return 0
        return round(sum(review.score for review in self.reviews) / len(self.reviews), 1)

def generate_charts(product):
    """Generates pie and bar charts for product reviews."""
    if not os.path.exists("static"):
        os.makedirs("static")

    scores = [review.score for review in product.reviews]
    score_counts = {i: scores.count(i) for i in range(1, 6)}

    labels = ["1★", "2★", "3★", "4★", "5★"]
    values = [score_counts.get(i, 0) for i in range(1, 6)]
    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=['red', 'orange', 'gray', 'lightgreen', 'green'], startangle=140)
    plt.title("Review Score Distribution")
    plt.savefig(f"static/review_pie_{product.product_id}.png")
    plt.close()

    # Bar Chart
    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color=['red', 'orange', 'gray', 'lightgreen', 'green'])
    plt.xlabel("Stars")
    plt.ylabel("Number of Reviews")
    plt.title("Review Count by Star Rating")
    plt.savefig(f"static/review_bar_{product.product_id}.png")
    plt.close()

@app.route("/product/<product_id>/charts")
def product_charts(product_id):
    """Route to generate and display product charts."""
    product = next((p for p in products if p.product_id == product_id), None)
    if not product:
        return "Product not found", 404

    generate_charts(product)
    return render_template("charts.html", product=product)


@app.route("/download/<filetype>/<product_id>")
def download_file(filetype, product_id):
    """Downloads JSON, CSV, or XLSX file with product reviews."""
    product = next((p for p in products if p.product_id == product_id), None)
    if not product:
        return "Product not found", 404

    filename = f"reviews_{product_id}.{filetype}"
    df = pd.DataFrame([review.to_dict() for review in product.reviews])

    if filetype == "json":
        df.to_json(filename, orient="records", indent=4, force_ascii=False)
    elif filetype == "csv":
        df.to_csv(filename, index=False)
    elif filetype == "xlsx":
        df.to_excel(filename, index=False)
    else:
        return "Invalid file type", 400

    return send_file(filename, as_attachment=True)


def save_products():
    """Saves products to a JSON file."""
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump([{"product_id": product.product_id, "reviews": [review.to_dict() for review in product.reviews]} for product in products], f, indent=4)

def load_products():
    """Loads products from a JSON file."""
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Product(p["product_id"], [Opinion(**r) for r in p["reviews"]]) for p in data]
    return []

products = load_products()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/products")
def product_list():
    return render_template("products.html", products=products)

@app.route("/extract", methods=["GET", "POST"])
def extract():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        if not product_id:
            flash("Please enter a valid product ID.", "danger")
            return redirect(url_for("extract"))
        return redirect(url_for("product_page", product_id=product_id))
    return render_template("extract.html")

@app.route("/product/<product_id>")
def product_page(product_id):
    product = next((p for p in products if p.product_id == product_id), None)
    if not product:
        product = Product(product_id)
        product.fetch_reviews()
        products.append(product)
        save_products()
    return render_template("product.html", product=product)

if __name__ == "__main__":
    app.run(debug=True)
