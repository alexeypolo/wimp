# Assume python 2.7
# Path to the interpreter is deliberately not mentioned.

import os
import errno
import sys
import optparse
import shlex
import subprocess
import threading
import getpass
from datetime import datetime
import json

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
def encrypt(lines):
    return run_proc(lines, 'openssl enc -des-ecb -pass env:WIMP_PASS')

def decrypt(encrypted_lines):
    return run_proc(encrypted_lines, 'openssl enc -d -des-ecb -pass env:WIMP_PASS')

def hash_rsa(password):
    hashed = run_proc(password, 'openssl dgst -sha1')
    return hashed[0:-1] # drop 'newline' that is appended by openssl

def pump_input(pipe, lines):
    with pipe:
        for line in lines:
            pipe.write(line)

def run_proc(input_string, command):
    p = subprocess.Popen(command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1)
    threading.Thread(target=pump_input, args=[p.stdin, input_string]).start()
    with p.stdout:
        output_string = p.stdout.read()
    p.wait()
    return output_string

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
    group.add_option("--start", action="store_true", dest="start",
        help="Start session")
    group.add_option("--end", action="store_true", dest="end",
        help="End session")
    group.add_option("--add", dest="add_entry", metavar="{id:value, password:value, tags:value, other:value, ...}",
        help="Add new password.")
    group.add_option("--update", dest="update_entry", metavar="{id:value, password:value, tags:value, other:value, ...}",
        help="Update fields of existing entry")
    group.add_option("--delete", dest="delete_entry_id", metavar="id",
        help="Delete existing entry")
    group.add_option("--list", action="store_true", dest="list_all",
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
    mandatory_exclusives = [opt.start, opt.end, opt.add_entry, opt.update_entry, opt.delete_entry_id, opt.list_all]
    if len(mandatory_exclusives) - mandatory_exclusives.count(None) != 1:
        print_and_exit(3, usage)

    return (opt, left_over_args)

def get_timestamp():
    return datetime.now().strftime("%y-%m-%d_%H:%M:%S")

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def master_password_new(path, master_hash_file):
    print 'Initializing wimp repo in', path
    make_sure_path_exists(path)

    password = getpass.getpass('New master password:')
    if not password:
        print_and_exit(5, "Empty string is not allowed")
        return None

    password2 = getpass.getpass('Confirm master password:')
    if password != password2:
        print_and_exit(5, "Passwords do not match")
        return None

    with open(master_hash_file, 'w') as f:
        f.write(hash_rsa(password))

    print 'OK'
    return password

def master_password_verify(master_hash_file):
    # ask user for master password
    password = getpass.getpass('Master password:')
    with open(master_hash_file) as f:
        fdata = f.read()

    if fdata != hash_rsa(password):
        print_and_exit(5, 'MISMATCH')
        return None

    print 'MATCH: OK'
    return password

db_dict={}
db_path=""
def db_store():
    db_dict['laststore'] = get_timestamp()
    with open(db_path, 'w') as f:
        f.write(encrypt(json.dumps(db_dict)))

def db_load():
    global db_dict
    with open(db_path) as f:
        db_dict = json.loads(decrypt(f.read()))
    db_dict['lastload'] = get_timestamp()

def init_repo(path):
    global db_dict, db_path

    # Create repo if none exists
    # Create new or verify existing master password
    master_hash_file = os.path.join(path, 'master.hash')
    if os.path.exists(master_hash_file):
        password = master_password_verify(master_hash_file)
    else:
        password = master_password_new(path, master_hash_file)

    os.putenv('WIMP_PASS', password)

    # DB: load if exists, or create new + store
    db_path = os.path.join(path, 'db.wimp')
    if os.path.isfile(db_path):
        db_load()
    else:
        db_dict['born'] = get_timestamp()
        db_store()
    return 0

def main(argv):
    is_supported_os() # exit if not
    (opt, left_over_args) = cl_parse(argv)
    init_repo(opt.path)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
