""" Command-line interface to the main masternode app """

import argparse

from . import version
from .container import IocContainer

class MasternodeJobManagerCLI(object):
	def run(self):
		""" Run the commandline interface """
		args = self.get_args()
		container = self.get_container(args)
		container.app().init_dapps(container)
		container.app().run_job(args['job'])

	def get_args(self):
		""" Proccess commandline args if not done yet, exit with help on errors """
		parser = argparse.ArgumentParser(description='Veles Masternode Jobs commandline interface version {}'.format(version.mn_version))
		parser.add_argument('job', help="Job to launch")
		parser.add_argument('--config', default='/etc/veles/mn.conf', help='Veles Masternode configuration file.')
		return vars(parser.parse_args())

	def get_container(self, args):
		return IocContainer(
			config=args	# Container's initial parameters, configuration to load real config
		)

# Just run if launched directly
if __name__ == '__main__':
	app = MasternodeJobManagerCLI()
	app.run()

