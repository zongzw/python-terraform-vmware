import threading
from .cmdrunner import CmdRunner
import pdb
import time
import re
import os
import filecmp

# TODO:
#    The CmdRunner used in TfExecuter class is subprocess based. 
#    Better solution is using pty, which start a pseudo terminal for context based executing. 
class TfExecuter:
    workerLock = threading.Lock()
    def __init__(self, config, reporter):
        self.tfbin = "/usr/local/bin/terraform"
        self.tfhome = "/data/VMwareOps/tf"
        
        self.config = config
        self.reporter = reporter
        self.confighome = "%s/configurations/%s" % (self.tfhome, self.config['id'])
    
    def deploy(self):
        deploythread = threading.Thread(target=self.deployImp)
        deploythread.start()
        
    def deployImp(self):        
        self.tfconfig()
        try:
            TfExecuter.workerLock.acquire()
            os.chdir(self.confighome)
            self.tfinit()
            self.tfapply()
        except Exception as e:
            print("failed to call terraform to execute vmware operations: %s " % e)
            self.reporter('failed', "failed to call terraform to execute vmware operations: %s " % e)
            return
        finally:
            TfExecuter.workerLock.release()

    def refresh(self):
        refreshthread = threading.Thread(target=self.refreshImp)
        refreshthread.start()
        
    def refreshImp(self):
    
        try:
            TfExecuter.workerLock.acquire()
            
            os.chdir(self.confighome)
            
            self.tfrefresh()
            
            if not filecmp.cmp("%s/terraform.tfstate" % self.confighome, "%s/terraform.tfstate.refresh" % self.confighome):
                self.reporter('resource-not-match', "physical resources are modified outside, scheduled to redeploy", type='report')
                self.reporter('', '', type='sign')
            else:
                output = self.tfoutput()
                self.reporter('refreshed', 'resources are updated %s: \n%s' % (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())), output), type='report')
            
        except Exception as e:
            print('failed to refresh actual state of resources: %s' % e)
            self.reporter('refresh-failed', 'failed to refresh actual state of resources: %s' % e)
            return
        finally:
            TfExecuter.workerLock.release()

    def tfinit(self):
        # $tfbin init -no-color -input=false
        (status, output) = CmdRunner("%s init -no-color -input=false" % self.tfbin)\
                        .execute().getstatusoutput_fin()
        if status != 0:
            raise Exception('failed to init: %s' % output)
        else:
            self.reporter('initialized', output)
    
    def tfoutput(self):
        (status, output) = CmdRunner("%s output" % self.tfbin)\
                        .execute().getstatusoutput_fin()
        if status != 0:
            raise Exception("failed to get result, select workspace failed: %s" % output)
        else:
            self.reporter('ready', output, type='report')
            
        return output
        
    def tfapply(self):
        apply = CmdRunner("%s apply -no-color -auto-approve -state=%s/terraform.tfstate %s" % (self.tfbin, self.confighome, self.confighome))
        apply.execute()
        
        def wait4fin():
            while True:
                (status, output) = apply.getstatusoutput_inc()
                
                if status is None:
                    if output.strip('\n') != '': self.reporter("in-progress", output)
                else: 
                    self.reporter('ready' if status == 0 else 'failed', output)
                    self.reporter('', '', type='fin')
                    if status == 0:
                        try:
                            TfExecuter.workerLock.acquire()
                            os.chdir(self.confighome)
                            self.tfoutput()
                        except Exception as e:
                            self.reporter("ready-but-no-report", "failed to fetch report after ready: %s" % e)
                        finally:
                            TfExecuter.workerLock.release()
                    break
                
                time.sleep(1)
                
        threading.Thread(target=wait4fin).start()
         
    def tfconfig(self):
        
        # create confighome
        (status, output) = CmdRunner("/bin/mkdir -p %s" % self.confighome)\
                        .execute().getstatusoutput_fin()
        if status != 0:
            self.reporter("failed", "return: %d, failed to create directory %s: %s" % (status, self.confighome, output))
            return
        self.reporter("configuring", "created folder: %s" % self.confighome)
        
        # create configfile
        try:
            with open("%s/main.tf" % self.confighome, 'w') as fw:
                fw.write(self.config['tf'])
        except Exception as e:
            self.reporter("failed", "failed to create main.tf: %s" % e)
            return
        self.reporter("configured", "created main.tf")
        
        # link terraform.d
        if not os.path.exists("%s/terraform.d" % self.confighome): 
            (status, output) = CmdRunner("ln -s %s/terraform.d %s" % (self.tfhome, self.confighome))\
                            .execute().getstatusoutput_fin()
            if status != 0:
                raise Exception("failed to link %s/terraform.d to %s/terrform.d: %s" % (self.tfhome, self.confighome, output))
            else:
                self.reporter("configuring", "created link for terraform.d")
    
    def tfshow(self):
            (status, output) = CmdRunner("%s show -no-color -module-depth=0" % self.tfbin)\
                                .execute().getstatusoutput_fin()
            if status != 0:
                raise Exception("failed to get initial state: %s" % output)
            
            return output
    
    def tfrefresh(self):
            (status, output) = CmdRunner("%s refresh -no-color -input=false -state-out=%s/terraform.tfstate.refresh %s" % (self.tfbin, self.confighome, self.confighome))\
                                            .execute().getstatusoutput_fin()
            if status != 0:
                raise Exception("failed to refresh physical resources: %s" % output) 
            else:
                self.reporter('refreshed', "refresh physical resources: %s" % output)
            