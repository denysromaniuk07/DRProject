import os
import json
import matplotlib.pyplot as plt
from models import Product, Opinion

PRODUCTS_FILE = "products.json"

def save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump([
            {
                "product_id": product.product_id,
                "name": product.name,
                "reviews": [review.to_dict() for review in product.reviews]
            } for product in products
        ], f, indent=4, ensure_ascii=False)

def load_products():
    
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [
                Product(
                    p["product_id"],
                    p.get("name", "Unknown Product"),
                    [Opinion(
                        opinion_id=r["opinion_id"],
                        author=r["author"],
                        recommendation=r["recommendation"],
                        score=r["score"],
                        content=r["content"],
                        pros=r["pros"],
                        cons=r["cons"],
                        helpful=r["helpful"],
                        unhelpful=r["unhelpful"],
                        publish_date=r["publish_date"],
                        purchase_date=r["purchase_date"]
                    ) for r in p["reviews"]]
                ) for p in data
            ]
    return []

def generate_charts(product):
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

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color=['red', 'orange', 'gray', 'lightgreen', 'green'])
    plt.xlabel("Stars")
    plt.ylabel("Number of Reviews")
    plt.title("Review Count by Star Rating")
    plt.savefig(f"static/review_bar_{product.product_id}.png")
    plt.close()
