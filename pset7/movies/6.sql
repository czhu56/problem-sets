SELECT AVG(rating)
FROM movies JOIN movies ON movies.id = ratings.movies_id
WHERE year = 2012;
