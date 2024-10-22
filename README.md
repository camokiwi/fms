# fms
This is fms repo for the COMP636 assessment. 

# Farm Management Simulator Application Design Report

#### Design Decisions

### 1. Application Structure

FMS is built using the Flask web framework. 
The main application logic code is in the app.py file, with a list of different html files stored in templates folder for various site pages. 

# Key components:
app.py: Contains all route definitions and core logic.
connect.py: Manages database connection.

base.html: this is the main template that other site pages extend from.
 * It defines a content block for all other templates to fill.
 * It has a container for flash messages.
 * It displays the FMS logo, current date, and navigation bar (including home, paddocks, mobs, stock by mob). 
 * Basic HTML structure. 

home.html: this is an extending base.html home page of the application, it displays a welcome message and a photo about farms.

mobs.html: this displays mobs' information, and allows end users to move mobs between paddocks directly on the mobs.html page.
* Extends base.html.
* List all mobs with mobs' details info like ID, Name, and Paddock assignment. 
* Enable end users to move a mob to another paddock by filling out a form.
* Error handling enabled for mob movement. 

paddock.html: this shows detailed information about a newly created paddock. 
* Extends base.html.
* It shows paddock details such as ID, Name, area, DM/ha and total DM.
* It shows a button to let end users to navigate back to the paddock list page (paddocks.html).

paddocks.html: this shows the whole paddock records and provide management options on the top on the page.
* Extends base.html.
* Displays a nice looking datatable about all paddocks with their details. 
* Two buttons to add a new paddock and move to the next day. 
* Edit action available next to each paddock.

paddock_add.html: this provides a form to let end users fill out to add a new paddock
* Extends base.html.
* End users can enter whatever they want except for ID and total DM.
* A submit button to add the new paddock. 
* A return button to bring users back to paddock list page. 

paddock_edit.html: this allows users to edit an existing paddock's details
* Extends base.html.
* A pre-filled form to let end uers to edit. This is a hard/time-consuming one but beautiful feature, as it provides super good UX/UI experience. End users can easily spot on current paddock's data and adjust them accordingly. 
* Two buttons to update the paddock and cancel the edit. 

stock_by_mob.html: This displays stock information grouped by mobs.
* Extends base.html.
* List each mob with its related paddock.
* Displays the stock count and average weight for each mob.
* A beautiful datatable containing each animal details within each mob. 

fms-local.sql: This is database file where connects to app.py
fms-pa.sql: This is database file where connects to app.py

### 2. Routing and viewing 
The application uses Flask's routing decorator to map URLs to functions. Each major feature (paddocks, mobs, stock) has its own route and corresponding view function.

1. Home Route
This document outlines all the routes defined in the app.py file, explaining their purposes and interactions within the Farm Management Simulator application.
Specific functionality:
* Checks if 'curr_date' exists in the session using 'curr_date' not in session
* If not, initializes it with start_date (a global variable set to October 29, 2024)
* Uses render_template("home.html") to display the home page
* No database interactions
* Template interaction: Renders home.html, which extends base.html and displays a welcome message and farm image

2. Clear Date Route: out of box route, no database interactions.
3. Reset Date Route: out of box route, no database interactions.

4. Mobs Route - @app.route("/mobs", methods=["GET", "POST"])
GET functionality:
* Use SQL to get all the mobs and their current paddock assignments.
* Run another SQL query to get available (empty) paddocks.
POST functionality:
* Extract mob_id and new_paddock_id from the form.
* Checks if the target paddock is already packed by other mobs.
* If not occupied, updates the mob's paddock_id in the database.
Database interactions:
* SELECT queries for mobs and available paddocks.
* UPDATE query to move the selected mob to the selected new paddock.
Uses flash() to let end users know the success or failure of the move operation.
Template interaction: Renders mobs.html with mob data and available paddocks.

5. Move Date Forward Route - @app.route("/move-date-forward")
Specific functionality:
* Retrieves current date from session, handling both string and datetime types
* Increments the date by one day using timedelta(days=1)
* Updates the session with the new date
No direct database interactions
Redirects to the paddocks route to reflect the updated date

6. Paddocks Route - @app.route("/paddocks")
Specific functionality:
* Calculate days value since the start date.
* Run a SQL query joining paddocks, mobs, and stock tables, which is fairly complex as it is putting different objects' data together.
* Calculate current dry matter for every single paddock based on the provided growth rate, consumption rate, and days value passed.
* Making row colour dynamic based on current DM/ha (red if < 1500, yellow if < 1800).
Database interaction: Form up a complex SELECT query joining multiple tables.
Template interaction: Renders paddocks.html with detailed paddock information.

7. Stock by Mob Route - @app.route("/stock_by_mob")
Specific functionality:
* Run SQL query joining stock, mobs, and paddocks datatables.
* Group stock data together by mobs, calculating animals weight and count for every single mob.
* Calculate average weight for each mob. 
* Calculate stock animals' age based on their date of birth and current date value.
Database interaction: Form up a complex SELECT query joining multiple datatables.
Template interaction: Renders stock_by_mob.html with grouped and calculated stock data.

8. Add Paddock Route - @app.route("/paddock/add")
Specific functionality: 
* This one is more like a page that reders paddock_add site page to let users enter new paddock info.
No database interactions here on this page. 
Template interaction: Renders paddock_add.html for new paddock details.

9. Paddock Insert Route - @app.route("/paddock/insert", methods=['POST'])
Specific functionality:
* Extract paddock details such as name, area, dm_per_ha from the form that end users just filled out.
* Calculate total_dm as formula specified = area * dm_per_ha.
* Insert the new paddock record into the database.
* Extract the new paddock's ID using cursor.lastrowid.
Database interactions:
* INSERT query to create a new paddock record.
* SELECT query to ensure the entered data is integrated. 
Use flash() to let users know the success or failure of the new record creating operation.
Bring users to the newly created paddock record detail page.

10. New Paddock Single Record Page Route - @app.route("/paddock")
Specific functionality:
* Extract recordId from URL. 
* Executes SQL query to get paddock details, including associated mob and stock count.
* Calculate current total DM based on provided values like growth, consumption, and days passed.
* Calculate days passed since the start date.
* By building out this page, I gained a new skill - extracting recordId in Python dev environment. 
* In my own Salesforce projects, there're many similar use cases that requires retrieving recordId from the URL in order to do something.
* This skill is essential, as providing users with the opportunity to review and edit their entries at the end of a form is a key feature favored by most business applications.
Database interaction: SELECT query joining paddocks and mobs datatable.
Template interaction: Renders paddock.html with detailed paddock information.

11. Edit a Paddock Route - @app.route("/paddock/edit")
Specific functionality:
* Retrieve paddock ID from URL of the running page.
* Run SQL query to get current paddock details.
* This is another good skill I gained from building out this page, which is prefilling the form. 
* Prefilling a form is an important feature that most business would want.
* Prefilling a form could not only help end users save time from filling out the form, but also minimise the mistake made by end users while filling out the form.
Database interaction: SELECT query to retrieve paddock data.
Template interaction: Renders paddock_edit.html with pre-filled form for paddock editing

12. Update Paddock Route - @app.route("/paddock/update", methods=['POST'])
Specific functionality:
* Retrieve newly entered paddock data from the form that end users just filled out.
* Recalculate total_dm based on new area and dm_per_ha.
* Update the paddock data in the database.
* It's good to learn this new industry knowledge in Python environment, the method of updating an existing record is called 'Post', which is same as OmniStudio DataRaptor dev environment but different from out-of-box Salesforce standard one (it's called Upsert). 
Database interaction: UPDATE query to update an existing paddock record.
Uses flash() to let users know the success or failure of the updating process.
Redirect users to the paddocks list page after successful update.

### 3. Database Interaction

The entire application uses MySQL for data interaction. MySQL is a pretty mighty query language.
getCursor() function is used to manage database connections.
Database Query Types and Usage
1. Paddocks Route
* Use LEFT JOIN to include paddocks without mobs.
* Include subquery for stock counting.
* Sorting orders alphabetically.
2. Mob Query with Paddock Information
* Join mobs with paddocks
* Alias columns for clarity
* Use LEFT JOIN to include mobs without paddocks
3. INSERT Operations
* Include automatic total_dm calculation
* Implement proper error handling which is a pretty good practise.
4. UPDATE Operations
* Update all the fields atomically.
* Include WHERE clause for a specific record.
5. Database Connection Configuration
* Allow for different environments (development/production), which is pretty good practise.

### 4. Data Calculation

1. Time-Based Calculation
* The system has a start date: October 29 2024.
* It keeps track of the current date in the session.
* It calculate how many days have passed since the start date.
2. Stock Consumption Calculation
* For example, there are 20 animals in a paddock, each animal eats 14 kg per day, 7 days have passed
* Total consumption = 20 animals × 14 kg × 7 days = 1,960 kg of grass eaten
3. Warning (red and yellow) Level Calculation
* Red warning: Less than 1,500 kg of grass.
* Yellow warning: Between 1,500 and 1,800 kg.
* No warning: More than 1,800 kg.
4. Average Weight per Mob
* mob['average_weight'] = mob['total_weight'] / mob['animal_count']
5. Stock animal Age Calculation
* Animal's age = (current_date - birth_date).days // 365

### 5. User Interface 
1. base.html
* Every page uses this same layout.
* The navigation menu stays the same throughout as well as the current date value.
2. Making Pages Look Good (Bootstrap Styling)
Bootstrap is like a collection of pre-made designs.
* Tables are easy to read
* Buttons are clearly visible
* Everything looks professional
* Works on both computers and mobile phones
3. Making the Site Responsive 
* On a computer: Shows two columns side by side
* On a phone: Stacks them on top of each other
* Text and tables adjust to fit the screen

### 6. Error Handling and User Feedback

1. Showing messages to Users (Using flash)
* Appear when something happens.
* Tell users if things worked or failed.
* This is a handy feature that many online businesses are keen to have. 
2. Handling things that goes wrong (Try-Except)
If everything works:
* User sees success message.
* Go back to paddock list.
If something goes wrong:
* Database stays unchanged.
* User sees error message.
* Can try again.

### 7. Design Rationale and Alternatives Considered

# Route Design Choices
GET vs POST Methods
* Get is performing extracting function, which is for showing like viewing paddocks list.
* I chose GET because it's better for bookmarking and sharing URLs.
* Also it can help with browser back button working properly, which is a pretty handy feature.

Used POST for changing data (like moving mobs or updating paddocks)
* I chose POST simply because it's best practise and generally safer for changing data.
* Another cool thing about POST is it can prevent accidental changes from refreshing the page.

# Template Design Decisions
Separate Templates vs IF Statements:
* In terms of viewing and editing paddocks pages, I chose separate templates.
* IF statement in theory would work too but I didn't choose it. 
* Reasons are following: 
* Cleaner code - making the code looking nice and clean is important, which is like managing household. cleaner space would always make people feel comfortable.
* Easier to maintain - this is an essential thing in development environment. We cannot only look at and care about what we can do and what the requirements are for now, as changing is alway hapenning, we need to leave enough room for the potential future growth. 
* Less chance of mistakes - simply because it's more organised.

# Base Template Structure:
I have put navigation and layout in base.html, which is a good practise. So that I don't need to repreat coding in every other template. More importanly, if there's changing requirement on the UI in the future, we don't need to make changes on every single template, instead just making changes on the base.html.

# Future Improvements Considered
Regarding tabletables, it is normally nice to give the filter function to the table so that the user can easily put a filter on it and they can easily spot on what they intend to. On the other hand, with a large volumn of data, it is essential to have filter available on the datatables. 


#### Image Sources

Image source is from an online website, which is directly referenced in the code. 
Source: src="https://images.pexels.com/photos/974314/pexels-photo-974314.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1


#### Database Questions

1. 
CREATE TABLE mobs (
	id int NOT NULL AUTO_INCREMENT,
	name varchar(50) DEFAULT NULL,
	paddock_id int not null,
	PRIMARY KEY (id),
    UNIQUE INDEX paddock_idx (paddock_id),	
	CONSTRAINT fk_paddock
		FOREIGN KEY (paddock_id)
		REFERENCES paddocks(id)
		ON DELETE NO ACTION
		ON UPDATE NO ACTION
);

2. 
UNIQUE INDEX paddock_idx (paddock_id),
CONSTRAINT fk_paddock
    FOREIGN KEY (paddock_id)
    REFERENCES paddocks(id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION

3. 
CREATE TABLE farms (
    id int NOT NULL AUTO_INCREMENT,
    name varchar(200) NOT NULL,
    description varchar(500),
    owner_name varchar(200) NOT NULL,
    PRIMARY KEY (id)
);

4. 
INSERT INTO farms (name, description, owner_name)
VALUES ("Happy every day farm", "100% pure New Zealand honey farm.", "Chen Ding");

5. 
Currently there's only one farm by default, which is not a good practise, so that creating a farm object is next must-do thing. Following fields would be nice to have along with new Farm object.
* farm_id
* farm_name
* farm_contactperson
* farm_size
* farm_location.city
* farm_location.street
* farm_location.number
