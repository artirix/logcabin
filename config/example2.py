from inputs.file import File as IFile
from filters.regex import Regex
from outputs.file import File as OFile

IFile('input.log')
Regex('(?P<timestamp>.+) - (?P<message>.+)')
OFile('output.log')

# try me:
# DATE=$(date); echo "$DATE - message" >> input.log
