from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask import flash # 6) requirement
from datetime import date, datetime, timedelta
from mysql.connector import Error # 7)
from connect import dbuser, dbpass, dbhost, dbport, dbname
import mysql.connector
import connect

app = Flask(__name__)
app.secret_key = 'COMP636 S2'

start_date = datetime(2024, 10, 29).replace(tzinfo=None) # has to do otherwise it keeps giving me error
pasture_growth_rate = 65    #kg DM/ha/day
stock_consumption_rate = 14 #kg DM/animal/day

db_connection = None
 
def getCursor():
    """Gets a new dictionary cursor for the database.
    If necessary, a new database connection is created here and used for all
    subsequent to getCursor()."""
    global db_connection
 
    if db_connection is None or not db_connection.is_connected():
        db_connection = mysql.connector.connect(user=connect.dbuser, \
            password=connect.dbpass, host=connect.dbhost,
            database=connect.dbname, autocommit=True)
       
    cursor = db_connection.cursor(buffered=False)   # returns a list
    # cursor = db_connection.cursor(dictionary=True, buffered=False)
   
    return cursor

#  This route is to add new paddocks below !!!! otherwise there's always connections issue
def get_db_connection():
    return mysql.connector.connect(
        host=dbhost,
        user=dbuser,
        password=dbpass,
        database=dbname,
        port=dbport
    )

@app.route("/")
def home():
    if 'curr_date' not in session:
        session.update({'curr_date': start_date})
    return render_template("home.html")

@app.route("/clear-date")
def clear_date():
    """Clear session['curr_date']. Removes 'curr_date' from session dictionary."""
    session.pop('curr_date')
    return redirect(url_for('paddocks'))  

@app.route("/reset-date")
def reset_date():
    """Reset session['curr_date'] to the project start_date value."""
    session.update({'curr_date': start_date})
    return redirect(url_for('paddocks'))  

# just updating existing mobs route here, 
# so that user can view mobs details and perform moving mob function at the same page
# Creating a new one route for move mob is nothing but duplicating 
@app.route("/mobs", methods=["GET", "POST"])
def mobs():
    """List the mob details and handle moving mobs to other paddocks."""
    connection = getCursor()
    
    # SQL to get all mobs with their current paddock assignments
    qstr = """
        SELECT mobs.id AS mob_id, mobs.name AS mob_name, paddocks.name AS paddock_name 
        FROM mobs 
        LEFT JOIN paddocks ON mobs.paddock_id = paddocks.id
    """
    connection.execute(qstr)
    mobs = connection.fetchall()
    
    # SQL to get available paddocks
    queryAvailablePaddocks = """
        SELECT p.id, p.name 
        FROM paddocks p 
        LEFT JOIN mobs m ON p.id = m.paddock_id 
        WHERE m.paddock_id IS NULL
    """
    connection.execute(queryAvailablePaddocks)
    available_paddocks = connection.fetchall()
    
    if request.method == "POST":
        mob_id = request.form["mob_id"]
        new_paddock_id = request.form["paddock_id"]

        # THis is to check if the target paddock is packed by other mobs
        query_check_paddock = "SELECT COUNT(*) FROM mobs WHERE paddock_id = %s"
        connection.execute(query_check_paddock, (new_paddock_id,))
        paddock_occupied = connection.fetchone()[0]

        if paddock_occupied > 0:
            flash("Error: The selected paddock already has a mob assigned to it.")
        else:
            # move the mob to the selected new paddock
            move_query = "UPDATE mobs SET paddock_id = %s WHERE id = %s"
            connection.execute(move_query, (new_paddock_id, mob_id))

            # Use the connection object to commit, not the cursor, issue occured if not using this 
            db = connection._connection  # Get the actual database connection from the cursor
            db.commit()

            flash("Mob moved successfully!")
            return redirect(url_for("mobs"))

    return render_template("mobs.html", mobs=mobs, paddocks=available_paddocks)  # connect values to the html file

# paddock move date forward route
@app.route("/move-date-forward")
def move_date_forward():
    if 'curr_date' not in session:
        session['curr_date'] = start_date
    else:
        if isinstance(session['curr_date'], str):
            current_date = datetime.strptime(session['curr_date'], "%Y-%m-%d").replace(tzinfo=None)
        else:
            current_date = session['curr_date'].replace(tzinfo=None)
        session['curr_date'] = current_date + timedelta(days=1)
    
    return redirect(url_for('paddocks'))  # connect values to the html file

# paddocks list route
@app.route("/paddocks")
def paddocks():
    if 'curr_date' not in session:
        session['curr_date'] = start_date

    if isinstance(session['curr_date'], str):
        current_date = datetime.strptime(session['curr_date'], "%Y-%m-%d").replace(tzinfo=None)
    else:
        current_date = session['curr_date'].replace(tzinfo=None)
    
    daysPassed = (current_date - start_date).days # assign the new value to the variaable 

    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # SQL to get all the required data, sorting them by alphabetically by name
        query = """
        SELECT 
            p.id, p.name, p.area, p.dm_per_ha, p.total_dm, 
            COALESCE(m.name, 'No Mob') AS mob_name,
            COALESCE((SELECT COUNT(*) FROM stock s WHERE s.mob_id = m.id), 0) AS stock_count
        FROM paddocks p
        LEFT JOIN mobs m ON p.id = m.paddock_id
        ORDER BY p.name ASC
        """
        cursor.execute(query)
        paddocks = cursor.fetchall()

        # This part is like formula, to calculate growth and consumption, and then determine what row color would be 
        for paddock in paddocks:
            growth = paddock['area'] * pasture_growth_rate * daysPassed
            consumption = paddock['stock_count'] * stock_consumption_rate * daysPassed
            paddock['current_total_dm'] = paddock['total_dm'] + growth - consumption
            paddock['current_dm_per_ha'] = paddock['current_total_dm'] / paddock['area']
            
            if paddock['current_dm_per_ha'] < 1500:
                paddock['row_color'] = 'table-danger'
            elif paddock['current_dm_per_ha'] < 1800:
                paddock['row_color'] = 'table-warning'
            else:
                paddock['row_color'] = ''

        return render_template("paddocks.html", paddocks=paddocks, current_date=current_date)  # connect values to the html file
    
    except Exception as e:
        flash(f"Error retrieving paddock data: {str(e)}")
        return redirect(url_for('home'))
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# stock by mob route
@app.route("/stock_by_mob")  
def stock_by_mob():
    connection = getCursor()
    
    # The SQL query to get mob, stock, paddock, and calculate the number of stock and average weight
    qstr = """
        SELECT 
            mobs.id AS mob_id, 
            mobs.name AS mob_name, 
            paddocks.name AS paddock_name, 
            stock.id AS animal_id, 
            stock.dob AS dob, 
            stock.weight AS weight
        FROM 
            stock
        INNER JOIN 
            mobs ON stock.mob_id = mobs.id
        INNER JOIN 
            paddocks ON mobs.paddock_id = paddocks.id
        ORDER BY 
            mobs.name, stock.id;
    """
    connection.execute(qstr)
    stockDetailData = connection.fetchall()  # This thing give a list of tuples
    
    groupedStock = {}  # This is to group the stock by mob
    current_date = datetime.now().date()  # FMS current date to use calculate the age later
    
    for row in stockDetailData:
        mob_id = row[0]  # Access mob id index 0
        if mob_id not in groupedStock:  # If the mob is not in the dictionary
            groupedStock[mob_id] = {
                'mob_name': row[1], 
                'paddock_name': row[2],  # Store the paddock name
                'animals': [], 
                'total_weight': 0,  # Set a first value for total weight for average calculation
                'animal_count': 0   # Set a first value for the number of stock in the mob
            }
        
        dateOfBirth_NZFormat = row[4].strftime('%d/%m/%Y')  # Transform DOB into NZ format, leave this one here for now for later use if it's required to display 
        
        birth_date = row[4]  # Date of Birth
        animal_Age = (current_date - birth_date).days // 365 
        
        # Add new animal details to the mob
        groupedStock[mob_id]['animals'].append ({
            'animalId': row[3],      # Assign Animal ID value to the vairable
            'dateOfBirth': dateOfBirth_NZFormat,  # Transformed DOB, didn't find it required, so just leave it here.
            'animalWeight': row[5],  # Assign animal weight value to the variable
            'animalAge': animal_Age  # Assign animal age value to the variable
         })
        
        groupedStock[mob_id]['total_weight'] += row[5]    # This is to update total weight 
        groupedStock[mob_id]['animal_count'] += 1         # This is to update the animal numbers
    
    # Calculate the average weight for each mob
    for mob_id in groupedStock:
        if groupedStock[mob_id]['animal_count'] > 0:
            groupedStock[mob_id]['average_weight'] = groupedStock[mob_id]['total_weight'] / groupedStock[mob_id]['animal_count']
        else:
            groupedStock[mob_id]['average_weight'] = 0  # This is to avoid math mistake - division by zero if there are no animal
    
    return render_template("stock_by_mob.html", grouped_stock=groupedStock) # connect values to the html file

# paddock_add form route 
@app.route("/paddock/add")
def add_paddock():
    return render_template("paddock_add.html") # refer to the new page

# adding a new paddock route
@app.route("/paddock/insert", methods=['POST'])
def paddock_insert():
    connection = None # set initial value, otherwise it keeps giving me error
    cursor = None     # set initial value, otherwise it keeps giving me error
    try:
        connection = get_db_connection() # connect with database
        cursor = connection.cursor() 
        name = request.form['name']         # assign values to the variable
        area = float(request.form['area'])  # assign values to the variable, convert the type to float
        dm_per_ha = float(request.form['dm_per_ha'])   # assign values to the variable, convert the type to float
        total_dm = area * dm_per_ha         # calculate total DM as requested

        query = """    
            INSERT INTO paddocks (name, area, dm_per_ha, total_dm)
            VALUES (%s, %s, %s, %s)
        """ # SQL to insert the new record paddock
        cursor.execute(query, (name, area, dm_per_ha, total_dm))
        connection.commit()
         
        new_id = cursor.lastrowid   # get the new id of the newly created paddock
        return redirect(f"/paddock?id={new_id}")  # use that id to navigate to the new paddock's page
    except Exception as e:
        flash(f"Error adding paddock: {str(e)}")   # error hanlding 
        return redirect("/paddock/add")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# new paddock route 
@app.route("/paddock")
def paddock():
    id = request.args.get('id')       # get id from record detail page in the URL
    if 'curr_date' not in session:
        session['curr_date'] = start_date  # assign value to the variable
    
    if isinstance(session['curr_date'], str):
        current_date = datetime.strptime(session['curr_date'], "%Y-%m-%d").replace(tzinfo=None)
    else:
        current_date = session['curr_date'].replace(tzinfo=None)
    
    daysPassed2 = (current_date - start_date).days  # calculate days 

    connection = None
    cursor = None
    try:
        connection = get_db_connection()  # connect with database
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT p.*, COALESCE(m.name, 'No Mob') AS mob_name,
               COALESCE((SELECT COUNT(*) FROM stock s WHERE s.mob_id = m.id), 0) AS stock_count
        FROM paddocks p
        LEFT JOIN mobs m ON p.id = m.paddock_id
        WHERE p.id = %s
        """  # SQL get paddock details and all the mod details too
        cursor.execute(query, (id,)) # run it 
        paddock = cursor.fetchone() # extract paddock info
        
        if paddock:
            growth = paddock['area'] * pasture_growth_rate * daysPassed2 # calculate new pasture growth value
            consumption = paddock['stock_count'] * stock_consumption_rate * daysPassed2 # calculate new consumption value
            paddock['current_total_dm'] = paddock['total_dm'] + growth - consumption
            return render_template("paddock.html", paddock=paddock, current_date=current_date) # back to paddock.html page with connected variable values
        else:
            flash("Paddock not found")    # error handling 
            return redirect("/paddocks")
    except Exception as e:
        flash(f"Error retrieving paddock: {str(e)}")
        return redirect("/paddocks")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Paddock display edit route
@app.route("/paddock/edit")
def edit_paddock():
    id = request.args.get('id') # get padock id from URL of the record page
    connection = None
    cursor = None
    try:
        connection = get_db_connection()   # database connection same as before
        cursor = connection.cursor(dictionary=True) # this is a tricky one, has to create a new cursor that give me dictionaries so this way no error
        query = "SELECT * FROM paddocks WHERE id = %s" 
        cursor.execute(query, (id,))      # run the command same as before
        paddock = cursor.fetchone()
        if paddock:
            return render_template("paddock_edit.html", paddock=paddock)  # navigate to paddock_edit page 
        else:
            flash("Paddock not found")    # error handling 
            return redirect("/paddocks")
    except Exception as e:
        flash(f"Error retrieving paddock for editing: {str(e)}")
        return redirect("/paddocks")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
            
# paddock updating route
@app.route("/paddock/update", methods=['POST'])
def paddock_update():
    connection = None
    cursor = None
    try:
        connection = get_db_connection() # same as before database connection
        cursor = connection.cursor()
        id = request.form['id']   # this is to get the id from form
        name = request.form['name'] # get the name from form 
        area = float(request.form['area']) # get the area from form  then conver to float
        dm_per_ha = float(request.form['dm_per_ha']) # get the dm_per_ha from form then conver to float
        total_dm = area * dm_per_ha  # Recalculate total DM

        query = """
            UPDATE paddocks
            SET name = %s, area = %s, dm_per_ha = %s, total_dm = %s
            WHERE id = %s
        """ # Update SQL
        cursor.execute(query, (name, area, dm_per_ha, total_dm, id))
        connection.commit()
        
        flash("Paddock updated successfully") # let user know if success
        return redirect("/paddocks")
    except Exception as e:
        flash(f"Error updating paddock: {str(e)}") #  error handling 
        return redirect(f"/paddock/edit?id={id}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()




