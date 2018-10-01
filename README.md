A lightweight tool to parse WhatsApp .txt files and output them to .csv
format.

Will output a file containing the following fields for each message:

 - message_id: A unique, consecutive, 1-indexed numerical id.
 - date: The date on which a message was sent / generated
 - time: As above
 - message_type: One of the following:
   - 'system':  Group creation etc messages from WhatsApp, without an 
                originating number
   - 'action':  Actions taken by a user in a chat (e.g adding a 
                participant
   - 'message': A message sent from one user to the group
 - phone: Phone number of users sending messages
 - phone_country_code: 2 character country code extrapolated from 
                       country dialling code (e.g 'GB')
 - phone_country: Longname for country code (e.g 'United Kingdom')
 - text: Contents of message / system message
 - text_direction: One of l2r or r2l, as defined by WhatsApp

Note: Only tested on WhatsApp outputs produced in 2018; earlier files
may have differing formats.

Developed by Josh Smith for Demos in autumn 2018.
        
Example for use from a UNIX command line:
python3 main.py -i imput_file.txt -o output.csv -v

Argparse help:
        optional arguments:
          -h, --help            show this help message and exit
          -i path, --input-file path
                                Path to a .txt file containing a WhatsApp message history.
          -o path, --output-file path
                                Desired path to output .csv file.If this already exists, it WILL be overwritten without warning (apart from this warning)
          -v, --validate        Validate: If true, will validate each entry according to expected format (e.g will check time is in hh:mm am/pm) and print offenders. Default: false
