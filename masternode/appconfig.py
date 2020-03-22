""" Wapper for configparser """

import os
from configparser import ConfigParser

class ApplicationConfig(ConfigParser):
	default_section='DEFAULT'

	""" Interface for using configuration,  """
	def __init__(self, filename):
		super().__init__(self)

		if not os.path.isfile(filename):
			raise ValueError('Configuration file not found: ' + filename)

		try:
			self.read(filename)
		except:
			raise ValueError('Error reading configuration file: ' + filename)


