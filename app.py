# app.py
from flask import Flask, render_template, request
import os
import pandas as pd
from modules.category import get_category_recommendations
from modules.visual import get_visual_recommendations
from modules.purchase_history import get_purchase_recommendations


app = Flask(__name__)
df = pd.read_csv("data/productList.csv")

def get_image_path(product_id):
    return f"/static/images/{product_id}.jpg"

@app.route("/", methods=["GET", "POST"])
def index():
    recs = {"target": None, "recommendations": []}
    product_id = None
    seen_ids = set()
    def add(pid, name, reason):
        if pid in seen_ids or pid == product_id:
            return
        recs["recommendations"].append({
            "id": pid,
            "name": name,
            "image": get_image_path(pid),
            "reason": reason
        })
        seen_ids.add(pid)

    if request.method == "POST":
        query = request.form.get("query").strip()
        if query.isdigit():
            product_id = query
        else:
            match = df[df["productName"].str.contains(query, case=False)]
            if match.empty:
                return render_template("index.html", error="No product found", recs=recs)
            product_id = str(match.iloc[0]["productID"])
            recs["matched_name"] = match.iloc[0]["productName"]

        if not os.path.exists(f"static/images/{product_id}.jpg"):
            return render_template("index.html", error="Product image not found", recs=recs)

        target = df[df["productID"] == int(product_id)].iloc[0]
        recs["target"] = {
            "id": product_id,
            "name": target["productName"],
            "image": get_image_path(product_id)
        }

        

        for pid, name in get_visual_recommendations(product_id):
            add(str(pid), name, "🎨 Visual")
        
        # 🧩 Subcategory Recommendations
        subcat_recs = get_category_recommendations(int(product_id), df, top_k=5)  # ask for extras in case of skips
        subcat_count = 0
        visual_recs = get_visual_recommendations(product_id)
        visual_ids = set(pid for pid, _ in visual_recs)  # collect visual rec product IDs

        for _, row in subcat_recs.iterrows():
            sid = str(row["productID"])
            if sid not in visual_ids:
                add(sid, row["productName"], "🧩 Matched by Subcategory")
                subcat_count += 1
            if subcat_count >= 2:
                break

        # 🛒 Purchase history recs
        purchase_recs = get_purchase_recommendations(product_id)

        if not purchase_recs:
            print(f"[INFO] No purchase recs found for {product_id}, using subcategory fallback.")
            # Fallback to same subcategory products as "Bought Together"
            sub_fallback = get_category_recommendations(int(product_id), df, top_k=5)
            fallback_count = 0
            for _, row in sub_fallback.iterrows():
                fallback_id = str(row["productID"])
                if fallback_id != product_id:
                    add(fallback_id, row["productName"], "🛒 Related by Subcategory")
                    fallback_count += 1
                if fallback_count >= 2:
                    break
        else:
            for pid, pname in purchase_recs:
                add(pid, pname, "🛒 Bought Together")


    return render_template("index.html", recs=recs)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

