#!/usr/bin/env python3

import time
import paramiko
import select
import os
import sys
import getpass
import argparse


class GetFilesToTransfer:
    # get files totransfer
    def __init__(self, mypath):
        # self.mydirpath = []
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
                self.myfilenames.append([os.path.getsize(fullpathname), fullpathname, relpathname])
            for name in dirnames:
                fullpathname = os.path.join(dirpath, name)
                relpathname = os.path.relpath(fullpathname, self.rootdir)
                self.mydirnames.append([fullpathname, relpathname])

    def rootdir(self):
        return self.rootdir

    def dirnames(self):
        return self.mydirnames

    def filenames(self):
        return self.myfilenames


def make_directories(sftp, remote_dir, dirnames):
    # make directory
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
    # make directory
    t1 = time.time()
    sftp.chdir(remote_dir)
    bytestransfer = 0.0
    for tbytes, local, remote in filenames:
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

    TrFiles = GetFilesToTransfer(local_dir)
    print("FILENAMES")
    for i in TrFiles.filenames():
        print(i)

    paramiko.util.log_to_file('mylog')

    # Open a transport

    transport = paramiko.Transport((host, port))
    # Authenticate
    transport.connect(username=username, password=password)
    # Go!

    sftp = paramiko.SFTPClient.from_transport(transport)

    make_directories(sftp, remote_dir, TrFiles.dirnames())
    push_files(sftp, remote_dir, TrFiles.filenames())

    # sftpstat = paramiko.SFTPClient.stat(sftp)
    # sftp1 = paramiko.SFTPClient.from_transport(transport)
    # sftp2 = paramiko.SFTPClient.from_transport(transport)

    # print(sftp)
    # print(sftp1)
    # print(sftp2)

    # List Remote Directory
    # remotefiles = sftp.listdir()
    # print(remotefiles)
    # remoteobj = sftp.listdir_attr()
    # for i in remoteobj:
    #   print(i)
    #   print(i.st_size)
    #   print(i.st_uid)
    #   print(i.st_gid)
    #   print(i.st_mode)
    #   print(i.st_atime)
    #   print(i.st_mtime)
    # print(sftpstat)
    #  Download

    # filepath = 'README.GET'
    # localpath = 'README.GET'
    # sftp.get(filepath, localpath)

    # Upload
    t1 = time.time()
    print('Elapsed: %f seconds' % (time.time() - t1))
    # filepath = 'README.GET'
    # localpath = 'README.PUT'
    # sftp.put(localpath, filepath)

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
