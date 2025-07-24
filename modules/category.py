import pandas as pd
def get_category_recommendations(product_id, df, top_k=2):
    target = df[df['productID'] == product_id]
    if target.empty:
        return pd.DataFrame()

    product = target.iloc[0]
    subcat = product['subCategoryName']
    cat = product['categoryName']

    # Get a larger candidate pool, not sorted
    subcat_matches = df[
        (df['subCategoryName'] == subcat) &
        (df['productID'] != product_id)
    ]

    reason = "Matched by subcategory"
    candidates = subcat_matches.copy()

    # Fallback to category
    if len(candidates) < top_k:
        cat_matches = df[
            (df['categoryName'] == cat) &
            (df['productID'] != product_id)
        ]
        candidates = pd.concat([candidates, cat_matches]).drop_duplicates('productID')
        reason = "Matched by category"

    # ✅ Truly randomize selection (fixes repetition)
    sampled = candidates.sample(n=min(top_k, len(candidates)), random_state=None)
    sampled['reason'] = reason
    return sampled[['productID', 'productName', 'categoryName', 'subCategoryName', 'mediaName', 'reason']]
