# Project ansible for Juniper devices

- Author: NhanDD <hp.duongducnhan@gmail.com>

## Developement setup

### Requirements

- Python version >= 3.10
- Using poetry to manage python package ```pip install poetry```

### Install package

- Using poetry install ```poetry install```
- Using pip to install extra lib ansible-lint ```pip install ansible-lint```
- Install ansible-galaxy collection install junipernetworks.junos
  - Enable env

    ``` shell
    poetry shell 
    ```

  - Using ansible-galaxy to install collection

    ``` shell
    ansible-galaxy collection install junipernetworks.junos
    ```

## Run playbook add interface vlan

### Setup

- Update host ip address, username, password in ./ansible_juniper/inventory/development/
  - File hosts.yml
  
    ``` vim
    ---
    all:
      children:
        lab:
          hosts:
            <device_ip_address>:
    
    ```

  - File ./group_vars/lab.yml
  
    ``` vim
    ---
    ansible_port: 22
    ansible_user: <device-username>
    ansible_password: <device-password>
    ansible_netconf_username: <device-netconf-username>
    ansible_netconf_password: <device-netconf-username>
    ansible_network_os: junos

    ```

- Configure playbook interface name, vlan name, vlan ip
  - file: ./ansible_juniper/playbook/pb_add_interface_vlan/vars.yml

    ``` vim
    ---
    vlan_id: 102
    vlan_name: "VLAN102"
    interface: "xe-0/0/4"

    ```

### Run playbook and check result

- Run playbook using command
  - Enable environment

    ``` shell
    poetry shell
    ```

  - Run playbook

    ``` shell
    ansible-playbook ansible_juniper/playbook/pb_add_interface_vlan.yml
    ```

  - Check result at:
    **result/pb_pb_add_interface_vlan/at_<datetime-run-task>/<host>/final_result.json**
  