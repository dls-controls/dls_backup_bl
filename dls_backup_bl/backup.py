from Queue import Queue
from threading import Thread
from time import sleep
from subprocess import Popen, PIPE
from pkg_resources import require
#require('dls_pmacanalyse')
require('numpy')
#require('cothread==2.10') # Using test branch instead
#from dls_pmacanalyse.dls_pmacanalyse import GlobalConfig, WebPage

import sys
sys.path.append("/dls_sw/work/common/python/dls_pmacanalyse/dls_pmacanalyse/")
sys.path.append("/dls_sw/work/common/python/dls_pmaclib/")

#from dls_pmacanalyse import GlobalConfig, WebPage
from dls_pmacanalyse_work import GlobalConfig, WebPage

import sys
import smtplib
import argparse
import json
import urllib
import urllib2
import cookielib
import hashlib
import re
import os
import errno
import pexpect   # local
import datetime
import time
import dls_packages
import git

#sys.path.append('/home/fmq68384/Python/cothread_test/cothread')
require('cothread==v2.12.threaded')
import cothread
from cothread.catools import *


class Worker(Thread):
    # Thread executing jobs from a given queue
    def __init__(self, tasks):
        Thread.__init__(self)
        self.Jobs = tasks
        self.daemon = True
        self.start()
    
    def run(self):
        while True:
            func, Arguments, kargs = self.Jobs.get()
            try: 
                func(*Arguments, **kargs)
            except Exception, e: 
                print e
            self.Jobs.task_done()


class ThreadPool:
    # Pool of threads working through queued jobs
    def __init__(self, NumberThreads):
        self.Jobs = Queue(NumberThreads)
        for _ in range(NumberThreads): 
            Worker(self.Jobs)

    # Add a job to the queue
    def AddJob(self, func, *Arguments, **kargs):
        self.Jobs.put((func, Arguments, kargs))

    # Wait for all queued jobs to finish
    def WaitForCompletion(self):
        self.Jobs.join()


class EmailMessage:
    def __init__(self):
        self.Message = ""

    def AddToMessage(self, Line):
        self.Message += "\n" + Line

    def PrintMessage(self):
        return self.Message


class tsConfig:
    def __init__(self, ts, BackupDirectory, username = None, password = None, tstype = None):
        self.ts = ts
        self.path = os.path.join(BackupDirectory, "TerminalServers", self.ts)
        mkdir_p(self.path)
        self.success = False
        if tstype in [None, "moxa"]:
            self.success = self.getMoxaConfig(username or "admin", password or "tslinux", "Config.txt")
        if self.success == False and tstype in [None, "acs"]:
            self.success = self.getAcsConfig(username or "root", password or "tslinux", "/mnt/flash/config.tgz")
        if self.success == False and tstype in [None, "acsold"]: 
            self.success = self.getAcsConfig(username or "root", password or "tslinux", "/proc/flash/script")
   
    def getMoxaConfig(self, username, password, remote_path):
        # get the base page to pickup the "FakeChallenge" variable
        url = "https://" + self.ts
        base = urllib2.urlopen(url).read()
        match = re.search("<INPUT type=hidden name=FakeChallenge value=([^>]*)>", base)
        if match is None:
            print "This returns a webpage that doesn't look like a moxa login screen"
            return False
        FakeChallenge = match.groups()[0]

        # do what the function SetPass() does on the login screen
        md = hashlib.md5(FakeChallenge).hexdigest()         
        p = ""
        for c in password:
            p += "%x"%ord(c)
        md5_pass = ""
        for i in range(len(p)):
            m = int(p[i], 16)
            n = int(md[i], 16)
            md5_pass += "%x"%(m^n)

        # store login cookie
        cj = cookielib.CookieJar()          
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        login_data = urllib.urlencode(dict(Username=username, MD5Password=md5_pass))
        resp = opener.open(url, login_data)
        if "Login Failed" in resp.read():
            print "Wrong password for this moxa"
            return False
        txt = os.path.join(self.path, remote_path)
        print "Saving config to", txt
        open(txt, "w").write(opener.open(url+"/"+remote_path).read())
        return True
                 
    def getAcsConfig(self, username, password, remote_path):
        tar = os.path.join(self.path, "config.tar.gz")
        child = pexpect.spawn('scp %s@%s:%s %s'%(username, self.ts, remote_path, tar))
        i = child.expect(['Are you sure you want to continue connecting (yes/no)?', 'Password:'], timeout=120)
        if i == 0:
            child.sendline("yes")
            child.expect('Password:', timeout=120)
        child.sendline(password)        
        i = child.expect([pexpect.EOF, "scp: [^ ]* No such file or directory"])    
        if i == 1:
            print "Remote path %s doesn't exist on this ACS" % remote_path
            return False
        else:
            print "Untarring", tar        
            os.system("tar --no-overwrite-dir -xzf %s -C %s" % (tar, self.path))
            os.system("chmod -f -R g+rwX,o+rX %s" % self.path)
            os.system("find %s -type d -exec chmod -f g+s {} +" % self.path)
            return True

def TimeStamp():
    return datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d")

def mkdir_p(path):
    if path is not None:
        if not os.path.exists(path):
            #print "Dir doesn't exist!"
            os.makedirs(path)
        elif not os.path.isdir(path):
            raise ConfigError('Backup path exists but is not a directory: %s' %path)
        else:
            pass
            #print "directory found!"

if __name__ == '__main__':   

    def SendEmail(Sender, Recipient, Subject, EmailText):
        # Diamond SMTP Address = outbox.rl.ac.uk
        ServerURL = 'outbox.rl.ac.uk'
        EmailHeader = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (Sender, Recipient, Subject)
        EmailMessage = EmailHeader + EmailText
        MailServer = smtplib.SMTP(ServerURL)
    	#mailServer.set_debuglevel(1)
        MailServer.sendmail(Sender, Recipient, EmailMessage)
        MailServer.quit()


    def BackupMotorController(Controller, Server, Port, GeoBrick, TermServ, BackupDirectory, NumRetries, MyEmail, PropertyList):
        # Call dls-pmacanalyse backup
        # If backup fails retry specified number of times before giving up
        for AttemptNum in range(NumRetries):
            try:
                print "\rBacking up " + Controller + " on server " + Server + " on port " + Port + ". Attempt " + str(AttemptNum + 1) + " of " + str(NumRetries)
                ConfigObject = GlobalConfig()
                ConfigObject.backupDir = os.path.join(BackupDirectory, "MotionControllers")
                #ConfigObject.resultsDir = "/localhome/i04detector"
                ConfigObject.writeAnalysis = False
                PmacObject = ConfigObject.createOrGetPmac(Controller)
                PmacObject.setProtocol(Server, Port, TermServ)
                PmacObject.setGeobrick(GeoBrick)
                ConfigObject.analyse()
                print "\rFinished backing up " + Controller
                PropertyList.append("Successful")
            except Exception as e:
		print e
                ErrorMessage = "ERROR: Problem backing up " + Controller + " on server " + Server + " on port " + Port
                MyEmail.AddToMessage(ErrorMessage)
                print ErrorMessage
                continue
            break
        else:
            ErrorMessage = "\nAll " + str(NumRetries) + " attempts to backup " + Controller + " failed"
            MyEmail.AddToMessage(ErrorMessage)
            print ErrorMessage
            PropertyList.append("Failed")
  
 
    def BackupZebra(Name, BackupDirectory, PropertyList):
        # Amend the backup file path
        Path = os.path.join(BackupDirectory, "Zebras/")
        mkdir_p(Path)
        Path += str(Name) + "_" + TimeStamp()

        for AttemptNum in range(NumRetries):
            try:
                print "Backing up Zebra " + Name + ". Attempt " + str(AttemptNum + 1) + " of " + str(NumRetries)
                caput('%s:%s' % (str(Name), 'CONFIG_FILE'), Path, datatype = 999, throw = False)
                if not res:
                    print "Can't set Zebra backup file path"
                    raise
                else:
                    # File path PV successfully set
                    caput('%s:%s' % (str(Name), 'CONFIG_WRITE.PROC'), 1, throw = False)
                    if not res:
                        # Store button PV failed to trigger
                        raise
                    else:
                        # Store button PV triggered successfully
                        pv = caget('%s:%s' % (str(Name), 'CONFIG_STATUS'), datatype = 999)
                        while pv == "Writing '" + Path + "'":
                            # Waiting for write to complete
                            sleep(1)
                            pv = caget('%s:%s' % (str(Name), 'CONFIG_STATUS'), datatype = 999)
                        if pv == "Too soon, initial poll not completed, wait a minute":
                            print pv
                            print "Waiting 3 seconds..."                        
                            Sleep(3)
                            raise
                        elif pv == "Can't open '" + Path + "'":
                            print pv
                            raise
                        elif pv == "Done":
                            print "Finished backing up Zebra " + Name
                            PropertyList.append("Successful")

            except:
                ErrorMessage = "ERROR: Problem backing up " + Name
                MyEmail.AddToMessage(ErrorMessage)
                print ErrorMessage
                continue
            break
        else:
            ErrorMessage = "\nAll " + str(NumRetries) + " attempts to backup " + Name + " failed"
            MyEmail.AddToMessage(ErrorMessage)
            print ErrorMessage
            PropertyList.append("Failed")

    
    def BackupTerminalServer(Server, Type, BackupDirectory, NumRetries, MyEmail, PropertyList):
        # If backup fails retry specified number of times before giving up
        for AttemptNum in range(NumRetries):
            try:
                print "Backing up terminal server " + Server + " of type " + Type + ". Attempt " + str(AttemptNum + 1) + " of " + str(NumRetries)
                tsConfig(Server, BackupDirectory, None, None, Type)
                print "\rFinished backing up " + Server
                PropertyList.append("Successful")
            except:
                ErrorMessage = "ERROR: Problem backing up " + Server
                MyEmail.AddToMessage(ErrorMessage)
                print ErrorMessage
                continue
            break
        else:
            ErrorMessage = "All " + str(NumRetries) + " attempts to backup " + Server + " failed"
            MyEmail.AddToMessage(ErrorMessage)
            print ErrorMessage
            PropertyList.append("Failed")

    # dls-python backup.py -j BL04I_Backup.json -n BL04I -b "/dls_sw/work/motion/Backups/BL04I" -e "James.OHea@diamond.ac.uk" -r 1

    # Setup an argument Parser
    Parser = argparse.ArgumentParser(
        description = 'Backup PMAC & GeoBrick motor controllers, terminal servers, and Zebra boxes',
        usage = "%(prog)s -j <JSON File> [options]")
    Parser.add_argument('-j', action = "store", dest = "JSONFileName", help = "JSON file of devices to be backed up")
    Parser.add_argument('-b', '--backupdir', action = "store", dest = "BackupDirectory", help = "Directory to save backups to")
    Parser.add_argument('-r', '--numretries', action = "store", type = int, default = "3", dest= "NumRetries", help = "Number of times to attempt backup (Default of 3)")
    Parser.add_argument('-t', '--numthreads', action = "store", type = int, default = "4", dest = "NumThreads", help = "Number of processor threads to use (Number of simutaneous backups) (Default of 4)")
    Parser.add_argument('-n', '--beamline', action = "store", dest = "BeamlineName", help = "Name of beamline backup is for")
    Parser.add_argument('-e', '--emailaddr', action = "store", dest = "EmailAddress", help = "Email address to send backup reports to")

    # Parse the command line arguments
    Arguments = Parser.parse_args()

    # The script cannot run without a specified JSON file to work with
    if not (Arguments.JSONFileName):
        print "\nNo JSON file specified\n"
        sys.exit()
    elif not (Arguments.BeamlineName):
        print "\nNo beamline name specified\n"
        sys.exit()
    elif not (Arguments.BackupDirectory):
        print "\nNo backup directory specified\n"
        sys.exit()
    else:
        # Store the arguments as variables
        JSONFileName = Arguments.JSONFileName
        BackupDirectory = Arguments.BackupDirectory
        NumRetries = Arguments.NumRetries
        NumThreads = Arguments.NumThreads
        BeamlineName = Arguments.BeamlineName
        if (Arguments.EmailAddress):
            EmailAddress = Arguments.EmailAddress

    # Add the .json file extension if not specified
    if not JSONFileName.lower().endswith('.json'):
        JSONFileName += '.json'

    # Initiate a thread pool with the desired number of threads
    BackupThreadPool = ThreadPool(NumThreads)

    MyEmail = EmailMessage()

    # Open JSON file of device details
    try:
        with open(JSONFileName) as JSONFile:
            # Read out the JSON data, then close the file
            JSONData = json.load(JSONFile)
        JSONFile.close()
    # Capture problems opening or reading the file
    except Exception as e: 
        print "\nInvalid json file name or path or invalid JSON\n"
        sys.exit()
    
    MotorControllerList = []
    TerminalServerList = []
    ZebraList = []

    # Retrieve the devices from the JSON data
    try:
        MotorControllerList = JSONData["MotorControllers"]
    except:
        pass
    try:
        TerminalServerList = JSONData["TerminalServers"]
    except:
        pass
    try:
        ZebraList = JSONData["Zebras"]
    except:
        pass
    
    # State the quantity of each device found
    """    if MotorControllerList["GeoBricks"]:
        NumGeoBricks = len(MotorControllerList["GeoBricks"])
    else:
        NumGeoBricks = 0
    if MotorControllerList["PMACs"]:
        NumPMACs = len(MotorControllerList["PMACs"])
    else:
        NumPMACs = 0
    NumTerminalServers = len(TerminalServerList)
    NumZebras = len(ZebraList)
    print
    print "Devices found in " + JSONFileName + ":"
    print "    ", NumGeoBricks, "GeoBricks"
    print "    ", NumPMACs, "PMACs"
    print "    ", NumTerminalServers, "Terminal Servers"
    print "    ", NumZebras, "Zebras"
    print"""

    # Create a stylesheet for a results webpage to use
    StyleSheet = open('%s/BackupResults.css' % BackupDirectory, 'w+')
    StyleSheet.write('''
            p{text-align:left; color:black; font-family:arial}
            h1{text-align:left; color:black}
            table{border-collapse:collapse}
            table, th, td{border:1px solid black}
            th, td{padding:5px; vertical-align:top}
            th{background-color:#EAf2D3; color:black}
            em{color:black; font-style:normal; font-weight:bold}
            #code{white-space:pre}
            #code{font-family:courier}
            ''')
    StyleSheet.close()

    # Create a webpage to list results of backups
    ResultsPage = WebPage('Backup Results for %s (%s)' % (BeamlineName, 
    datetime.datetime.fromtimestamp(time.time()).strftime("%d/%m/%Y")), 
    '%s/%s_Backup_Results.htm' % (BackupDirectory, BeamlineName), 
    styleSheet = BackupDirectory +'/BackupResults.css')

    # Go through every motor controller listed in JSON file
    MotorControllerPropertyList = []
    for ControllerType in MotorControllerList:
        for MotorController in MotorControllerList[ControllerType]:
            PropertyList = []
            # Pull out the controller details
            Controller = MotorController["Controller"]
            Server = MotorController["Server"]
            Port = MotorController["Port"]

            # Check whether the controller is a GeoBrick or PMAC
            if ControllerType == "GeoBricks":
                GeoBrick = True
            else:
                GeoBrick = False

            # Check whether a terminal server is used or not
            if Port == "1025":
                TermServ = False
            else:
                TermServ = True

            # Keep a record of properties for the results table
            PropertyList.append(str(Controller))
            PropertyList.append(str(ControllerType))
            PropertyList.append(str(Server))
            PropertyList.append(str(Port))

            # Add a backup job to the pool
            BackupThreadPool.AddJob(BackupMotorController, Controller, Server, Port, GeoBrick, TermServ, BackupDirectory, NumRetries, MyEmail, PropertyList)
            # Add properties to master list
            MotorControllerPropertyList.append(PropertyList)

    # Go through every terminal server listed in JSON file
    TerminalServerPropertyList = []
    for TerminalServer in TerminalServerList:
        PropertyList = []
        # Pull out the server details
        Server = TerminalServer["Server"]
        Type = TerminalServer["Type"]
        # Keep a record of properties for the results table
        PropertyList.append(str(Server))
        PropertyList.append(str(Type))
        # Add a backup job to the pool
        BackupThreadPool.AddJob(BackupTerminalServer, Server, Type, BackupDirectory, NumRetries, MyEmail, PropertyList)
        # Add properties to master list
        TerminalServerPropertyList.append(PropertyList)

    # Go through every zebra listed in JSON file
    ZebraPropertyList = []
    for Zebra in ZebraList:
        PropertyList = []
        # Pull out the PV name detail
        Name = Zebra["Name"]
        # Keep a record of properties for the results table
        PropertyList.append(str(Name))
        # Add a backup job to the pool
        BackupThreadPool.AddJob(BackupZebra, Name, BackupDirectory, PropertyList)
        # Add properties to master list
        ZebraPropertyList.append(PropertyList) 

    # Wait for completion of all backup threads
    BackupThreadPool.WaitForCompletion()
    print "\nBackup run complete!\n"
    
    # Order the results alphabetically to make them easier to read
    MotorControllerPropertyList.sort()
    TerminalServerPropertyList.sort()
    ZebraPropertyList.sort()

    # Create table of results for motor controllers
    MotorControllerTable = ResultsPage.table(ResultsPage.body())
    Row = ResultsPage.tableRow(MotorControllerTable)
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Motion Controllers"))
    # Add column headings
    Row = ResultsPage.tableRow(MotorControllerTable)
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Controller"))
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Type"))
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Server"))
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Port"))
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Backup"))
    # Populate the cells with results
    for Controller in MotorControllerPropertyList:
        Row = ResultsPage.tableRow(MotorControllerTable)
        for Property in Controller:
            # Highlight failures
            if Property == "Failed":
                Property = ResultsPage.emphasize(ResultsPage.body(), 'Failed')
            ResultsPage.tableColumn(Row, Property)
    
    # Separate the tables    
    LineBreak = ResultsPage.lineBreak(ResultsPage.body())

    # Create table of results for terminal servers
    TerminalServerTable = ResultsPage.table(ResultsPage.body())
    Row = ResultsPage.tableRow(TerminalServerTable)
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Terminal Servers"))
    # Add column headings
    Row = ResultsPage.tableRow(TerminalServerTable)
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Name"))
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), 'Type'))
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), 'Backup'))
    # Populate the cells with results
    for TerminalServer in TerminalServerPropertyList:
        Row = ResultsPage.tableRow(TerminalServerTable)
        for Property in TerminalServer:
            # Highlight failures
            if Property == "Failed":
                Property = ResultsPage.emphasize(ResultsPage.body(), 'Failed')
            ResultsPage.tableColumn(Row, Property)

    # Separate the tables    
    LineBreak = ResultsPage.lineBreak(ResultsPage.body())

    # Create table of results for zebras
    ZebraTable = ResultsPage.table(ResultsPage.body())
    Row = ResultsPage.tableRow(ZebraTable)
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Zebras"))
    # Add column headings
    Row = ResultsPage.tableRow(ZebraTable)
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Name"))
    ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), 'Backup'))
    # Populate the cells with results
    for Zebra in ZebraPropertyList:
        Row = ResultsPage.tableRow(ZebraTable)
        for Property in Zebra:
            # Highlight failures
            if Property == "Failed":
                Property = ResultsPage.emphasize(ResultsPage.body(), 'Failed')
            ResultsPage.tableColumn(Row, Property)

    # Write the finished results page out
    ResultsPage.write()

    print MyEmail.PrintMessage()

    # Send email if needed
    if MyEmail.PrintMessage() != "" and Arguments.EmailAddress != None:
        SendEmail(EmailAddress, EmailAddress, "Backup Problems", MyEmail.PrintMessage())

    # Link to beamline backup git repository in the motion area
    GitRepo = git.Repo("/dls_sw/work/motion/Backups/" + BeamlineName)

    # Gather up any changes
    UntrackedFiles = GitRepo.untracked_files
    ModifiedFiles = [diff.a_blob.name for diff in GitRepo.index.diff(None)]
    ChangeList = UntrackedFiles + ModifiedFiles 

    # If there are changes, commit them
    if ChangeList:
	    if UntrackedFiles:
	        print "The following files are untracked:"
            for File in UntrackedFiles:
		        print File
	    if ModifiedFiles:
	        print "The following files are modified or deleted:"
	        for File in ModifiedFiles:
		        print File
	    print "Adding them to the staging area"
	    # repo.index.add(ChangeList)
	    # Note repo.git.add is used to handle deleted files
	    GitRepo.git.add(all=True)
	    GitRepo.index.commit("Modified files commited")
	    print "Committed changes"
    else:
	    print "Repository up to date. No actions taken"
	
    print "Done"



