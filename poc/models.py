from django.db import models

import json
import hashlib
import base64
import threading
import time
import random

import socket
import sys
import os

import pdb
# Create your models here.
from .tf import TfExecuter

class VirtualMachine(models.Model):
    
    cpus_opts = [1, 2, 4, 8, 16]
    CPU_CHOICES = []
    for n in cpus_opts: 
        CPU_CHOICES.append(("%d" % n, "%d" % n))
        
    mem_opts = [128, 256, 512, 1024, 2048, 4096, 8192, 16384]
    MEM_CHOICES = []
    for n in mem_opts:
        MEM_CHOICES.append(("%d" % n, "%d" % n))
        
    config_default = """#!/bin/bash
echo "Finished virtual machine provision: `date`"
uname -a
echo "Starting to configure ..."

# ======= Input your configuration process =======

exit 0
"""
    id          = models.AutoField(primary_key=True)
    
    name        = models.CharField(max_length=256, default="vm-name-prefix-maxlength-256")
    count       = models.PositiveIntegerField(default='1')
    cpus        = models.CharField(max_length=8, choices=tuple(CPU_CHOICES), default='2')
    memory      = models.CharField(max_length=8, choices=tuple(MEM_CHOICES), default='512')   
    disk        = models.PositiveIntegerField(default='20')
    network     = models.CharField(max_length=128, default="VM Network")
    config      = models.TextField(default=config_default)
    
    report      = models.TextField(default="None")
    status      = models.CharField(max_length=32, default="new")
    log         = models.TextField(default="EOF")
    cursign        = models.CharField(max_length=128, editable=False, default='0')
    finsign     = models.CharField(max_length=128, editable=False, default='0')
    
    def __str__(self):
        #return json.dumps(self.to_json())
        rlt = []
        for n in ['id', 'name', 'count', 'status', 'cpus', 'memory', 'disk', 'network']:
            rlt.append("%s: %s" % (n, eval("self.%s" % n)))
        return " | ".join(rlt)
    
    def to_json(self):
        return {
            'id': "vm_%d" % self.id,
            'name': self.name, 
            'count': self.count,
            'cpus': self.cpus, 
            'memory': self.memory, 
            'disk': self.disk, 
            'network': self.network,
            'config': self.config,
            'report': self.report,
            'status': self.status,
            'log': self.log,
            'cursign': self.cursign,
            'finsign': self.finsign
        }
        
    def deploy(self):
        j = self.to_json()
        for n in ['id', 'status', 'log', 'cursign', 'finsign', 'report']: del j[n]
        
        md5j = hashlib.md5(json.dumps(j).encode("utf-8")).hexdigest()
        if md5j == self.cursign: return
        
        self.cursign = md5j
        self.finsign = '1'
        self.save()

        tfconf = """
module "poc" {
  source = "../../modules/poc"
  vsphereuser = "vsphere.local\\\\localadmin"
  vspherepassword = "L0cal@dmin"
  vsphereserver = "xxx.xx.xx.x"
  
  datacenter = "Datacenter"
  datastore = "datastore_x"
  cluster = "Dedi03"
  vmtemplate = "/Datacenter/vm/Photon"

  vmname = "%s"
  count = "%s"
  num_cpus = "%s"
  memory = "%s"
  disk = "%s"
  network = "%s"
  configuration = "%s"
}

output "vm-names" {
  value = ["${module.poc.vm_names}"]
}
""" % (
    j['name'],
    j['count'],
    j['cpus'],
    j['memory'],
    j['disk'],
    j['network'],
    base64.b64encode(bytes(j['config'], 'utf-8')).strip().decode()
    )

        configuration = {
            'id': "vm_%d" % self.id,
            'tf': tfconf,
        }

        self.status = "ChangeRequest"
        self.log = "Change request is committed."
        self.save()
        
        tf = TfExecuter(configuration, self.update_statusoutput)
        tf.deploy()

    def refresh(self):
        
        if self.cursign != self.finsign:
            # may in progress of deploying
            return
        
        configuration = {
            'id': "vm_%d" % self.id,
            'tf': ''
        }
        tf = TfExecuter(configuration, self.update_statusoutput)
        tf.refresh()

    def update_statusoutput(self, status, output, type='log'):
        #self.status  = "%s-%s" % (self.status, status)
        if status != '': self.status = status
        if type == 'log':
            tstr = time.strftime("%Y-%m-%d %H:%M:%S : ", time.localtime(time.time()))
            self.log = '\n'.join([self.log, '', tstr, output])
            logs = self.log.split('\n')
            if len(logs) > 500: # TODO: move this logic to a separate thread for log rotating.
                self.log = '\n'.join(logs[500:])
        elif type == 'report':
            self.report = output
        elif type == 'sign':
            self.cursign = '0'
            self.finsign = '1'
        elif type =='fin':
            self.finsign = self.cursign
        else:
            raise Exception("not supported type: %s" % type)
        
        self.save()

class rundaemon:
    def start_deployer():
        while True:
            vms = VirtualMachine.objects.all()
            for n in vms:
                try:
                    n.deploy()
                except Exception as e: 
                    print("When try to deploy %s, exception happens: %s" % (n, e))
            
            time.sleep(5)

    def start_refresher():
        while True:
            vms = VirtualMachine.objects.all()
            for n in vms:
                try:
                    n.refresh()
                except Exception as e: 
                    print("When try to refresh %s, exception happens: %s" % (n, e))
            
            '''
            When terraform calls are too frequently, vmware.vapi reports error:
            * module.poc.vsphere_virtual_machine.vm[0]: 
                vsphere_virtual_machine.vm.0: 
                    Get unexpected status code: 500: 
                        call failed: Error response from vCloud Suite API: 
            {
                "value": {
                    "messages": [
                        {
                            "id": "vapi.bindings.method.impl.unexpected",
                            "default_message": "Provider method implementation threw unexpected exception: Rejecting login on a session where login failed",
                            "args": [
                                "Rejecting login on a session where login failed"
                            ]
                        }
                    ]
                },
                "type": "com.vmware.vapi.std.errors.internal_server_error"
            }
            '''
            time.sleep(100)
    
    def start_daemonprocess():
        
        def daemon():
            time.sleep(10)  # wait for manage.py to start.
        
            threading.Thread(target=rundaemon.start_deployer).start()
            threading.Thread(target=rundaemon.start_refresher).start()
        
        threading.Thread(target=daemon).start()
        
    if len(sys.argv) >= 2 and sys.argv[1] == "runserver":
        
        if os.path.exists("daemon.exists.pid"):
            os.system("rm daemon.exists.pid")
        else:
            os.system("echo >> daemon.exists.pid")
            start_daemonprocess()
        

