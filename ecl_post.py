#!/bin/env python
from ECLAPI import ECLConnection, ECLEntry
from os import path, access, R_OK

#URL = "http://dbweb4.fnal.gov:8080/ECL/demo"
URL="http://dbweb6.fnal.gov:8080/ECL/uboone"

with open('login.dat') as f:
  credentials = [x.strip().split(':') for x in f.readlines()]

user = credentials[0][0]
password = credentials[0][1]


if __name__ == '__main__':
    '''
    '''
    import getopt, sys
#    print "here1"   
    opts, args = getopt.getopt(sys.argv[1:], 'nU:')

    print_only = False

    for opt, val in opts:
        if opt=='-n':
            print_only = True
            
        if opt == '-U':
            URL = val
            
      
#################
#   Create test entry
    e = ECLEntry(category='Purity Monitor', tags=[], formname='default', 
                text='<b> Nearline lifetime plots! </b> <BR>', preformatted=True)

#       Optional. Set the author username. The user must be registered CRL user 
    e.setAuthor('xmlmicro')

#   Attach some file
#    e.addAttachment('attached-file', '/bin/zcat', 
#        data='Data may come here as an argument. The file will not be read in this case')

#   Attach some image
# Image data also can be passed as a parameter here using 'image' argument.
    PATH1='./QCQA_100tracks.pdf'
    PATH2='./QCandQA_100tracks.pdf'
    if path.isfile(PATH1) and access(PATH1, R_OK):
        e.addImage('QCQA',PATH1, image=None)
    else:
        print "Either file is missing or is not readable"  

    if path.isfile(PATH2) and access(PATH2, R_OK):
        e.addImage('QCandQA',PATH2, image=None)
    else:
	print "Either file is missing or is not readable"


    if not print_only:
        # Define connection        print "here4"
#        print URL
#        print "here3"
        elconn = ECLConnection(URL, user, password)
        print "here4",user,password
        #
        # The user should be a special user created with the "raw password" by administrator.
        # This user cannot login via GUI
        # The password should be kept in some file protected from other users, like postgres does with .pgpass file.
        # Postgres checks if .pgpass mode <= 0600 before uses the file.

        # Post test entry created above
        response = elconn.post(e)
#        print "here5"
        # Print what we have got back from the server
        print response
#        print "here6"
        # Close the connection
        elconn.close()
    else:
        # Just print prepared XML
        print e.xshow()
