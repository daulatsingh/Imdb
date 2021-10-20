import unittest
from main import app, db
import json


class BucketlistTestCase(unittest.TestCase):

    '''
    Admin: username:"dsingh@gmail.com", password:"fynd"
    User : username:"user1@gmail.com", password:"fynd"
    '''

    USERNAME = "dsingh@gmail.com"
    PASSWORD = "fynd"

    def setUp(self):

        self.app = app.test_client()
        self.db = db
        self.token = ""
        response = self.app.get('/login', auth=(self.USERNAME, self.PASSWORD))
        print(self.USERNAME)
        self.token = json.loads(response.data.decode("utf-8"))["token"]


    def test_successful_addmovie(self):

        payload = {
                    "99popularity": 85.0,
                    "director": "David Lean",
                    "genre": [
                      "Adventure",
                      " Biography",
                      " Drama",
                      " History",
                      " War"
                    ],
                    "imdb_score": 8.5,
                    "name": "Lawrence of Arabia"
                  }
        response = self.app.post('/movie', headers={"x-access-token":self.token,
                                                    "Content-Type":"application/json"},
                                    data=json.dumps(payload))
        self.assertEqual(200, response.status_code)

    def test_successful_search_movie(self):

        movie_name = "Lawrence of Arabia"
        response = self.app.get('/movie/{}'.format(movie_name), headers={"x-access-token":self.token,
                                                    "Content-Type":"application/json"},
                                    )
        self.assertEqual(200, response.status_code)

    def test_successful_all_movies(self):

        response = self.app.get('/movies', headers={"x-access-token":self.token,
                                                    "Content-Type":"application/json"},
                                    )
        self.assertEqual(200, response.status_code)

    def test_successful_update_movie(self):

        payload = {
                    "99popularity": 85.0,
                    "director": "David Lean",
                    "genre": [
                      "Adventure",
                      " Biography",
                      " Drama",
                      " History",
                      " War"
                    ],
                    "imdb_score": 8.5,
                    "name": "King Kong"
                  }
        movie_name = "King Kong"

        response = self.app.put('/movie/{}'.format(movie_name), headers={"x-access-token":self.token,
                                                    "Content-Type":"application/json"},
                                data=json.dumps(payload))
        self.assertEqual(200, response.status_code)



if __name__ == "__main__":

    unittest.main()