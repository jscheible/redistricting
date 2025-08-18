import sys, getopt
import geopandas as gpd
import tabulate

# ---------------------------------------------------------------------
#  PARSE_COMMAND_LINE()
# ---------------------------------------------------------------------
def parse_command_line():
    # Define global variables
    global shape_file
    global field_string
    global field_list

    field_list = None
    
    # Remove 1st argument from the
    # list of command line arguments
    argumentList = sys.argv[1:]

    # Options
    options = "hf:s:"

    # Long options
    long_options = ["help", "fields=", "shape-file="]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--help"):
                print ( "Displaying Help" )

            elif currentArgument in ("-f", "--fields"):
                field_string = currentValue
                print( "Field_String: ", field_string )
                field_list = field_string.split(',')

            elif currentArgument in ("-s", "--shape-file"):
                shape_file = currentValue

    except getopt.error as err:
        # output error, and return with an error code
        print (str(err))


# ---------------------------------------------------------------------
# TABULATE OUTPUT
# ---------------------------------------------------------------------
def tabulate_output():
    print( field_list )

    column_width = {}
    for name in field_list:
        print( "NAME: ", name )
        column_width[name] = len( name )

    for ii in vtd.index:
        for name in field_list:
            data_width = len( vtd.at[ii,name] )
            if column_width[name] < data_width:
                column_width[name] = data_width

    format_str = {}
    width = 1
    for name in field_list:
        format_str[name] = " %-" + str(column_width[name]) + "s "
        width += column_width[name] + 3

    print( "-"*width )
    print( end="|" )
    for name in field_list:
        print( format_str[name] %name, end="|" )
    print()
    print( "-"*width )

    for ii in vtd.index:
        print( end="|" )
        for name in field_list:
            print( format_str[name] %vtd.at[ii,name], end="|" )
        print()
    print( "-"*width )

# ---------------------------------------------------------------------
#  MAIN PROGRAM
# ---------------------------------------------------------------------

global vtd

# Parse command line
parse_command_line()

# Read Shapefile for Voting Districts
vtd = gpd.read_file( shape_file )

nObjects = len(vtd.index)
print( 'There are %d records.' %nObjects )
print( vtd.columns )

if field_list == None: exit()

tabulate_output()
