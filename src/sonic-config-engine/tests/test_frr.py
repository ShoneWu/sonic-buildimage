import filecmp
import json
import os
import subprocess

import tests.common_utils as utils

from unittest import TestCase

class TestCfgGen(TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.script_file = utils.PYTHON_INTERPRETTER + ' ' + os.path.join(self.test_dir, '..', 'sonic-cfggen')
        self.t0_minigraph = os.path.join(self.test_dir, 't0-sample-graph.xml')
        self.t0_port_config = os.path.join(self.test_dir, 't0-sample-port-config.ini')
        self.output_file = os.path.join(self.test_dir, 'output')

    def tearDown(self):
        try:
            os.remove(self.output_file)
        except OSError:
            pass


    def run_script(self, argument, check_stderr=False):
#        print '\n    Running sonic-cfggen ' + argument
        if check_stderr:
            output = subprocess.check_output(self.script_file + ' ' + argument, stderr=subprocess.STDOUT, shell=True)
        else:
            output = subprocess.check_output(self.script_file + ' ' + argument, shell=True)

        if utils.PY3x:
            output = output.decode()

        linecount = output.strip().count('\n')
        if linecount <= 0:
            print('    Output: ' + output.strip())
        else:
            print('    Output: ({0} lines, {1} bytes)'.format(linecount + 1, len(output)))
        return output

    def run_diff(self, file1, file2):
        output = subprocess.check_output('diff -u {} {} || true'.format(file1, file2), shell=True)

        if utils.PY3x:
            output = output.decode()

        return output

    def run_case(self, template, target, extra_data=None):
        template_dir = os.path.join(self.test_dir, '..', '..', '..', 'dockers', 'docker-fpm-frr', "frr")
        conf_template = os.path.join(template_dir, template)
        constants = os.path.join(self.test_dir, '..', '..', '..', 'files', 'image_config', 'constants', 'constants.yml')
        cmd_args = self.t0_minigraph, self.t0_port_config, constants, conf_template, template_dir, self.output_file
        cmd = "-m %s -p %s -y %s -t %s -T %s > %s" % cmd_args
        if extra_data:
            cmd = ("-a '%s' " % json.dumps(extra_data)) + cmd
        self.run_script(cmd)

        original_filename = os.path.join(self.test_dir, 'sample_output', utils.PYvX_DIR, target)
        r = filecmp.cmp(original_filename, self.output_file)
        diff_output = self.run_diff(original_filename, self.output_file) if not r else ""

        return r, "Diff:\n" + diff_output

    def test_config_frr(self):
        self.assertTrue(*self.run_case('frr.conf.j2', 'frr.conf'))

    def test_bgpd_frr(self):
        self.assertTrue(*self.run_case('bgpd/bgpd.conf.j2', 'bgpd_frr.conf'))

    def test_zebra_frr(self):
        self.assertTrue(*self.run_case('zebra/zebra.conf.j2', 'zebra_frr.conf'))

    def test_bgpd_frr_dualtor(self):
        extra_data = {"DEVICE_METADATA": {"localhost": {"subtype": "DualToR"}}}
        self.assertTrue(*self.run_case('bgpd/bgpd.conf.j2', 'bgpd_frr_dualtor.conf', extra_data=extra_data))
