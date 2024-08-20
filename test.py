import unittest
import warnings
from api import app

class TestApp(unittest.TestCase):
    def setUP(self):
        app.config["TESTING"] = True
        self.app = app.test_client()

        warnings.simplefilter("ignore", category=DeprecationWarning)

    def test_index(self):
        response = self.app.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "index.html")

    def test_first_name(self):
        response = self.app.get("/first_name")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("tabudo" in response.data.decode())

    # def test_add_form(self):
    #     response = self.app.get("/add_form")
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data.decode(), "add.html")
    
    # def test_add(self):
    #     response = self.app.get("/add")
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data.decode(), "index.html")

    # def test_edit(self):
    #     response = self.app.get("/edit/<int:id")
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data.decode(), "index.html")

    # def test_delete(self):
    #     response = self.app.get("/delete/<int:id>")
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.data.decode(), "index.html")

    if __name__ == '__main__':
        unittest.main()