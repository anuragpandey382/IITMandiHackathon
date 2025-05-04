import convert
import model


def watchlist_to_recommendations(watchlist, num):
    watchlist = convert.watchlist_titles_to_ids(watchlist)

    closest = model.closest_user(watchlist)
    
    print(closest)

    recs = model.recommendation_ids(closest, num)
    titles = convert.titles_from_recs(recs)

    imdbs = convert.imdb_from_recommendations(titles)

    return imdbs

if __name__ == "__main__":

    movie_ratings = {
        "You Are My Sunshine (2015)": 5.0, # You Are My Sunshine (2015) - Drama|Romance
        "5 to 7 (2014)": 5.0, # 5 to 7 (2014) - Comedy|Drama|Romance
        "Vesna (1947)": 5.0, # Vesna (1947) - Comedy|Romance
        "Afonya (1975)": 5.0, # Afonya (1975) - Comedy|Drama|Romance
        "We'll Live Till Monday (1968)": 5.0, # We'll Live Till Monday (1968) - Drama|Romance
        "The Beginning (1970)": 5.0, # The Beginning (1970) - Comedy|Romance
        "Walking the Streets of Moscow (1963)": 5.0, # Walking the Streets of Moscow (1963) - Comedy|Romance
        "Don't Grieve! (1969)": 5.0, # Don't Grieve! (1969) - Comedy|Drama|Romance
        "Oblomov (1980)": 5.0, # Oblomov (1980) - Comedy|Drama|Romance
        "Holiday (2014)": 4.0, # Holiday (2014) - Action|Romance|Thriller
        "Hecate (1982)": 5.0  # Hecate (1982) - Drama|Romance
    }

    #print(convert.watchlist_titles_to_ids(movie_ratings))

    recs = watchlist_to_recommendations(movie_ratings, 30)

    print(recs)
    # x = convert.get_imdb_ids_from_titles(recs)
    # print(x)