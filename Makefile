SOURCE_DIR := ansible_juniper
PLAYBOOK_DIR := ${SOURCE_DIR}/playbook

setup-dev:
	pip install --upgrade pip
	pip install ansible-lint
	poetry install
	poetry run ansible-galaxy collection install junipernetworks.junos


run-add-interface-vlan:
	poetry run ansible-playbook ${PLAYBOOK_DIR}/pb_add_interface_vlan.yml