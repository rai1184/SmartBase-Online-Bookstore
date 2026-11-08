# backend/app/utils/scoring.py

def score_alternative(book, target_params, relaxation_flags):
    distance = 0.0
    
    max_price = target_params.get("max_price")
    publication_year = target_params.get("publication_year")
    min_rating = target_params.get("min_rating")  # <--- Added
    
    relax_price = relaxation_flags.get("relax_price", False)
    relax_year = relaxation_flags.get("relax_year", False)
    relax_rating = relaxation_flags.get("relax_rating", False)  # <--- Added

    # 1. Price distance
    if relax_price and max_price:
        try:
            target_p = float(max_price)
            actual_p = book["msrp"]
            price_diff = abs(actual_p - target_p)
            distance += min(price_diff / 50.0, 1.0) * 0.33
        except ValueError:
            pass

    # 2. Publication year distance
    if relax_year and publication_year:
        try:
            target_y = int(publication_year)
            if book["publication_date"]:
                actual_y = int(book["publication_date"][:4])
                year_diff = abs(actual_y - target_y)
                distance += min(year_diff / 20.0, 1.0) * 0.33
        except ValueError:
            pass
            
    # 3. Rating distance (ONLY active when r_rating is True)
    if relax_rating and min_rating:
        try:
            target_r = float(min_rating)
            actual_r = book["rating"]
            
            if actual_r is not None:
                if actual_r < target_r:
                    # Penalize the gap between actual rating and target minimum
                    rating_gap = target_r - actual_r
                    distance += (rating_gap / 5.0) * 0.34  # Normalized across 5-star scale
            else:
                # Unrated books get a minor penalty when rating constraint is relaxed
                distance += 0.2 * 0.34
        except ValueError:
            pass
    
    return distance


def rank_alternatives(formatted_alternatives, exact_isbns, target_params, relaxation_flags):
    scored_alternatives = []
    
    for book in formatted_alternatives:
        if book["isbn"] not in exact_isbns:
            book["similarity_score"] = score_alternative(book, target_params, relaxation_flags)
            scored_alternatives.append(book)

    scored_alternatives.sort(key=lambda x: x["similarity_score"])
    return scored_alternatives