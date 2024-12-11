# CECS327-Assignment8-Group24

### Start the TCP Server
To start the TCP server, run `python server.py`
Enter in the desired IP address and port number

### Start the TCP Client
To start the TCP client, run `python client.py`
Enter in the same IP address and port number of the server you wish to connect to

### Connecting to Database
In order to change the database to connect to, change the uri string near the top of the server.py file. Ex:
`uri = "mongodb+srv://user:<db_password>@cluster.mvzpl.mongodb.net/?retryWrites=true&w=majority&appName=appname"`
