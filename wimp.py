# Assume python 2.7
# Path to the interpreter is deliberately not mentioned.

import os
import sys
import optparse
import shlex
import subprocess

def print_and_exit(rc, message):
    if len(message):
        print message
    sys.exit(rc)

def is_windows():
    return os.getenv('OS') == 'Windows_NT'

def is_supported_os():
    if not is_windows():
        return True
    if os.getenv('USERPROFILE'):
        return True
    print_and_exit(1, 'Unsupported Windows version, should be Vista or higher')
    return False

# A really appealing option for crypto library:
# Stanford Javascript Crypto Library http://bitwiseshiftleft.github.io/sjcl/
# BSD or GPLv2 license
#
# For now, we use openssl
# http://how-to.linuxcareer.com/using-openssl-to-encrypt-messages-and-files
#
def encrypt(password, data):
    encrypted_data = run_pipe(['echo -n ' + data, 'openssl enc -base64'])
    return encrypted_data[0:-1] # last character is newline - drop it

def decrypt(password, encrypted_data):
    data = run_pipe(['echo ' + encrypted_data, 'openssl enc -base64 -d'])
    return data

# For more insights:
#   https://crackstation.net/hashing-security.htm
def hash(password):
    signature = run_pipe(['echo -n ' + password, 'openssl dgst -sha1'])
    return signature[0:-1] # last character is newline - drop it

def run_pipe(cmds):
    # Assemble a pipe line:
    # - First stage in pipe: don't override stdin
    # - Mid/Last stages: wire ins and outs
    #
    # Last stage's stdout must be PIPE, otherwise communicate won't capture stdout
    pipe = []
    pipe.append(subprocess.Popen(shlex.split(cmds[0]), stdout=subprocess.PIPE))
    for i in range(1, len(cmds)):
        pipe.append(subprocess.Popen(shlex.split(cmds[i]), stdin=pipe[-1].stdout, stdout=subprocess.PIPE))

    # Allow pipe[i] to receive a SIGPIPE if pipe[i+1] exits. Do not apply this to the last proc in pipe !!!
    for p in pipe[0:-1]:
        p.stdout.close()

    (out, err) = pipe[-1].communicate()
    if err:
        print_and_exit(2, 'pipe error: ' + str(err))
    return out

def default_path():
    if is_windows():
        return os.path.join(os.getenv('USERPROFILE'), 'wimp')
    return os.path.join(os.getenv('HOME'), '.wimp')

def cl_parse(argv):
    description="\
WIMP (Where Is My Password) password manager. Supports multiple tags, \
passwords history, AES encryption. \ New passwords are read from stdin. JSON \
is used for all options that take complex arguments. PASSWORD is formatted as \
a single JSON object, TAGS is formatted as a JSON list of strings. Unless '--\
path' is given, passwords are stored in $HOME/.wimp/ on Linux or in \
$USERPROFILE/wimp on Windows. With '--path' multiple password storages can be \
used. Each passwords storage is protected with a single master password. \
"
    usage="python %prog <--add|--update|--delete|--list_all> [options]"
    epilog='''
Example 1: Add new password
    python wimp.py --add="{'title':'stackoverflow', 'username':'my_user_name', \\
        'url'='http://stackoverflow.com/', 'tags':'fun'}"

Example 2: List all passwords tagged as 'fun' and/or 'work'
    python wimp.py --list_by_tags="['fun','work']"
'''

    # dont strip new-lines from multiline epilog but just print it as-is
    optparse.OptionParser.format_epilog = lambda self, formatter: self.epilog

    parser = optparse.OptionParser(description=description, usage=usage,
        version="%prog 0.1", epilog=epilog)

    group = optparse.OptionGroup(parser, "Basics", "")
    group.add_option("-a", "--add", dest="add_entry", metavar="PASSWORD",
        help="Add new password.")
    group.add_option("-u", "--update", dest="update_entry", metavar="ID",
        help="Update fields of existing entry")
    group.add_option("-d", "--delete", dest="delete_entry_id", metavar="ID",
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
    group.add_option("--path", dest="path", default=default_path(), metavar="PATH",
        help="Path to passwords repository. If omitted, the default is " + default_path() + ".")
    parser.add_option_group(group)

    (opt, left_over_args) = parser.parse_args(argv)
    print opt

    # Check that exactly one option in this list is not None
    # TODO: mutually exclusive options and subcommands are supported in argparse package. Consider using it.
    mandatory_exclusives = [opt.add_entry, opt.update_entry, opt.delete_entry_id, opt.list_all]
    if len(mandatory_exclusives) - mandatory_exclusives.count(None) != 1:
        print_and_exit(3, usage)

    return (opt, left_over_args)

def main(argv):
    is_supported_os() # exit if not
    (opt, left_over_args) = cl_parse(argv)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
