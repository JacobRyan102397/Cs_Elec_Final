from flask import Flask, render_template, request, redirect, url_for,Response,make_response,jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'cselec'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/mock_data', methods={"GET"})
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM mock_data")
    mock_data = cur.fetchall()
    cur.close()

    return make_response(jsonify(mock_data), 30)

# @app.route('/')
# def hello():
#     return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True)
