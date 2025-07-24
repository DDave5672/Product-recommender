# modules/purchase_history.py
import pandas as pd
import os
import pickle
from collections import defaultdict
from difflib import get_close_matches

def default_dict_int():
    return defaultdict(int)

# Load product data
product_df = pd.read_csv("data/productList.csv")
purchase_df = pd.read_csv("data/filtered_purchase_history.csv")

# Build name-ID map
product_df["full_name"] = (
    product_df["productName"].fillna('') + " " + product_df["description"].fillna('')
).str.lower().str.strip()
name_to_id = dict(zip(product_df["full_name"], product_df["productID"]))
id_to_name = dict(zip(product_df["productID"], product_df["productName"]))

# Fuzzy match mapping
def fuzzy_map(name):
    matches = get_close_matches(name, name_to_id.keys(), n=1, cutoff=0.75)
    return name_to_id[matches[0]] if matches else None

purchase_df["normalized_name"] = purchase_df["Product_name"].str.lower().str.strip()
purchase_df["product_id"] = purchase_df["normalized_name"].apply(fuzzy_map)
purchase_df = purchase_df.dropna(subset=["product_id"])

# Build co-occurrence matrix
def build_co_occurrence_matrix():
    print("[INFO] Building co-occurrence matrix from scratch...")
    basket = purchase_df.groupby("pk_userID")["product_id"].apply(list).reset_index(name="products")
    co_matrix = defaultdict(default_dict_int)
    for products in basket["products"]:
        unique = list(set(products))
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                a, b = unique[i], unique[j]
                co_matrix[a][b] += 1
                co_matrix[b][a] += 1
    return co_matrix

# Lazy loading with pickle cache
_matrix_path = "data/co_matrix.pkl"
_co_matrix = None

def get_co_matrix():
    global _co_matrix
    if _co_matrix is not None:
        return _co_matrix
    
    if os.path.exists(_matrix_path):
        print("[INFO] Loading co-occurrence matrix from cache...")
        with open(_matrix_path, "rb") as f:
            _co_matrix = pickle.load(f)
    else:
        _co_matrix = build_co_occurrence_matrix()
        with open(_matrix_path, "wb") as f:
            pickle.dump(_co_matrix, f)

    return _co_matrix

# Recommendation interface
def get_purchase_recommendations(product_id, top_k=2):
    print(f"[DEBUG] No co-purchase data for {product_id}")
    product_id = int(product_id)
    co_matrix = get_co_matrix()

    if product_id not in co_matrix:
        return []

    related = sorted(co_matrix[product_id].items(), key=lambda x: -x[1])[:top_k]
    return [(str(int(pid)), id_to_name.get(pid, "Unknown")) for pid, _ in related]
