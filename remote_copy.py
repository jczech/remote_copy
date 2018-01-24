#!/usr/bin/env python3

from __future__ import print_function
from builtins import input

import time
import paramiko
import select
import os
import sys
import getpass
import argparse
import hashlib



class FilesToTransfer:
    # get files to transfer
    def __init__(self, mypath):
        self.mydirnames = []
        self.myfilenames = []
        self.myfilesize = []

        self.rootdir, self.firstdir = os.path.split(mypath)
        print("ROOT=", self.rootdir)
        self.mydirnames.append([mypath, self.firstdir])
        for (dirpath, dirnames, filenames) in os.walk(mypath):
            for name in filenames:
                fullpathname = os.path.join(dirpath, name)
                relpathname = os.path.relpath(fullpathname, self.rootdir)
                hash_str = ""
                with open(fullpathname, 'rb') as f:
                    h = hashlib.sha1()
                    h.update(f.read())
                    hash_str = h.hexdigest()
                self.myfilenames.append([
                    os.path.getsize(fullpathname),
                    fullpathname,
                    relpathname,
                    hash_str])
            for name in dirnames:
                fullpathname = os.path.join(dirpath, name)
                relpathname = os.path.relpath(fullpathname, self.rootdir)
                self.mydirnames.append([fullpathname, relpathname])

        # log the filenames and hashes
        with open("./fname_hash.txt", 'w') as out:
            for _, fname, _, hash_str in self.myfilenames:
                out.write("{0}, {1}\n".format(fname, hash_str)) 


def make_directories(sftp, remote_dir, dirnames):
    # make the directory tree
    t1 = time.time()
    sftp.chdir(remote_dir)
    for local, remote in dirnames:
        print(local, remote)
        try:
            sftp.lstat(remote)
        except:
            sftp.mkdir(remote)
    t2 = time.time()
    print('Elapsed (makedir): %f seconds' % (t2 - t1))


def push_files(sftp, remote_dir, filenames):
    # remote copy every file
    t1 = time.time()
    sftp.chdir(remote_dir)
    bytestransfer = 0.0
    for tbytes, local, remote, hash_str in filenames:
        print(tbytes, local, remote)
        sftp.put(local, remote)
        bytestransfer = bytestransfer + tbytes
    t2 = time.time()
    print('Elapsed (makedir): %f seconds' % (t2 - t1))
    print('Bytes Transferred: %f seconds' % (bytestransfer))
    print('Throughput: %f MegaBytes per second' % ((bytestransfer/1000000.0)/(t2-t1)))


def setup_argparser():
    parser = argparse.ArgumentParser(
        description="How to profile MCell using nutmeg tests:")
    parser.add_argument(
        "-l", "--local_dir", required=True, help="local directory")
    parser.add_argument(
        "-r", "--remote_dir", required=True, help="remote directory")
    return parser.parse_args()


def main():
    args = setup_argparser()
    local_dir = args.local_dir
    remote_dir = args.remote_dir

    host = "data.psc.edu"
    port = 22
    username = input("Enter your username:")
    password = getpass.getpass(prompt="Enter your password:")

    transfer_files = FilesToTransfer(local_dir)
    print("FILENAMES")
    for fname in transfer_files.myfilenames:
        print(fname)

    paramiko.util.log_to_file('mylog')

    # Open a transport
    transport = paramiko.Transport((host, port))
    # Authenticate
    transport.connect(username=username, password=password)

    # Upload
    sftp = paramiko.SFTPClient.from_transport(transport)
    make_directories(sftp, remote_dir, transfer_files.mydirnames)
    push_files(sftp, remote_dir, transfer_files.myfilenames)

    t1 = time.time()
    print('Elapsed: %f seconds' % (time.time() - t1))

    # Close
    sftp.close()
    transport.close()

    command = 'ls -l'
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # client.set_missing_host_key_policy(paramiko.WarningPolicy())

        client.connect(host, port=port, username=username, password=password)

        stdin, stdout, stderr = client.exec_command(command)
        print(stdout.read(),)

    finally:
        client.close()

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, port=port, username=username, password=password)
    transport = client.get_transport()
    channel = transport.open_session()
    channel.exec_command("ls")
    while True:
        if channel.exit_status_ready():
            break
        rl, wl, xl = select.select([channel], [], [], 0.0)
        if len(rl) > 0:
            # Must be stdout
            print(channel.recv(1024))


if __name__ == "__main__":
    main()
