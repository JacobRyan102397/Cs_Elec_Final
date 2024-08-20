from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_mysqldb import MySQL
import re
import xml.etree.ElementTree as ET
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management and security

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'cselec'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Fetch results as dictionaries

mysql = MySQL(app)  # Initialize MySQL with Flask app

# Helper function to format the response in either JSON or XML
def format_response(data, response_format):
    if response_format == 'xml':
        root = ET.Element("mock_data")  # Root element for XML
        for item in data:
            record = ET.SubElement(root, "record")  # Each record as a sub-element
            for key, value in item.items():
                child = ET.SubElement(record, key)  # Add each key-value as a child
                child.text = str(value)
        xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')  # Convert tree to string
        response = make_response(xml_str)  # Create HTTP response
        response.headers['Content-Type'] = 'application/xml'  # Set content type to XML
        return response
    else:
        return jsonify(data)  # Default to JSON response

# Route to display all records (Read operation)
@app.route('/')
def index():
    cur = mysql.connection.cursor()  # Create a cursor to interact with the database
    cur.execute("SELECT * FROM mock_data")  # Fetch all records from the mock_data table
    mock_data = cur.fetchall()  # Store the results in a variable
    cur.close()  # Close the cursor

    return render_template('index.html', mock_data=mock_data)  # Render index.html with the data

# Route to render the form for adding a new record
@app.route('/add_form', methods=['GET'])
def add_form():
    return render_template('add.html')  # Render add.html form for adding data

# Route to handle form submission for adding a new record (Create operation)
@app.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':
        # Extract form data
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

        cur = mysql.connection.cursor()  # Create a cursor
        try:
            # Insert the new record into the mock_data table
            cur.execute("INSERT INTO mock_data (first_name, last_name, email, gender, ip_address) VALUES (%s, %s, %s, %s, %s)",
                        (first_name, last_name, email, gender, ip_address))
            mysql.connection.commit()  # Commit the transaction
            flash("Record successfully added!")
        except Exception as e:
            mysql.connection.rollback()  # Rollback if there is any error
            flash(f"Error occurred: {str(e)}")
        finally:
            cur.close()  # Close the cursor

        return redirect(url_for('index'))  # Redirect to the index page after adding the record

# Route to edit an existing record (Update operation)
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    cur = mysql.connection.cursor()  # Create a cursor

    if request.method == 'POST':
        # Extract form data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        gender = request.form['gender']
        ip_address = request.form['ip_address']

        # Input validation
        if not first_name or not last_name or not email:
            flash("First Name, Last Name, and Email are required!")
            return redirect(url_for('edit', id=id))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid Email Address!")
            return redirect(url_for('edit', id=id))

        if gender not in ['Male', 'Female', 'Other']:
            flash("Invalid Gender!")
            return redirect(url_for('edit', id=id))

        if not re.match(r"^(?:\d{1,3}\.){3}\d{1,3}$", ip_address):
            flash("Invalid IP Address!")
            return redirect(url_for('edit', id=id))

        try:
            # Update the record in the mock_data table
            cur.execute("""
                UPDATE mock_data 
                SET first_name=%s, last_name=%s, email=%s, gender=%s, ip_address=%s 
                WHERE id=%s
                """, (first_name, last_name, email, gender, ip_address, id))
            mysql.connection.commit()  # Commit the transaction
            flash("Record successfully updated!")
        except Exception as e:
            mysql.connection.rollback()  # Rollback if there is any error
            flash(f"Error occurred: {str(e)}")
        finally:
            cur.close()  # Close the cursor

        return redirect(url_for('index'))  # Redirect to the index page after updating the record

    cur.execute("SELECT * FROM mock_data WHERE id=%s", (id,))  # Fetch the record to edit
    record = cur.fetchone()  # Store the result in a variable
    cur.close()  # Close the cursor
    
    return render_template('edit.html', record=record)  # Render the edit.html form with the record data

# Route to delete a record (Delete operation)
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    cur = mysql.connection.cursor()  # Create a cursor

    try:
        # Delete the record from the mock_data table
        cur.execute("DELETE FROM mock_data WHERE id=%s", (id,))
        mysql.connection.commit()  # Commit the transaction
        flash("Record successfully deleted!")
    except Exception as e:
        mysql.connection.rollback()  # Rollback if there is any error
        flash(f"Error occurred: {str(e)}")
    finally:
        cur.close()  # Close the cursor

    return redirect(url_for('index'))  # Redirect to the index page after deleting the record

# Route to handle search functionality
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')  # Get the search query from the request
    filter_by = request.args.get('filter_by', 'first_name')  # Get the filter option (default to first_name)

    cur = mysql.connection.cursor()  # Create a cursor

    if query:
        # Use LIKE for partial matching in the search query
        search_query = f"SELECT * FROM mock_data WHERE {filter_by} LIKE %s"
        cur.execute(search_query, (f'%{query}%',))
        search_results = cur.fetchall()  # Store the search results
    else:
        # If no search query is provided, return all records
        cur.execute("SELECT * FROM mock_data")
        search_results = cur.fetchall()  # Store all records

    cur.close()  # Close the cursor

    return render_template('index.html', mock_data=search_results)  # Render index.html with search results

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app in debug mode
