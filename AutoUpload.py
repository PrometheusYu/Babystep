#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import time
import datetime
import zipfile
from ftplib import FTP
import logging
import pdb

remoteip = '172.20.72.206'
remoteport = 21
loginname = 'stanley'
loginpassword = 'stanley'
localpath = 'D:\dst\\'
remotepath = '/bakfile'
filename = (datetime.datetime.today() - datetime.timedelta(days=time.localtime().tm_wday + 1)).strftime("%Y-%m-%d") + '.zip'
srcdir= 'D:\src'
dstdir= 'D:\dst'


class MyFTP(FTP):  # 对FTP的继承
    # 继承父类中的方法,在子类中可以直接调用
    # 重载父类中retrbinary的方法
    def storbinary(self, cmd, fd, fsize=0, rest=0):
        blocksize = 1024
        cmpsize = rest
        self.voidcmd('TYPE I')
        conn = self.transfercmd(cmd, rest)  # 此命令实现从指定位置开始上传,以达到续传的目的
        while 1:
            if rest == 0:
                buf = fd.read(blocksize)
            else:
                fd.seek(cmpsize)
                buf = fd.read(blocksize)
            if buf:
                conn.send(buf)
            else:
                print 'Ending'
                break
            cmpsize += blocksize
        conn.close()
        fd.close()


def ConnectFTP(remoteip, remoteport, loginname, loginpassword):
    ftp = MyFTP()
    try:
        ftp.connect(remoteip, remoteport)
    except:
        return (0, 'connect failed!')
    else:
        try:
            ftp.login(loginname, loginpassword)
        except:
            return (0, 'login failed!')
        else:
            return (1, ftp)

def mywork(remoteip, remoteport, loginname, loginpassword, remotepath, localpath, filename, filesize):
    res = ConnectFTP(remoteip, remoteport, loginname, loginpassword)
#   pdb.set_trace()
    bufsize = 1024
    if res[0] != 1:
        print res[1]
        sys.exit()
    ftp = res[1]
    fd=open(localpath+filename,'rb')
    ftp.set_pasv(0)  # 到这一部出现连接超时请偿试设置非0值
    if remotepath:
        ftp.cwd(remotepath)
        file_list = ftp.nlst()
        result=0
        if filename in file_list:
            rest = ftp.size(filename)
            logging.info('Conntinue uploading...')
            try:
                ftp.storbinary('STOR %s' % filename, fd, filesize, rest)
            except:
                result=1
        else:
            logging.info('Starting upload:...')
            try:
                ftp.storbinary('STOR %s' % filename, fd, filesize, 0)
            except:
                result=1
        ftp.set_debuglevel(0)
        return result

def zipgenerate(srcdir,dstdir):
#   pdb.set_trace()
    os.chdir(srcdir)
    Files=os.listdir('.')
    todayfiles=[]

    while len(Files) > 0:
        File=Files.pop()
        ModifiedDate=time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(File)))
        LatestSunday=(datetime.datetime.today() - datetime.timedelta(days=time.localtime().tm_wday + 1)).strftime("%Y-%m-%d")
        if( ModifiedDate==LatestSunday ):
            todayfiles.append(File)
#   pdb.set_trace()
    f = zipfile.ZipFile(os.path.join(dstdir,LatestSunday)+'.zip','w', zipfile.ZIP_DEFLATED)
    for i in todayfiles:
        f.write(i)
    f.close()

def zipdel3weekago():

    Files = os.listdir('.')
    logging.info('Begin to remove files 3 weeks ago')
    for i in Files:
        date = int(os.stat(i).st_mtime)
        now = int(time.time())
        if (now - date) > 1814400: #文件生成超过三周（3*7*24*3600）就删除
            logging.info('File %s has been removed', i)
            os.remove(i)

if __name__ == '__main__':

    os.chdir(dstdir)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename='AutoUpload.log',
                        filemode='w')
    zipdel3weekago()
    if not os.path.exists(filename):
        logging.info('File %s does not exists, now begin to generate zip file', filename)
        zipgenerate(srcdir,dstdir)
        logging.info('File generating finished.')
    patht=os.path.join(localpath,filename)
    statinfo = os.stat(patht)
    filesize = int(statinfo.st_size)
    logging.info('Size of file that needs to be uploaded is %d', filesize)
    logging.info('Now begin to upload zip file...')
    time.sleep(5)

    count=0
    while count < 12:
        count += 1
        result=mywork(remoteip, remoteport, loginname, loginpassword, remotepath, localpath, filename, filesize)
        if result != 0:
            logging.info('Try to connect to ftp server %d times in 5 minutes', count)
            time.sleep(300)
        elif result == 0:
            logging.info('Successfully finished uploading!!!')
            break
    sys.exit()