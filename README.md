# python-terraform-vmware

This project is a sample of wrapping terraform executable in python django to implement clone virtual machine on vmware.

## When running it with the following command: 
`python manage.py runserver 0:8080`

2 daemons would start up:
**deployer**: regularly check db changes, if any, call terraform to apply the change. 
**refresher**: regularly check terraform.state to sync actual status from vmware, 
if any change(indicates some unexpected changes outside terraform), call terraform to restore back the db state. 

## Some valuable references from this repo:

1. django models.
2. wrapper TfExecuter: 
* multithread based encapsulation to switch terraform directories just before terraform apply/refresh.
* asynchronization mode to call terraform apply. 
* encapsulate terraform operations separately in functions: tfinit/tfoutput/tfapply/tfrefresh/tfconfig/tfshow
3. wrapper CmdRunner: 
* execute command in thread, and provide getstatusoutput_[cur/fin/inc], 3 ways of getting output. 
