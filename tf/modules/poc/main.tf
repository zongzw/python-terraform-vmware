variable "vsphereuser" {
  description = "username for access vcenter"
  type = "string"
  default = "vsphere.local\\localadmin"
}

variable "vspherepassword" {
  description = "password for ${var.vsphereuser} to access vcenter"
  type = "string"
  default = "L0cal@dmin"
}

variable "vsphereserver" {
  description = "vsphere server address"
  type = "string"
  default = "xxx.xx.xx.x"
}

variable "datacenter" {
  description = "vcenter address"
  type = "string"
  default = "Datacenter"
}

variable "datastore" {
  description = "datastore name"
  type = "string"
  default = "datastore_x"
}

variable "cluster" {
  description = "host or cluster name"
  type = "string"
  default = "Dedi03"
}

variable "network" {
  description = "network name"
  type = "string"
  default = "VM Network"
}

variable "vmtemplate" {
  description = "template from ovf"
  type = "string"
  default = "/Datacenter/vm/Photon"
}

variable "vmname" {
  description = "the vm name to create"
  type = "string"
  default = "terraform-test"
}

variable "num_cpus" {
  description = "number of cpus"
  type = "string"
  default = "2"
}

variable "memory" {
  description = "size of memory"
  type = "string"
  default = "1024"
}

variable "count" {
  
}

variable "disk" {
}

variable "configuration" {}

provider "vsphere" {
  #alias          = "dp"
  user           = "${var.vsphereuser}"
  password       = "${var.vspherepassword}"
  vsphere_server = "${var.vsphereserver}"

  # if you have a self-signed cert
  allow_unverified_ssl = true
}

data "vsphere_datacenter" "dc" {
  name = "${var.datacenter}"
}

data "vsphere_datastore" "datastore" {
  name          = "${var.datastore}"
  datacenter_id = "${data.vsphere_datacenter.dc.id}"
}

data "vsphere_resource_pool" "pool" {
  name          = "${var.cluster}/Resources"
  datacenter_id = "${data.vsphere_datacenter.dc.id}"
}

data "vsphere_network" "network" {
  name          = "${var.network}"
  datacenter_id = "${data.vsphere_datacenter.dc.id}"
}

data "vsphere_virtual_machine" "template_from_ovf" {
  name          = "${var.vmtemplate}"
  datacenter_id = "${data.vsphere_datacenter.dc.id}"
}

resource "vsphere_virtual_machine" "vm" {
  #provider         = "vsphere.dp"

  count            = "${var.count}"
  name             = "${var.vmname}-${count.index}-${uuid()}"
  resource_pool_id = "${data.vsphere_resource_pool.pool.id}"
  datastore_id     = "${data.vsphere_datastore.datastore.id}"

  num_cpus = "${var.num_cpus}"
  memory   = "${var.memory}"
  #guest_id = "${data.vsphere_virtual_machine.template_from_ovf.id}"
  guest_id = "other3xLinux64Guest"

  network_interface {
    network_id = "${data.vsphere_network.network.id}"
  }
  
  clone {
    template_uuid = "${data.vsphere_virtual_machine.template_from_ovf.id}"
  }

  #provisioner "file" {
  #  source      = "scripts/configure-vm.sh"
  #  destination = "/root/configure-vm.sh"
  #}

  lifecycle {
    #ignore_changes = ["name"]
  }

  connection {
    type        = "ssh"
    user        = "root"
    password    = "kubernetes"
  }

  provisioner "remote-exec" {
    inline = [
    		"echo ${var.configuration} | base64 -d > /root/configure.sh",
    		"/usr/bin/sed -i 's/\r//g' /root/configure.sh",
    		"chmod +x /root/configure.sh",
    		"/root/configure.sh",
    ]
    #on_failure = "continue"
  }

  disk {
    label = "disk0"
    size  = "${var.disk}"
  }
}

output "vm_names" {
  value = "${vsphere_virtual_machine.vm.*.name}"
}
