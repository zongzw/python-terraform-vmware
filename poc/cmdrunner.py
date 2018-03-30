import json
import sys
import os
import subprocess
import shlex
import threading

'''
Not supported: 
1. built-in functions, like "cd"
2. pipeline, like: cat <somefile> | wc -l
3. context based, like: cd /path/to/file; ls
'''

class CmdRunner:
    def __init__(self, cmd):
        self.cmd = shlex.split(cmd)
        self.thread = threading.Thread(target=self.executeImp)
        self.read = 0
        self.status = None
        self.output = []
        self.lock = threading.Lock()

    def execute(self):
        self.thread.start()
        return self

    def getstatusoutput_cur(self):
        return (self.status, '\n'.join(self.output))
        
    def getstatusoutput_fin(self):
        self.thread.join()
        return (self.status, '\n'.join(self.output))
        
    def getstatusoutput_inc(self):
        self.lock.acquire()
        total = len(self.output)
        output = '\n'.join(self.output[self.read:])
        self.read = total
        status = self.status
        self.lock.release()

        return (self.status, output)

    def executeImp(self):
        print(self.cmd)
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while(True):
            retcode = self.p.poll()
            line = self.p.stdout.readline().decode()
            
            self.lock.acquire()
            self.status = retcode
            if line.strip('\n') != '': self.output.append(line.strip('\n'))
            self.lock.release()

            if(retcode is not None):
                break

if __name__ == "__main__":
    import time
    
    os.chdir('/tmp')
    c = CmdRunner("pwd")
    print(c.execute().getstatusoutput_fin())
    exit(0)
    
    tf = CmdRunner("/usr/local/bin/terraform workspace list")
    tf.execute()
    
    (status, output) = tf.getstatusoutput_fin()
    print(status)
    print(output)
    print("%d, %s" % (status, output))    
