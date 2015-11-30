# Assume python 2.7
# Path to the interpreter is deliberately not mentioned.

import os
import sys
import optparse

def cl_parse(argv):
    usage="python %prog [options]"
    epilog='''
Example 1:
    TODO

Example 2:
    TODO
'''

    # dont strip new-lines from multiline epilog but just print it as-is
    optparse.OptionParser.format_epilog = lambda self, formatter: self.epilog

    parser = optparse.OptionParser(usage=usage, version="%prog 0.1", epilog=epilog)

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
    parser.add_option_group(group)

    (options, left_over_args) = parser.parse_args(argv)

    return (options, left_over_args)

def main(argv):
    (options, left_over_args) = cl_parse(argv)

    print options

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
