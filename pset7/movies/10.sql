SELECT name 
FROM people 
JOIN directors ON directors.person_id = people_id
JOIN ratings ON directors.movie_id = ratings.movie_id
WHERE rating >= 9.0;