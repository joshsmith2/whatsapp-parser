import main
import unittest
import re
import os

class ProcessingTest(unittest.TestCase):
    """ These tests were set up with live data which has not been included in
    the repo. You will need to supply your own sample WhatsApp data, then
    update the following tests:
        test_first_message_is_correct
        test_right_count
        test_country_code_conversion
    to fit your data.
    """

    def setUp(self):
        test_root = os.path.dirname(os.path.realpath(__file__))
        data_dir = os.path.join(test_root, 'data')
        self.test_csv = os.path.join(data_dir, 'sample_chat.txt')

        self.first_message = "28/08/2018, 11:55 am - Messages to this group " \
                             "are now secured with end-to-end encryption. " \
                             "Tap for more info."
        self.messages = main.read_to_messages(self.test_csv)
        self.date_regex = "[0-9]{2}/[0-9]{2}/[0-9]{4}"

    def test_right_count(self):
        self.assertEqual(len(self.messages), 25)

    def test_date_regex_present_in_each_record(self):
        for m in self.messages:
            self.assertTrue(re.match(self.date_regex, m))

    def test_first_message_is_correct(self):
        self.assertEqual(self.messages[0], self.first_message)

    def test_verify_by_regex(self):
        dicts = main.convert_messages_to_dicts(self.messages)
        main.verify_dicts(dicts)

    def test_country_code_conversion(self):
        dicts = main.convert_messages_to_dicts(self.messages)
        self.assertEqual(dicts[6]['phone_country'], 'United Kingdom')

    def test_whole_process(self):
        if os.path.exists('test_out.csv'):
            os.remove('test_out.csv')
        dicts = main.convert_messages_to_dicts(self.messages)
        main.verify_dicts(dicts)
        main.output_to_csv(dicts, 'test_out.csv')
        self.assertTrue(os.path.exists('test_out.csv'))


