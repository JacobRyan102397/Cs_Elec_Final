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
        root = ET.Element("name")  # Root element for XML
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
    # Join name with city and job to get readable names for city and job
    cur.execute("SELECT n.idName, n.f_name, n.m_name, n.l_name, n.City_idCity, n.Job_idJob, c.PPC as city_name, j.`White color` as job_name FROM cselec.name n LEFT JOIN cselec.city c ON n.City_idCity = c.idCity LEFT JOIN cselec.job j ON n.Job_idJob = j.idJob;")
    names = cur.fetchall()  # Store the results in a variable
    cur.close()  # Close the cursor

    return render_template('index.html', name=names)  # Render index.html with the data

# Route to render the form for adding a new record (show city and job lists)
@app.route('/add_form', methods=['GET'])
def add_form():
    cur = mysql.connection.cursor()
    cur.execute("SELECT idCity, PPC FROM cselec.city")
    cities = cur.fetchall()
    cur.execute("SELECT idJob, `White color` FROM cselec.job")
    jobs = cur.fetchall()
    cur.close()
    return render_template('add.html', cities=cities, jobs=jobs)  # Render add.html form for adding data

# Route to handle form submission for adding a new record (Create operation)
@app.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':
        f_name = request.form.get('f_name')
        m_name = request.form.get('m_name')
        l_name = request.form.get('l_name')
        City_idCity = request.form.get('City_idCity')
        Job_idJob = request.form.get('Job_idJob')

        # Simple validation
        if not f_name or not l_name:
            flash("First and Last Name are required!")
            return redirect(url_for('add_form'))

        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO name (f_name, m_name, l_name, City_idCity, Job_idJob)
                VALUES (%s, %s, %s, %s, %s)
            """, (f_name, m_name, l_name, City_idCity, Job_idJob))
            mysql.connection.commit()
            flash("Record added successfully!")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Error: {str(e)}")
        finally:
            cur.close()

        return redirect(url_for('index'))


# Route to edit an existing record (Update operation)
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    cur = mysql.connection.cursor()  # Create a cursor

    if request.method == 'POST':
        # Extract form data
        f_name = request.form.get('f_name')
        m_name = request.form.get('m_name')
        l_name = request.form.get('l_name')
        City_idCity = request.form.get('City_idCity')
        Job_idJob = request.form.get('Job_idJob')

        # Input validation
        if not f_name or not l_name:
            flash("First and Last Name are required!")
            return redirect(url_for('edit', id=id))

        try:
            # Update the record in the name table
            cur.execute("""
                UPDATE name
                SET f_name=%s, m_name=%s, l_name=%s, City_idCity=%s, Job_idJob=%s
                WHERE idName=%s
                """, (f_name, m_name, l_name, City_idCity, Job_idJob, id))
            mysql.connection.commit()  # Commit the transaction
            flash("Record successfully updated!")
        except Exception as e:
            mysql.connection.rollback()  # Rollback if there is any error
            flash(f"Error occurred: {str(e)}")
        finally:
            cur.close()  # Close the cursor

        return redirect(url_for('index'))  # Redirect to the index page after updating the record

    # For GET request, fetch the record and lists for select inputs
    cur.execute("SELECT * FROM name WHERE idName=%s", (id,))  # Fetch the record to edit
    record = cur.fetchone()  # Store the result in a variable
    cur.execute("SELECT idCity, PPC FROM cselec.city")
    cities = cur.fetchall()
    cur.execute("SELECT idJob, `White color` FROM cselec.job")
    jobs = cur.fetchall()
    cur.close()  # Close the cursor
    
    return render_template('edit.html', record=record, cities=cities, jobs=jobs)  # Render the edit.html form with the record data

# Route to delete a record (Delete operation)
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    cur = mysql.connection.cursor()  # Create a cursor

    try:
        # Delete the record from the name table
        cur.execute("DELETE FROM name WHERE idName=%s", (id,))
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
    filter_by = request.args.get('filter_by', 'all')  # Get the filter option (default to all)

    cur = mysql.connection.cursor()  # Create a cursor

    if query:
        # Special handling for searching city or job by their displayed name
        if filter_by == 'city':
            cur.execute("SELECT n.idName, n.f_name, n.m_name, n.l_name, c.PPC as city_name, j.`White color` as job_name FROM cselec.name n LEFT JOIN cselec.city c ON n.City_idCity = c.idCity LEFT JOIN cselec.job j ON n.Job_idJob = j.idJob WHERE c.PPC LIKE %s", (f'%{query}%',))
            search_results = cur.fetchall()
        elif filter_by == 'job':
            cur.execute("SELECT n.idName, n.f_name, n.m_name, n.l_name, c.PPC as city_name, j.`White color` as job_name FROM cselec.name n LEFT JOIN cselec.city c ON n.City_idCity = c.idCity LEFT JOIN cselec.job j ON n.Job_idJob = j.idJob WHERE j.`White color` LIKE %s", (f'%{query}%',))
            search_results = cur.fetchall()
        elif filter_by == 'all':
            # Search across name fields and related city and job names
            cur.execute("SELECT n.idName, n.f_name, n.m_name, n.l_name, c.PPC as city_name, j.`White color` as job_name FROM cselec.name n LEFT JOIN cselec.city c ON n.City_idCity = c.idCity LEFT JOIN cselec.job j ON n.Job_idJob = j.idJob WHERE n.f_name LIKE %s OR n.m_name LIKE %s OR n.l_name LIKE %s OR c.PPC LIKE %s OR j.`White color` LIKE %s", (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%',))
            search_results = cur.fetchall()
        else:
            # Use LIKE for partial matching in the name table columns
            query_column = filter_by if filter_by in ['f_name', 'm_name', 'l_name'] else 'f_name'
            cur.execute(f"SELECT n.idName, n.f_name, n.m_name, n.l_name, c.PPC as city_name, j.`White color` as job_name FROM cselec.name n LEFT JOIN cselec.city c ON n.City_idCity = c.idCity LEFT JOIN cselec.job j ON n.Job_idJob = j.idJob WHERE n.{query_column} LIKE %s", (f'%{query}%',))
            search_results = cur.fetchall()  # Store the search results
    else:
        # If no search query is provided, return all records
        cur.execute("SELECT n.idName, n.f_name, n.m_name, n.l_name, c.PPC as city_name, j.`White color` as job_name FROM cselec.name n LEFT JOIN cselec.city c ON n.City_idCity = c.idCity LEFT JOIN cselec.job j ON n.Job_idJob = j.idJob")
        search_results = cur.fetchall()  # Store all records

    cur.close()  # Close the cursor

    return render_template('index.html', name=search_results)  # Render index.html with search results

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app in debug mode
