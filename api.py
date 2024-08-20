from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import re
import dicttoxml  # To convert dictionaries to XML

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'cselec'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Read (Retrieve)
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM mock_data")
    mock_data = cur.fetchall()
    cur.close()

    return render_template('index.html', mock_data=mock_data)

# Route to render the add form
@app.route('/add_form', methods=['GET'])
def add_form():
    return render_template('add.html')

# Create (Add) new record
@app.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        gender = request.form['gender']
        ip_address = request.form['ip_address']

        # Input validation
        if not first_name or not last_name or not email:
            flash("First Name, Last Name, and Email are required!")
            return redirect(url_for('add_form'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid Email Address!")
            return redirect(url_for('add_form'))

        if gender not in ['Male', 'Female', 'Other']:
            flash("Invalid Gender!")
            return redirect(url_for('add_form'))

        if not re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", ip_address):
            flash("Invalid IP Address!")
            return redirect(url_for('add_form'))

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO mock_data (first_name, last_name, email, gender, ip_address) VALUES (%s, %s, %s, %s, %s)",
                        (first_name, last_name, email, gender, ip_address))
            mysql.connection.commit()
            flash("Record successfully added!")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error occurred: {str(e)}")
        finally:
            cur.close()

        return redirect(url_for('index'))

# Update
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        gender = request.form['gender']
        ip_address = request.form['ip_address']

        # Input validation
        if not first_name or not last_name or not email:
            flash("First Name, Last Name, and Email are required!")
            return redirect(url_for('edit'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid Email Address!")
            return redirect(url_for('edit'))

        if gender not in ['Male', 'Female', 'Other']:
            flash("Invalid Gender!")
            return redirect(url_for('edit'))

        if not re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", ip_address):
            flash("Invalid IP Address!")
            return redirect(url_for('edit'))

        try:
            cur.execute("UPDATE mock_data SET first_name=%s, last_name=%s, email=%s, gender=%s, ip_address=%s WHERE id=%s", (first_name, last_name, email, gender, ip_address, id))
            mysql.connection.commit()
            flash("Record successfully updated!")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error occurred: {str(e)}")
        finally:
            cur.close()

        return redirect(url_for('index'))
    else:
        cur.execute("SELECT * FROM mock_data WHERE id=%s", (id,))
        record = cur.fetchone()
        cur.close()
        return render_template('edit.html', record=record)

# Delete
@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    cur = mysql.connection.cursor()

    try:
        cur.execute("DELETE FROM mock_data WHERE id=%s", (id,))
        mysql.connection.commit()
        flash("Record successfully deleted!")
    except Exception as e:
        mysql.connection.rollback()
        flash(f"Error occurred: {str(e)}")
    finally:
        cur.close()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
