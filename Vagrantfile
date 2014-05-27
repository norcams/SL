# -*- mode: ruby -*-
# vi: set ft=ruby :

$provision = <<SHELL
yum -y install https://dl.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
yum -y install perl perl-Net-IP perl-NetAddr-IP perl-Net-Netmask perl-JSON
SHELL

VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "centos65"
  config.vm.box_url = "http://opscode-vm-bento.s3.amazonaws.com/vagrant/virtualbox/opscode_centos-6.5_chef-provisionerless.box"

  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--ioapic", "off"]
    vb.customize ["modifyvm", :id, "--cpus", 1]
    vb.customize ["modifyvm", :id, "--memory", 1024]
  end

  config.vm.provision :shell, inline: $provision

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :machine
  end

end
