from utils import save_products, load_products, generate_charts
import os
import json
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from models import Product, Opinion

PRODUCTS_FILE = 'products.json'

app = Flask(__name__)

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
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump([{
            "product_id": product.product_id,
            "name": product.name,  
            "reviews": [review.to_dict() for review in product.reviews]
        } for product in products], f, indent=4, ensure_ascii=False)

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

@app.route("/about")
def about():
    return render_template("about.html")