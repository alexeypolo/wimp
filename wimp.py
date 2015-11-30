# Assume python 2.7
# Path to the interpreter is deliberately not mentioned.

import os
import sys
import optparse

def cl_parse(argv):
    description="WIMP (Where Is My Password) password manager. \
Supports multiple tags, passwords history, AES encryption. \
New passwords are read from stdin. \
JSON is used for all options that take complex arguments. \
PASSWORD is formatted as a single JSON object, TAGS is formatted as a JSON list of strings.\
"
    usage="python %prog [options]"
    epilog='''
Example 1: Add new password
    python wimp.py --add="{'title':'stackoverflow', 'username':'my_user_name', 'url'='http://stackoverflow.com/', 'tags':'fun'}"

Example 2: List all passwords tagged as 'fun' and/or 'work'
    python wimp.py --list_by_tags="['fun','work']"
'''

    # dont strip new-lines from multiline epilog but just print it as-is
    optparse.OptionParser.format_epilog = lambda self, formatter: self.epilog

    parser = optparse.OptionParser(description=description, usage=usage, version="%prog 0.1", epilog=epilog)

    group = optparse.OptionGroup(parser, "Basics", "")
    group.add_option("-a", "--add", dest="add_password", metavar="PASSWORD",
        help="Add new password.")
    group.add_option("-u", "--update", dest="update_id", metavar="ID",
        help="Update fields of existing entry")
    group.add_option("-d", "--delete", dest="delete_id", metavar="ID",
        help="Delete existing entry")
    group.add_option("-l", "--list", action="store_true", dest="list_all", metavar="[TAGS]",
        help="List all passwords")
    parser.add_option_group(group)

    group = optparse.OptionGroup(parser, "Advanced", "")
    group.add_option("--list_by_tags", dest="list_by_tags", metavar="[TAGS]",
        help="List passwords filtered by a list of tags")
    group.add_option("--list_tags", dest="list_tags", metavar="[TAGS]",
        help="List tags")
    group.add_option("--echo", dest="echo_password", action="store_true",
        help="Echo when typing a new password. By default this option is 'off'.")
    parser.add_option_group(group)

    (options, left_over_args) = parser.parse_args(argv)

    return (options, left_over_args)

def main(argv):
    (options, left_over_args) = cl_parse(argv)

    print options

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
