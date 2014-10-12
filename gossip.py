#!/usr/bin/python

import os
import sys
import subprocess
import string

#print 'sys.argv[0]', sys.argv[0] #Contains name of the script as it appears in the command line
pathname = os.path.dirname(sys.argv[0]) #returns a directory path portion
#print 'path = ', pathname
dirpath = os.path.abspath(pathname) #returns the a fully qualified path
fullpath = dirpath+"/msgrank"
#print 'full path = ',fullpath 
print "filename RANK,   FROM,		TO, 		CC,		BCC, 		Namelist"
#Step 1 - for each file extract the Rank and the name of the person FROM field who sends the msg.
#Step 2 - Also extract the mail content (3rd line). 
#Step 3 - Pass this through the NPR to find PERSON name. 
#Step 4 - Parse the NER output extracting words preceeding \PERSON. These are the person names gossiped about
numfile = 0 #Count of the number of files processed
numfile_othercomp = 0 #Initialize number of files having other company address (other than enron)
othercomp_dict = {} #Has (filename:othercompany address count) as the key value pair
namefile = {}
hasname_mail = 0 #Count of the number of email msgs which have names in their body
numgossip_mails = 0 #Count of the number of email msgs which contains gossip

for filename in os.listdir(fullpath):
  f = open(fullpath+'/'+filename) #All files have 3 lines
  numfile = numfile + 1
  #1st line has rank
  line = f.readline()
  line = line.strip()

  #2nd line has from, to cc bcc field
  line = f.readline()
  line = line.strip()
  #line = line.lower()  #change all to lower case for easy checking

  othercomp_count = 0 #Initializing the other company address count to 0
  othercomp_flag = 0 #Initializing other company address flag to 0
  
  #From namelist
  if(line.find('X-From:') == -1):
    #noXFrom_FILE.write(filename+'\n')
    continue #If there is no X-From: in the msg then skip processing this file
  #From namelist
  junk, fromname = line.split('X-From:',1)
  fromname, junk = fromname.split('X-To:',1)
  if(fromname.endswith('>')): #If fromname has trailing <> characters
    fromname, junk = fromname.split('<',1)
    fromname = fromname.strip()
    if(fromname.find(',')!=-1): #Fullname FORMAT = lname, fname
      lname, fname = fromname.split(',',1)
      lname = lname.strip()
      fname = fname.strip()
      fromname = fname + ' ' + lname
  
  #"To" namelist
  #Can have 2 formats -- 
  # FORMAT 1 -- lname1, fname1 <junk...>, lname2, fname2 <junk..>
  # FORMAT 2 --- fname1 lname1, fname1 lname1
  tonamelist = [] #Declaring an empty tonamelist array
  junk, tonames = line.split('X-To:',1)
  tonames, junk = tonames.split('X-cc:',1) #tonames has ( name <>, name <> ) or (name , name)

  if(tonames.find('>') != -1): #Handling FORMAT 1 names
    tonames = tonames.split('>')
    if(len(tonames) > 2): #More than 1 person present in the TO field
      for name in tonames:
	#Ignore the last field which is ' ' and fields containing .com (other company address)
	if(name != tonames[len(tonames)-1] and not(name.find('.com') != -1 or name.find('.net') != -1 or name.find('.edu') != -1 or name.find('"')!= -1 or name.find("@")!=-1)):
	  name, junk = name.split('<')
	  name = name.strip(',') #Removing any padded spaces and leading or trailing comma ,
          name = name.strip(' ')
	  fullname = name #when the below conditions not true, then name contains the fullname
	  if(name.find(',')!=-1): #name can be lname, fname OR fname lname (without , seperation)
	    lname, fname = name.split(',')
            fullname = fname.strip()+' '+lname.strip()
          tonamelist.append(fullname)
	#Count the number of NON ENRON employee addresses in the email msg
	if(name.find('.com') != -1 and name.find('.net') != -1 and name.find('.edu') != -1 and name.find('"')!= -1 and name.find("@")!=-1): 
  	  othercomp_flag = 1
	  othercomp_count = othercomp_count + 1
          print 'NON ENRON toNames1', name
    else:
	if(tonames[0].find('.com') == -1 and tonames[0].find('.net') == -1 and tonames[0].find('.edu') == -1): #Ignore people of other companies
    	  fullname, junk = tonames[0].split('<',1)#Only one name present as the 1st element of the name array
	  fullname = fullname.strip()
	  tonamelist.append(fullname)
	#Count the number of NON ENRON employee addresses in the email msg
	if(tonames[0].find('.com') != -1 and tonames[0].find('.net') != -1 and tonames[0].find('.edu') != -1 and tonames[0].find('"')!= -1 and tonames[0].find("@")!=-1): 
  	  othercomp_flag = 1
	  othercomp_count = othercomp_count + 1
          print 'NON ENRON toNames2', tonames[0]
  else: #Handling FORMAT 2
    if(tonames[0].find(',') == -1 and tonames[0].find('.net') == -1 and tonames[0].find('.edu') == -1): #Ignande people of other companies
      if(tonames.find(',')):
        tonames = tonames.split(',')
      for name in tonames:
        name = name.strip()
        tonamelist.append(name)
    #Count the number of NON ENRON employee addresses in the email msg
    if(tonames[0].find('.com') != -1 and tonames[0].find('.net') != -1 and tonames[0].find('.edu') != -1 and tonames[0].find('"')!= -1 and tonames[0].find("@")!=-1): 
      othercomp_flag = 1
      othercomp_count = othercomp_count + 1
      print 'NON ENRON toNames3', tonames[0]
  
  #"cc" namelist
  ccnamelist = []
  junk, ccnames = line.split('X-cc:',1)
  ccnames, junk = ccnames.split('X-bcc:',1)
  if(ccnames.find('>') != -1): #Handling FORMAT 1 names
  # FORMAT 1 -- lname1, fname1 <junk...>, lname2, fname2 <junk..>
    ccnames = ccnames.split('>')
    if(len(ccnames) > 2): #More than 1 person present in the TO field
      for name in ccnames:
	#Ignore the last field which is ' ' and fields containing .com (other company address)
	if(name != ccnames[len(ccnames)-1] and 	not(name.find('.com') != -1 or name.find('.net') != -1 or name.find('.edu') != -1 or name.find('"')!= -1 or name.find("@")!=-1)):
	  name, junk = name.split('<')
	  name = name.strip(',') #Removing any padded spaces and leading or trailing comma ,
	  fullname = name
	  if(name.find(',')!=-1): #name can be lname, fname OR fname lname (without , seperation)
	    lname, fname = name.split(',')
            fullname = fname.strip()+' '+lname.strip()
          ccnamelist.append(fullname)
	#Count the number of NON ENRON employee addresses in the email msg
	if(name.find('.com') != -1 and name.find('.net') != -1 and name.find('.edu') != -1 and name.find('"')!= -1 and name.find("@")!=-1): 
  	  othercomp_flag = 1
	  othercomp_count = othercomp_count + 1
          print 'NON ENRON ccNames1', name
    else:
	if(ccnames[0].find('.com') == -1 and ccnames[0].find('.net') == -1 and ccnames[0].find('.edu') == -1): #Ignande people of other companies
	  fullname, junk = ccnames[0].split('<',1)#Only one name present as the 1st element of the name array
	  fullname = fullname.strip()
          ccnamelist.append(fullname)
	#Count the number of NON ENRON employee addresses in the email msg
	if(ccnames[0].find('.com') != -1 and ccnames[0].find('.net') != -1 and ccnames[0].find('.edu') != -1 and ccnames[0].find('"')!= -1 and ccnames[0].find("@")!=-1): 
  	  othercomp_flag = 1
	  othercomp_count = othercomp_count + 1
          print 'NON ENRON ccNames2', ccnames[0]
  else: #Handling FORMAT 2
    if(ccnames[0].find(',') and ccnames[0].find('.net') == -1 and ccnames[0].find('.edu') == -1):
      ccnames = ccnames.split(',')
    for name in ccnames:
      name = name.strip()
      ccnamelist.append(name)
    #Count the number of NON ENRON employee addresses in the email msg
    if(ccnames[0].find('.com') != -1 and ccnames[0].find('.net') != -1 and ccnames[0].find('.edu') != -1 and ccnames[0].find('"')!= -1 and ccnames[0].find("@")!=-1): 
      othercomp_flag = 1
      othercomp_count = othercomp_count + 1
      print 'NON ENRON ccNames3', ccnames[0]
  
  #"bcc" namelist
  bccnamelist = []
  junk, bccnames = line.split('X-bcc:',1)
  bccnames, junk = bccnames.split('X-Folder:',1)
  if(bccnames.find('>') != -1): #Handling FORMAT 1 names
  # FORMAT 1 -- lname1, fname1 <junk...>, lname2, fname2 <junk..>
    bccnames = bccnames.split('>')
    if(len(bccnames) > 2): #More than 1 person present in the TO field
      for name in bccnames:
	#Ignore the last field which is ' ' and fields containing .com (other company address)
	if(name != bccnames[len(bccnames)-1] and not(name.find('.com') != -1 or name.find('.net') != -1 or name.find('.edu') != -1 or name.find('"')!= -1 or name.find("@")!=-1)):
	  name, junk = name.split('<')
	  name = name.strip(',') #Removing any padded spaces and leading or trailing comma ,
	  fullname = name
	  if(name.find(',')!=-1): #name can be lname, fname OR fname lname (without , seperation)
	    lname, fname = name.split(',')
            fullname = fname.strip()+' '+lname.strip()
          bccnamelist.append(fullname)
	#Count the number of NON ENRON employee addresses in the email msg
	if(name.find('.com') != -1 and name.find('.net') != -1 and name.find('.edu') != -1 and name.find('"')!= -1 and name.find("@")!=-1): 
  	  othercomp_flag = 1
	  othercomp_count = othercomp_count + 1
          print 'NON ENRON bccNames', name
    else:
	if(bccnames[0].find('.com') == -1 and bccnames[0].find('.net') == -1 and bccnames[0].find('.edu') == -1): #Ignore people of other companies
	  fullname, junk = bccnames[0].split('<',1)#Only one name present as the 1st element of the name array
	  fullname = fullname.strip()
          bccnamelist.append(fullname)
	#Count the number of NON ENRON employee addresses in the email msg
	if(bccnames[0].find('.com') != -1 and bccnames[0].find('.net') != -1 and bccnames[0].find('.edu') != -1 and bccnames[0].find('"')!= -1 and bccnames[0].find("@")!=-1): 
  	  othercomp_flag = 1
	  othercomp_count = othercomp_count + 1
          print 'NON ENRON bccNames', bccnames[0]
  else: #Handling FORMAT 2
    if(bccnames[0].find(',') and bccnames[0].find('.net') == -1 and bccnames[0].find('.edu') == -1):
      bccnames = bccnames.split(',')
    for name in bccnames:
      name = name.strip()
      bccnamelist.append(name)
    #Count the number of NON ENRON employee addresses in the email msg
    if(bccnames[0].find('.com') != -1 and bccnames[0].find('.net') != -1 and bccnames[0].find('.edu') != -1 and bccnames[0].find('"')!= -1 and bccnames[0].find("@")!=-1): 
      othercomp_flag = 1
      othercomp_count = othercomp_count + 1
      print 'NON ENRON bccNames', bccnames[0]
 
  #3rd line has body (content) of the msg
  line = f.readline()
  f.close() #Entire file has been read. Close it.

  #Write line to a file to pass it to ner
  f2 = open('sent.txt','w')
  f2.write(line)
  f2.close()
  subprocess.call('./ner.sh sent.txt > sent-ner.txt 2> /dev/null',shell=True)

  f2 = open('sent-ner.txt')
  line = f2.readline()
  line = line.strip()
  words = line.split() 
  #Parsing sent-ner.txt to find names of people mentioned in the email body  
  namecontd = 0 #fname lname i	s treated by NER as 2 different persons. name is continued till we reach a word which doesnot end with /PERSON
  namelist = [] #Array has the list of names of people mentioned in the email body 
  name = " "
  for word in words:
     if(word.endswith('PERSON')):
       if(namecontd == 0):
         name, junk = word.split('/PERSON',1)
	 if(name == "bloombergs"): #EXCEPTIONS
	   namecontd = 0 #Discard the name
	 else:
           namecontd = 1
       else: #The name is continued
         contdname, junk = word.split('/PERSON',1)
	 if(contdname != "boss"): #EXCEPTION
           name = name+" "+contdname
	 else:
           namelist.append(name)
	   namecontd = 0
     else: #previous word endswith /0 and is not a person name
       if(name != " "):
         namelist.append(name)
       namecontd = 0
       name = " " 

  print filename, -1 , fromname, tonamelist, ccnamelist, bccnamelist, namelist
  #print filename, rank, fromname, tonamelist, ccnamelist, bccnamelist, namelist
  #Keep a count of the number of emails which have names mentioned in the email body  
  if(namelist):
    hasname_mail = hasname_mail + 1
  #Check and print how many other company address, print only those files for which namelist is NON EMPTY
  if(othercomp_flag == 1): #and namelist):  
    numfile_othercomp = numfile_othercomp + 1
    othercomp_dict[filename] = othercomp_count
    namefile[filename] = namelist


  #Count gossips -- STEPS --
  #Loop through the namelist
  #For each item in namelist check if it is a nickname. ner finds nicknames too. Now match this with the nicknames.txt data to find corresponding goodname.
  #Check to, cc, bcc list to find a match. If not then count as gossip

  gflag = 0 #Initially no gossips(this is true for an empty namelist)
  if(namelist): #Check non empty namelist
    gflag = 1 #Mark that there is gossip whenever the list is non-empty. Scan through to,cc,bcc list and if the inmsgname is found then there is no gossip

    for inmsgname in namelist:
      #Check if the inmsgname is mentioned in the form of nickname and substitute this nickname with the corresponding goodname
      filenick = open('nicknames.txt')
      while True:
        linenick = filenick.readline()
        if not linenick: #Exit if EOF reached
     	  break
        goodname, nickname = linenick.split('\t')
        if inmsgname == nickname:
   	  print 'Inmsg == nickname %s %s %s ' %(inmsgname, goodname, nickname)
   	  inmsgname = goodname #Substitute nickname with goodname, before searching for gossip
      filenick.close() 
     
      #Check if inmsgname is present in tolist
      for toname in tonamelist:
        toname = string.lower(toname)
        if(toname.find(',') != -1):#Either Comma seperated toname (lastname, firstname) FORMAT. remove comma and get one single name
      	  l_toname, f_toname = toname.split(',',1)
      	  l_toname = l_toname.strip()
      	  f_toname = f_toname.strip()
      	  toname = f_toname + ' ' + l_toname
	else: #Or space seperated toname (firstname lastname) FORMAT
          if inmsgname == toname: #Either the inmsgname can be equal to the fullname 
  	    print 'FullTOname = inmsgname'
  	    gflag = 0
          toname_parts = toname.split(' ') #Or has (1stname lastname) or even (1stname midinitial lastname)
          for i in toname_parts: #Check if any of these parts are mentioned in the msg
  	    if i == inmsgname:
  	      print 'Part toname = inmsgname (%s %s)' %(i, inmsgname)
  	      gflag = 0
  
      #Check if inmsgname is present in cclist
      for ccname in ccnamelist:
        if(ccname != ''):
          ccname = string.lower(ccname)
          if(ccname.find(',') != -1):#Either Comma seperated ccname (lastname, firstname) FORMAT. remove comma and get one single name
    	    l_ccname, f_ccname = ccname.split(',',1)
  	    l_ccname = l_ccname.strip()
  	    f_ccname = f_ccname.strip()
  	    ccname = f_ccname + ' ' + l_ccname
	  else: #Or space seperated ccname (firstname lastname) FORMAT
            if inmsgname == ccname:
    	      print 'FullCCname = inmsgname'
    	      gflag = 0
            ccname_parts = ccname.split(' ') #Or has (1stname lastname) or even (1stname midinitial lastname)
            for i in ccname_parts: #Check if any of these parts are mentioned in the msg
  	      if i == inmsgname:
  	        print 'Part ccname = inmsgname (%s %s)' %(i, inmsgname)
  	        gflag = 0
  
      #Check if inmsgname is present in bcclist
      for bccname in bccnamelist:
        if(bccname != ''):
          bccname = string.lower(bccname)
          if(bccname.find(',') != -1):#Either Comma seperated ccname (lastname, firstname) FORMAT. remove comma and get one single name
    	    l_bccname, f_bccname = bccname.split(',',1)
  	    l_bccname = l_bccname.strip()
  	    f_bccname = f_bccname.strip()
  	    bccname = f_bccname + ' ' + l_bccname
	  else: #Or space seperated ccname (firstname lastname) FORMAT
            if inmsgname == bccname:
  	      print 'FullBCCname = inmsgname'
  	      gflag = 0
            bccname_parts = bccname.split(' ') #Or has (1stname lastname) or even (1stname midinitial lastname)
            for i in bccname_parts: #Check if any of these parts are mentioned in the msg
  	      if i == inmsgname:
  	        print 'Part bccname = inmsgname (%s %s)' %(i, inmsgname)
  	        gflag = 0
    
  if(gflag):
    numgossip_mails = numgossip_mails + 1 #Increase the count of the number of emails containing gossips

#Print the number of other company address (this is just for checking the number of emailaddresses we are ignoring)
print 'filenames 	#of NON ENRON emails ignored'
nonenron_file = open('nonENRON_namelist.txt',"w")
for key in othercomp_dict.keys():
  print '%s	  %s	%s' %(key, othercomp_dict[key],namefile[key])
  line1 = key + '	' + str(othercomp_dict[key]) + '   ' 
  line2 = namefile[key] 
  nonenron_file.write(line1)
  for items in namefile[key]:
    nonenron_file.write(items)
    nonenron_file.write(',')
  nonenron_file.write('\n')
nonenron_file.close()
print 'Total number of email messages processed=', numfile
print 'Number of files having email addresses of non ENRON employee ignored', numfile_othercomp
print 'Number of emails having PERSON names in the msg= ',hasname_mail
print 'Number of emails containing gossips=',numgossip_mails
