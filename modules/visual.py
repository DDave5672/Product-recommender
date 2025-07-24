# modules/visual.py
import pandas as pd
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from model.extract_clip_features import extract_clip_feature

# Load data
product_df = pd.read_csv("data/productList.csv")
def get_cat_df():
    cat_df = pd.read_csv("data/catalog_embeddings.csv")
    cat_df["embedding"] = cat_df["embedding"].apply(eval).apply(np.array)
    return cat_df

manual_df = pd.read_csv("data/manual_visual_recommendations.csv")

manual_map = {
    str(row["anchor"]).replace(".jpg", ""): [
        str(row["recommendation_1"]).replace(".jpg", ""),
        str(row["recommendation_2"]).replace(".jpg", ""),
        str(row["recommendation_3"]).replace(".jpg", "")
    ]
    for _, row in manual_df.iterrows()
}


# ✅ Lazy model load
projection_model = None
def lazy_load_model():
    global projection_model
    if projection_model is None:
        projection_model = torch.jit.load("model/trained_visual_model_scripted.pt")
        projection_model.eval()

_cat_df = None

def get_cat_df():
    global _cat_df
    if _cat_df is None:
        print("[DEBUG] Loading catalog_embeddings.csv...")
        _cat_df = pd.read_csv("data/catalog_embeddings.csv")
        _cat_df["embedding"] = _cat_df["embedding"].apply(eval).apply(np.array)
    return _cat_df


def get_visual_recommendations(product_id, top_k=2):
    product_id = str(product_id)

    # ✅ Manual recs — force top_k limit
    if product_id in manual_map:
        print(f"[DEBUG] Manual recs for {product_id}: {manual_map[product_id]}")
        all_ids = manual_map[product_id]
        rec_ids = manual_map[product_id][:top_k] # ✅ LIMIT HERE
        recs = [
            (rid, product_df[product_df["productID"] == int(rid)]["productName"].values[0])
            for rid in rec_ids
            if not product_df[product_df["productID"] == int(rid)].empty
        ]
        return recs

    # Fallback to model
    lazy_load_model()
    image_path = f"static/images/{product_id}.jpg"
    feat = extract_clip_feature(image_path)
    with torch.no_grad():
        emb = projection_model(feat.unsqueeze(0)).numpy()[0]

    cat_df = get_cat_df()
    sims = cosine_similarity([emb], np.vstack(cat_df["embedding"]))[0]
    top_idx = sims.argsort()[::-1]

    recs = []
    for i in top_idx:
        pid = str(cat_df.iloc[i]["product_id"])
        if pid != product_id:
            row = product_df[product_df["productID"] == int(pid)]
            if not row.empty:
                recs.append((pid, row["productName"].values[0]))
        if len(recs) >= top_k:
            break

    return recs

