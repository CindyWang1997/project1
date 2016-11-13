#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
import datetime
from flask import Flask, request, render_template, g, redirect, Response, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2
#DATABASEURI = "sqlite:///test.db"
#DATABASEURI = "postgresql://xw2368:s4beh@<104.196.175.120>/postgres"
DATABASEURI = "mysql+pymysql://root:Yue970217@localhost/airticket"

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  #cursor = g.conn.execute("SELECT name FROM test")
  #names = []
  #for result in cursor:
    #names.append(result['name'])  # can also be accessed using result[0]
  #cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  #context = dict(data = names)
  if not session.get('logged_in'):
    return render_template('index.html')
  else:

    # userInfo stores information about user
    userInfo = {}
    
    # cmd grep user information from Passenger table
    cmd = 'SELECT gender, email, birth_year, balance FROM Passenger where name = (:aname) LIMIT 1'
    cursor = g.conn.execute(text(cmd), aname = session['username'])
    for result in cursor:
      userInfo['name'] = session['username']
      userInfo['gender'] = result['gender']
      userInfo['email'] = result['email']
      userInfo['age'] = datetime.datetime.now().year - result['birth_year']
      userInfo['balance'] = result['balance']

    context = dict(user = userInfo)
    cursor.close()
    return render_template('main.html', **context)


@app.route('/login', methods=['POST'])
def do_admin_login():
  if request.form['username']:
      session['logged_in'] = True
      session['username'] = request.form['username']

      cmd = 'SELECT PID from Passenger where name = (:aname) LIMIT 1'
      cursor = g.conn.execute(text(cmd), aname = session['username'])
      for result in cursor:
        session['PID'] = result['PID']
      
  return redirect("/")

@app.route('/logout')
def do_admin_logout():
  session.clear()

  return redirect("/")

  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  #return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#

@app.route('/searchATicket', methods=['GET'])
def do_search_ticket():

  # search database for departure and destination id
  depart = request.args.get('departure')
  dest = request.args.get('destination')
  output = 'Find Below Available Tickets <br>'
  output = output + \
          """<table style="width:100%">
                <tr>
                  <th>Agency ID</th>
                  <th>Agency Name</th> 
                  <th>Flight ID</th>
                  <th>Company</th>
                  <th>Duration</th>
                  <th>Distance</th>
                  <th>Departure Airport</th>
                  <th>Destination Airtport</th>
                  <th>Price</th>
                  <th>Quantity</th>
                </tr>
          """

  cmd = """SELECT s.aid, ag.name, f.fid, c.name, f.duration, f.distance, f.dep_IATA, f.des_IATA, s.price, s.seat_remain
        FROM Sell s join Agency ag ON s.aid = ag.aid JOIN Flight f ON s.FID = f.FID JOIN Company c ON c.cid = f.cid WHERE f.FID in
        (SELECT f2.fid from Flight f2 join Airport a on f2.dep_iata = a.iata join Airport b on f2.des_iata = b.iata
        WHERE (a.location = (:aDepart) and b.location = (:aDest)))"""
  cursor = g.conn.execute(text(cmd), aDepart = depart, aDest = dest)

  for result in cursor:
    output = output + '<tr>' + \
                        '<th>' + str(result[0]) + '</th>' + \
                        '<th>' + result[1] + '</th>' + \
                        '<th>' + result[2] + '</th>' + \
                        '<th>' + result[3] + '</th>' + \
                        '<th>' + str(result[4]) + '</th>' + \
                        '<th>' + str(result[5]) + '</th>' + \
                        '<th>' + str(result[6]) + '</th>' + \
                        '<th>' + str(result[7]) + '</th>' + \
                        '<th>' + str(result[8]) + '</th>' + \
                        '<th>' + str(result[9]) + '</th>' + \
                      '<tr>'

  output = output + '</table>'  
  cursor.close()
  return output


# This route buys a ticket
# Update Passenger balance
# Update Milege for the company
# Insert into Ticket table
# Decrease Sell remaining seats
# reload page
@app.route('/buyATicket', methods=['POST'])
def buy():
    AID=request.form['aAID']
    FID=request.form['aFID']

    # Decrease remaining seats if there still are
    cmd_seat='UPDATE Sell SET  seat_remain = seat_remain -1 where Sell.AID=(:AID) and Sell.FID=(:FID)'


    # Insert into Ticket table
    cmd_ticket = 'INSERT INTO Ticket(AID,FID,PID) VALUES ((:aAID), (:aFID), (:aPID))'
    cursor=g.conn.execute(text(cmd_ticket), aAID=AID, aFID=FID, aPID=session['PID'])
    cursor.close()

    # Update Passenger Balance
    cmd_price ='SELECT price from Sell WHERE AID = (:aAID) and FID = (:aFID) LIMIT 1'
    cursor = g.conn.execute(text(cmd_price), aAID=AID, aFID=FID)
    r_price=0     # Ticket price
    for result in cursor:
        r_price=result['price']
    cursor.close()

    cmd_balance='UPDATE Passenger p SET p.balance = p.balance - (:r_price) where p.PID=(:PID)'
    cursor = g.conn.execute(text(cmd_balance), r_price=r_price, PID=session['PID'])
    cursor.close()

    

    ##(milege++)
    #cmd_distance='SELECT Flight.distance from Flight where Flight.FID = (:FID)'
    #cursor=g.conn.execute(cmd,FID=FID)
    #distance=0
    #for result in cursor:
     #   distance=result
    #cursor.close()

    #cmd_millege='UPDATE Millage where Millage.PID=(:PID) and MIllage.CID=(:CID) SET mile = mile + (:distance)'
    #cursor =g.conn.execute(cmd_millege,PID=PID,CID=CID,distance=distance)
    #cursor.close()
    return redirect("/")



if __name__ == "__main__":
  app.secret_key = os.urandom(12)
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
