# Calculate similarity score for a book
def score_alternative(book, target_params, relaxation_flags):

    distance = 0.0
    
    max_price = target_params.get("max_price")
    publication_year = target_params.get("publication_year")
    
    relax_price = relaxation_flags.get("relax_price", False)
    relax_year = relaxation_flags.get("relax_year", False)

    # Price distance
    if relax_price and max_price:
        try:
            target_p = float(max_price)
            actual_p = book["msrp"]
            # Normalize difference,  max reasonable price is $50
            price_diff = abs(actual_p - target_p)
            distance += min(price_diff / 50.0, 1.0) * 0.5
        except ValueError:
            pass

    # Publication year distance
    if relax_year and publication_year:
        try:
            target_y = int(publication_year)
            if book["publication_date"]:
                actual_y = int(book["publication_date"][:4])
                year_diff = abs(actual_y - target_y)
                # Normalize difference (assuming max reasonable year delta is 20 years)
                distance += min(year_diff / 20.0, 1.0) * 0.5
        except ValueError:
            pass
            
    # Future TAH genre distance logic can be cleanly added here!
    
    return distance

# Filter out duplicates, create similiarity scores, then sort
def rank_alternatives(formatted_alternatives, exact_isbns, target_params, relaxation_flags):
    scored_alternatives = []
    
    for book in formatted_alternatives:
        # Exclude books that are already shown in exact matches
        if book["isbn"] not in exact_isbns:
            book["similarity_score"] = score_alternative(book, target_params, relaxation_flags)
            scored_alternatives.append(book)

    # Sort alternatives by similarity score (lowest distance = best alternative match)
    scored_alternatives.sort(key=lambda x: x["similarity_score"])
    
    return scored_alternatives