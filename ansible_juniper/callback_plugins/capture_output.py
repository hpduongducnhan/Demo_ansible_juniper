# Make coding more python3-ish, this is required for contributions to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

# not only visible to ansible-doc, it also 'declares' the options the plugin requires and how to configure them.


import os
import time
import json
from typing import Dict, List
from datetime import datetime
from ansible.playbook.task import Task
from ansible.executor.task_result import TaskResult
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager
from ansible.vars.hostvars import HostVars


copied_callback_options = {
    'display_skipped_hosts': True,
    'display_ok_hosts': True,
    'display_failed_stderr': False,
    'show_custom_stats': False,
    'show_per_host_start': False,
    'check_mode_markers': False,
    'show_task_path_on_failure': False,
    'result_format': 'json',
    'pretty_results': None
}


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'log-file'
    CALLBACK_NAME = 'capture_output'

    def __init__(self, *args, **kwargs):
        self.nhandd_playbook_name = None
        self.nhandd_start_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.nhandd_host_outputs = {}
        return super().__init__(*args, **kwargs)

    def v2_playbook_on_start(self, playbook):
        self.nhandd_playbook_name = os.path.splitext(os.path.basename(playbook._file_name))[0]
        return super().v2_playbook_on_start(playbook)

    def v2_runner_on_failed(self, result: TaskResult, ignore_errors=False):
        res = super().v2_runner_on_failed(result, ignore_errors)
        self._capture_output(result)
        return res

    def v2_runner_on_ok(self, result: TaskResult, **kwargs):
        res = super().v2_runner_on_ok(result, **kwargs)
        self._capture_output(result)
        return res

    def v2_runner_on_unreachable(self, result: TaskResult):
        res = super().v2_runner_on_unreachable(result)
        self._capture_output(result)
        return res

    def v2_runner_on_skipped(self, result: TaskResult):
        res = super().v2_runner_on_skipped(result)
        self._capture_output(result)
        return res

    def v2_playbook_on_stats(self, stats):
        res = super().v2_playbook_on_stats(stats)
        # This method is called after the playbook has finished running
        self._write_outputs()  # Write the output files here
        return res

    def _get_task_register_output(self, host: str, task_result: TaskResult, register_names: List[str]) -> Dict:
        result = {name: None for name in register_names}
        task: Task = task_result._task
        if not task or not isinstance(task, Task):
            return
        var_manager: VariableManager = task.get_variable_manager()
        if not var_manager or not isinstance(var_manager, VariableManager):
            return

        all_vars: Dict = var_manager.get_vars()
        if not all_vars:
            return
        host_vars: HostVars = all_vars.get('hostvars', {})
        if not host_vars:
            return

        for name in register_names:
            result[name] = host_vars.get(host, {}).get(name, {})
        return result

    def _collect_config_status_output_from_register(self, host: str, result: TaskResult, register_names: List[str] = []):
        if not register_names:
            register_names = [
                'res_show_conf_before', 'res_show_conf_after',
                'res_show_status_before', 'res_show_status_after',
                'res_device_facts'
            ]

        res = self._get_task_register_output(host, result, register_names)
        try:
            config_before: List = self.nhandd_host_outputs[host]['before']['config']
            config_after: List = self.nhandd_host_outputs[host]['after']['config']

            status_before: List = self.nhandd_host_outputs[host]['before']['status']
            status_after: List = self.nhandd_host_outputs[host]['after']['status']

            for k, v in res.items():
                if k == 'res_show_conf_before' and v and v not in config_before:
                    print('get key:', k)
                    config_before.append(v)
                elif k == 'res_show_conf_after' and v and v not in config_after:
                    config_after.append(v)

                elif k == 'res_show_status_before' and v and v not in status_before:
                    status_before.append(v)
                elif k == 'res_show_status_after' and v and v not in status_after:
                    status_after.append(v)
                elif k == 'res_device_facts':
                    self.nhandd_host_outputs[host]['device_facts'] = v

        except Exception as e:
            print(f'Collect config status output from register get exception: {e}')

    def _capture_output(self, result: TaskResult):
        host = result._host.get_name()
        if host not in self.nhandd_host_outputs:
            self.nhandd_host_outputs[host] = {
                'before': {
                    'status': [],
                    'config': [],
                },
                'after': {
                    'status': [],
                    'config': [],
                },
                'outputs': [],
                'device_facts': {}
            }

        task_name = result.task_name
        if task_name in ('Gathering Facts',):
            return

        # auto collect register output
        self._collect_config_status_output_from_register(host, result)

        try:
            saved = {
                'task_name': task_name,
                "is_failed": result.is_failed(),
                "is_changed": result.is_changed(),
                "is_skipped": result.is_skipped(),
                "is_unreachable": result.is_unreachable(),
                "result": result._result
            }
            self.nhandd_host_outputs[host]['outputs'].append({time.time(): saved})
        except Exception as e:
            print(f"Capture output get exception {e}")

    def _write_outputs(self):
        try:
            output_dir = os.path.join('result', f'pb_{self.nhandd_playbook_name}', f'at_{self.nhandd_start_time}')
            for host, info in self.nhandd_host_outputs.items():
                host_output_dir = os.path.join(output_dir, f'host_{host}')
                os.makedirs(host_output_dir, exist_ok=True)

                output_file = os.path.join(host_output_dir, f"final_result.json")
                with open(output_file, "w") as f:
                    json.dump(info['outputs'], f, indent=4)

                before_execution_file = os.path.join(host_output_dir, f"before_execution.json")
                with open(before_execution_file, "w") as f1:
                    json.dump(info['before'], f1, indent=4)

                after_execution_file = os.path.join(host_output_dir, f"after_execution.json")
                with open(after_execution_file, "w") as f2:
                    json.dump(info['after'], f2, indent=4)

                device_facts_file = os.path.join(host_output_dir, f"device_facts.json")
                with open(device_facts_file, "w") as f3:
                    json.dump(info['device_facts'], f3, indent=4)

        except Exception as e:
            print(f"Write output get exception {e}")
