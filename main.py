import re
import phonenumbers
import pycountry
import argparse
import csv


def read_to_messages(in_file):
    #expand to cover alternative date formats...
    date1_match_regex = "[0-9]{2}/[0-9]{2}/[0-9]{4}, " \
                        "[0-9]{1,2}:[0-9]{2} (?:am|pm)"
    date2_match_regex = "[0-9]{2}\/[0-9]{2}\/[0-9]{4}, " \
                        "[0-9]{1,2}:[0-9]{2}"
    date_formats_regex = [date1_match_regex, date2_match_regex]
    date_formats_comparing_regex = []

    # generate splitting regex for date formats
    for count in range (0, len(date_formats_regex)):
        date_formats_comparing_regex.append("\s(?=" \
            + date_formats_regex[count] + " - .)")
    # Reads the whole file into memory - suitable for our use case but beware
    # for very large files
    with open(in_file, encoding="utf8") as f:
        contents = f.read()
        # identifies what data/time format is used; e.g. below:
        for count in range (0, len(date_formats_comparing_regex)):
            if re.search(date_formats_regex[count], contents):
                print(date_formats_comparing_regex[count])
                return re.split(date_formats_comparing_regex[count], contents)

def convert_messages_to_dicts(messages):
    # Regex for WhatsApp phone numbers. Note; \xa0 is a non-breaking space
    phone_regex = '(\+[0-9 \xa0()-]{5,50})(?:\u202c)?(:)?'
    out_dicts = []
    message_id = 1

    for count, message in enumerate(messages):
        # Create a new dictionary with a 1-indexed unique ID
        m_dict = {'message_id': str(count + 1)}

        date_split = message.split(',')
        m_dict['date'] = date_split[0].strip()

        time_split = ','.join(date_split[1:]).split(' - ')
        m_dict['time'] = time_split[0].strip()

        remainder = ' - '.join(time_split[1:])
        # Whatsapp strings seem to start with an embedding explaining text
        # direction. Record then remove this
        try:
            embedding = remainder[0]
        except IndexError as e:
            print("No text found in {}".format(message))
            raise e
        if embedding == '\u202a':
            m_dict['text_direction'] = 'l2r'
            remainder = remainder[1:]
        elif embedding == '\u202b':
            m_dict['text_direction'] = 'r2l'
            remainder = remainder[1:]

        # If the rest of the message doesn't start with a +, it's a
        # system message
        if remainder[0] == '+':
            phone_match = re.match(phone_regex, remainder)
            if phone_match:
                number = phone_match.group(1)
                colon = phone_match.group(2)
                # If there's a colon at the end of the phone number, it's a message
                if colon:
                    m_dict['message_type'] = 'message'
                # If there's not, it's something a number has done (an 'action')
                else:
                    m_dict['message_type'] = 'action'
                m_dict['phone'] = number
                # Set the text to what's left after the number
                m_dict['text'] = remainder[len(phone_match.group(0)) + 1:].strip()
            else:
                print("Not a number! {}".format(remainder))
        elif re.search(':', remainder) is not None:
                NewRemainder = re.split(':', remainder)
                m_dict['message_type'] = 'message'
                m_dict['phone'] = ''
                m_dict['nickname'] = NewRemainder[0]
                m_dict['text'] = NewRemainder[1:]
        # It's just a message from the system
        else:
                m_dict['message_type'] = 'system'
                m_dict['phone'] = ''
                m_dict['text'] = remainder.strip()
        out_dicts.append(m_dict)

    add_country_codes(out_dicts)
    return out_dicts

def add_country_codes(dicts):
    for d in dicts:
        try:
            if d['phone']:
                clean_number = d['phone'].replace('(', '').replace(')', '')
                number = phonenumbers.parse(clean_number)
                code = phonenumbers.region_code_for_number(number)
                country = pycountry.countries.get(alpha_2=code).name
                d['phone_country_code'] = code
                d['phone_country'] = country
        except KeyError as e:
            print("Couldn't find phone number in {}".format(d))
            raise e

def verify_dicts(message_dictionaries):
    test_regex = {'date': '[0-9]{2}/[0-9]{2}/[0-9]{4}',
                  'time': '[0-9]{1,2}:[0-9]{2} (pm|am)',
                  'phone': '\+[0-9 ]+',
                  'nickname': '.',
                  'text': '.+',
                  'message_type': "[system|action|message]",
                  'text_direction': '[l2r|r2l]',
                  'message_id': '[0-9]+',
                  'phone_country_code': '[A-Z]{2}',
                  'phone_country': '[A-Z].+'}
    for m_dict in message_dictionaries:
        for key in m_dict:
            try:
                if len(m_dict[key]) > 0:
                    assert (re.match(test_regex[key], m_dict[key].strip()))
            except AssertionError:
                print("Dodgy looking " + key + ": " + m_dict[key])
                print("On message {}".format(m_dict))


def output_to_csv(dicts, out_path):
    fieldnames = ['message_id', 'date', 'time', 'message_type',
                  'phone', 'nickname', 'phone_country_code', 'phone_country',
                  'text', 'text_direction']
    with open(out_path, 'w', encoding="utf8") as out_file:
        writer = csv.DictWriter(out_file, fieldnames)
        writer.writeheader()
        writer.writerows(dicts)


def parse_commandline_args():
    parser = argparse.ArgumentParser(description=r"""
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
        """, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', '--input-file',
                        type=str, dest='input_file', metavar='path',
                        help='Path to a .txt file containing a WhatsApp '
                             'message history.')
    parser.add_argument('-o', '--output-file',
                        type=str, dest='output_file', metavar='path',
                        help='Desired path to output .csv file.'
                             'If this already exists, it WILL be overwritten '
                             'without warning (apart from this warning)')
    parser.add_argument('-v', '--validate',
                        action='store_true', dest='validate', default=False,
                        help='Validate: If true, will validate each entry '
                             'according to expected format (e.g will check '
                             'time is in hh:mm am/pm) and print offenders.'
                             'Default: false')

    return parser.parse_args()


def main():
    args = parse_commandline_args()
    messages = read_to_messages(args.input_file)
    dicts = convert_messages_to_dicts(messages)
    if args.validate:
        print('Verifying messages...')
        verify_dicts(dicts)
        print('Done.')
    output_to_csv(dicts, args.output_file)


if __name__ == "__main__":
    main()
