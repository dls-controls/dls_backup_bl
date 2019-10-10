


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
                                                      datetime.datetime.fromtimestamp(
                                                          time.time()).strftime(
                                                          "%d/%m/%Y")),
                      '%s/%s_Backup_Results.htm' % (
                          BackupDirectory, BeamlineName),
                      styleSheet=BackupDirectory + '/BackupResults.css')




# Create table of results for motor controllers
MotorControllerTable = ResultsPage.table(ResultsPage.body())
Row = ResultsPage.tableRow(MotorControllerTable)
ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(),
                                                   "Motion Controllers"))
# Add column headings
Row = ResultsPage.tableRow(MotorControllerTable)
ResultsPage.tableColumn(Row,
                        ResultsPage.emphasize(ResultsPage.body(), "Controller"))
ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Type"))
ResultsPage.tableColumn(Row,
                        ResultsPage.emphasize(ResultsPage.body(), "Server"))
ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Port"))
ResultsPage.tableColumn(Row,
                        ResultsPage.emphasize(ResultsPage.body(), "Backup"))
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
ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(),
                                                   "Terminal Servers"))
# Add column headings
Row = ResultsPage.tableRow(TerminalServerTable)
ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Name"))
ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), 'Type'))
ResultsPage.tableColumn(Row,
                        ResultsPage.emphasize(ResultsPage.body(), 'Backup'))
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
ResultsPage.tableColumn(Row,
                        ResultsPage.emphasize(ResultsPage.body(), "Zebras"))
# Add column headings
Row = ResultsPage.tableRow(ZebraTable)
ResultsPage.tableColumn(Row, ResultsPage.emphasize(ResultsPage.body(), "Name"))
ResultsPage.tableColumn(Row,
                        ResultsPage.emphasize(ResultsPage.body(), 'Backup'))
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
