# import the inputs, filters and outputs
from inputs.file import File as IFile
from filters.regex import Regex
from outputs.file import File as OFile

# read line by line from input.log
IFile('input.log')
# extract from message format 'timestamp - message'
Regex('(?P<timestamp>.+) - (?P<message>.+)')
# and output the resulting structured event (json) to output.log
OFile('output.log')

# try me:
# DATE=$(date); echo "$DATE - message" >> input.log
