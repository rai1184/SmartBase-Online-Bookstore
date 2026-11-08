# backend/app/utils/scoring.py
from contextlib import closing
from app.database.connection import get_db_connection

# Type abstraction hierarchy
class GenreTAH:
    def __init__(self):
        self.genre_map = {}  # genre_name -> parent_name
        self.load_hierarchy()

    # Load TAH from the Genre table
    def load_hierarchy(self):
        try:
            with closing(get_db_connection()) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute("""
                        SELECT 
                            Child.genre_name AS child,
                            Parent.genre_name AS parent
                        FROM Genres Child
                        LEFT JOIN Genres Parent ON Child.genre_parent_id = Parent.genre_id
                        """)
                    rows = cursor.fetchall()
                    for child, parent in rows:
                        self.genre_map[child] = parent
        except Exception:
            # Fallback if DB isn't ready during init
            pass

    # Returns all ancestors of a genre
    def get_ancestors(self, genre):
        ancestors = []
        current = genre
        while current in self.genre_map and self.genre_map[current]:
            parent = self.genre_map[current]
            ancestors.append(parent)
            current = parent
        return ancestors

    # Tree distance, or lowest common ancestor, between two genres
    def calculate_distance(self, genre_a, genre_b):
        if not genre_a or not genre_b or genre_a == "All" or genre_b == "All":
            return 1.0  # Max distance penalty if missing

        if genre_a == genre_b:
            return 0.0

        chain_a = [genre_a] + self.get_ancestors(genre_a)
        chain_b = [genre_b] + self.get_ancestors(genre_b)

        distance = 0
        lca_found = False

        # Calculate distance between the two genres
        # Check each ancestor of A, starting at A
        # If it is in the ancestor list of B, that is the lowest ancestor
        # The distance between them is how many ancestors away from A the match was, plus how many ancestors away from B the match was
        for i, a in enumerate(chain_a):
            if a in chain_b:
                j = chain_b.index(a)
                distance = i + j
                lca_found = True
                break

        if not lca_found:
            return 1.0

        # Normalize distance (assuming a max tree depth hop of 4)
        return min(distance / 4.0, 1.0)


def score_alternative(book, target_params, relaxation_flags, genre_tah):
    distance = 0.0
    
    max_price = target_params.get("max_price")
    publication_year = target_params.get("publication_year")
    min_rating = target_params.get("min_rating")  
    target_genre = target_params.get("genre")     
    
    relax_price = relaxation_flags.get("relax_price", False)
    relax_year = relaxation_flags.get("relax_year", False)
    relax_rating = relaxation_flags.get("relax_rating", False)  
    relax_genre = relaxation_flags.get("relax_genre", False)    

    # Price distance
    if relax_price and max_price:
        try:
            target_p = float(max_price)
            actual_p = book["msrp"]
            price_diff = abs(actual_p - target_p)
            distance += min(price_diff / 50.0, 1.0) * 0.25
        except ValueError:
            pass

    # Publication year distance
    if relax_year and publication_year:
        try:
            target_y = int(publication_year)
            if book["publication_date"]:
                actual_y = int(book["publication_date"][:4])
                year_diff = abs(actual_y - target_y)
                distance += min(year_diff / 20.0, 1.0) * 0.25
        except ValueError:
            pass
            
    # Rating distance
    if relax_rating and min_rating:
        try:
            target_r = float(min_rating)
            actual_r = book["rating"]
            
            if actual_r is not None:
                if actual_r < target_r:
                    # Penalize the gap between actual rating and target minimum
                    rating_gap = target_r - actual_r
                    distance += (rating_gap / 5.0) * 0.25  # Normalized across 5-star scale
            else:
                # Unrated books get a minor penalty when rating constraint is relaxed
                distance += 0.2 * 0.25
        except ValueError:
            pass

    # Genre distance via TAH
    if relax_genre and target_genre and target_genre != "All":
        actual_genre = book["genre"]
        genre_dist = genre_tah.calculate_distance(target_genre, actual_genre)
        distance += genre_dist * 0.25
    
    return distance


def rank_alternatives(formatted_alternatives, exact_isbns, target_params, relaxation_flags):
    scored_alternatives = []
    genre_tah = GenreTAH()
    
    for book in formatted_alternatives:
        if book["isbn"] not in exact_isbns:
            book["similarity_score"] = score_alternative(book, target_params, relaxation_flags, genre_tah)
            scored_alternatives.append(book)

    scored_alternatives.sort(key=lambda x: x["similarity_score"])
    return scored_alternatives