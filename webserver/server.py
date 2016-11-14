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
from flask import Flask, flash, request, render_template, g, redirect, Response, session

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



@app.route('/searchATicket', methods=['GET'])
def do_search_ticket():

  # search database for departure and destination id
  depart = request.args.get('departure')
  dest = request.args.get('destination')
  output = 'Find Below Available Tickets <br>'
  output = output + \
          """<table style="width:80%">
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
                        '<td>' + str(result[0]) + '</td>' + \
                        '<td>' + result[1] + '</td>' + \
                        '<td>' + result[2] + '</td>' + \
                        '<td>' + result[3] + '</td>' + \
                        '<td>' + str(result[4]) + '</td>' + \
                        '<td>' + str(result[5]) + '</td>' + \
                        '<td>' + str(result[6]) + '</td>' + \
                        '<td>' + str(result[7]) + '</td>' + \
                        '<td>' + str(result[8]) + '</td>' + \
                        '<td>' + str(result[9]) + '</td>' + \
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
    cmd_remain = 'SELECT `seat_remain` FROM Sell s WHERE s.AID=(:aAID) and s.FID=(:aFID) LIMIT 1'
    cursor = g.conn.execute(text(cmd_remain), aAID=AID, aFID=FID)
    r_remain=0
    for result in cursor:
        r_remain = result[0]
    cursor.close()

    # Check if there is still remaining seat
    if (r_remain <= 0):

        # No enough Seat, alarm the user
        flash('This Ticket Is Not Available!')

    else:
        cmd_seat='UPDATE Sell s SET seat_remain = seat_remain -1 where s.AID=(:aAID) and s.FID=(:aFID)'
        g.conn.execute(text(cmd_seat), aAID=AID, aFID=FID)

        # Cannot just delete row from Sell othewise, ticket foreign key constraint fails

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

        

        ## Add milege to table
        cmd_distance='SELECT distance from Flight where FID = (:aFID)'
        cursor=g.conn.execute(text(cmd_distance),aFID=FID)
        distance=0
        for result in cursor:
            distance=result[0]
        cursor.close()

        # Get Company ID
        cmd_cid = 'SELECT f.cid FROM Sell s JOIN Flight f ON s.fid = f.fid WHERE f.fid = (:aFID) LIMIT 1'
        cursor = g.conn.execute(text(cmd_cid), aFID=FID)
        cid = 0
        for result in cursor:
            cid = result[0]
        cursor.close()

        # If this passenger does not have milege for this comapny, add it to the Milege Table
        cmd_check='SELECT COUNT(*) from Milege M where M.PID=(:aPID) AND M.CID=(:aCID)'
        cursor =g.conn.execute(text(cmd_check),aPID=session['PID'],aCID=cid)
        check=0
        for result in cursor:
            check=result[0]
        cursor.close()
    
        if(check==0):
            cmd_insert='INSERT INTO Milege(Air_miles,PID,CID) VALUES (0,(:PID),(:CID))'
            cursor=g.conn.execute(text(cmd_insert),PID=session['PID'],CID=cid)
        cursor.close()

        cmd_milege='UPDATE Milege SET air_miles = air_miles + (:adistance) WHERE PID=(:aPID) and CID=(:aCID)'
        g.conn.execute(text(cmd_milege),aPID=session['PID'], aCID=cid, adistance=distance)

        flash("You successfully purchased the ticket!")
    return redirect("/")


@app.route('/showTicket')
def displayTicket():
  cmd_st='SELECT T.TID,T.FID,T.AID,F.dep_IATA,F.des_IATA,F.duration,F.distance FROM Ticket T JOIN Flight F ON T.FID=F.FID WHERE T.PID=(:aPID)'
  cursor = g.conn.execute(text(cmd_st), aPID=session['PID'])
  r_ticket=[]
  for result in cursor:
    r_ticket.append(result)
  cursor.close()

  context = dict(allTickets = r_ticket)
  return render_template('tickets.html', **context)



@app.route('/accountInfo')
def displayAccount():
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
    return render_template('accountInfo.html', **context)


@app.route('/addBalance', methods=['POST'])
def addABalance():
    balance=request.form['addAmount']

    cmd_add = 'UPDATE Passenger SET balance = balance + (:abalance) WHERE PID=(:aPID)'
    g.conn.execute(text(cmd_add), abalance=balance, aPID=session['PID'])
    flash("%d dollars added to your account!" %float(balance))

    return redirect('/accountInfo')
    

@app.route('/whereTo')
def recommend_place():
  return render_template('recommendation.html')


@app.route('/searchAGO', methods=['GET'])
def do_search_GO():

  # search database for location
  loca = request.args.get('currLoc')
  output = 'These trips might be great for you! <br>'
  output = output + \
          """<table style="width:80%">
                <tr>
                  <th>Agency ID</th>
                  <th>Flight ID</th>
                  <th>Price</th>
                  <th>Destination</th>
                </tr>
          """

  cmd_go = """SELECT S.AID,S.FID,S.price, B.location FROM Sell S JOIN Flight F ON S.FID=F.FID JOIN Airport A ON F.dep_IATA = A.IATA 
              JOIN Airport B on F.des_IATA = B.IATA, 
              Passenger P 
              WHERE A.location=(:aloca) AND S.price <= P.balance AND P.PID=(:aPID)"""
  cursor = g.conn.execute(text(cmd_go), aloca = loca, aPID = session['PID'])

  for result in cursor:
    output = output + '<tr>' + \
                        '<td>' + str(result[0]) + '</td>' + \
                        '<td>' + result[1] + '</td>' + \
                        '<td>' + str(result[2]) + '</td>' + \
                        '<td>' + str(result[3]) + '</td>' + \
                      '<tr>'

  output = output + '</table>'  
  cursor.close()
  return output


@app.route('/milege')
def displayMilege():
  cmd_sm='SELECT M.CID,C.name,M.air_miles FROM Milege M Join Company C on M.CID = C.CID WHERE M.PID=(:aPID)'
  cursor = g.conn.execute(text(cmd_sm), aPID=session['PID'])
  r_milege=[]
  for result in cursor:
    r_milege.append(result)
  cursor.close()

  context = dict(allMileges = r_milege)
  return render_template('milege.html', **context)





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
