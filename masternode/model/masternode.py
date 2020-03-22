""" Veles Masternode (gen 2) masternode models """
from .interfaces import AbstractFillableObject, AbstractFillableCollection
import copy

class Masternode(AbstractFillableObject):
	""" Represents a masternode """
	_required = ['ip', 'outpoint', 'payee']		# Required attributes
	status = 'UNKNOWN'
	dapp_status = 'UNKNOWN'
	signing_key = None
	last_checked = None

class MasternodeCollection(AbstractFillableCollection):
	""" Dictionary that holds Masternode objects """
	def add(self, mn):
		self[mn.ip] = mn

class MasternodeList(MasternodeCollection):
	""" Holds a masternode list, that can be obtained in several modes """
	def __init__(self, entries, mode = None):
		super().__init__(entries)
		self._mode = mode

	def get_mode(self):
		return self._mode

class MasternodeInfoList(MasternodeList):
	def attributes(self, nested=True):
		result = {}

		for ip, mn in self.items():
			result[ip] = mn.attributes(nested)

		return result

class MasternodeInfoMixin(Masternode):
	""" Represents a last known state of a masternode with associated information """

	def update_core_info(self, core_info):
		self._core_info = core_info

	def update_version_info(self, version_info):
		self._version_info = version_info

	def update_service_info(self, service_info):
		self._service_info = service_info

	def get_core_info(self):
		if not hasattr(self, '_core_info'):
			return {}

		return self._core_info

	def get_service_info(self):
		if not hasattr(self, '_service_info'):
			return {}

		return self._service_info

	def get_version_info(self):
		if not hasattr(self, '_version_info'):
			return {}

		return self._version_info

	def attributes(self, nested=False):
		result = super().attributes()

		if nested:
			if self.get_core_info():
				result['core'] = self.get_core_info()
			if self.get_service_info():
				result['services'] = self.get_service_info()
			if self.get_version_info():
				result['version'] = self.get_version_info()
		else:
			result = {
				**result,
				**self.get_core_info(),
				**self.get_version_info(),
				**self.get_service_info(),
			}

		return result

class MasternodeInfo(MasternodeInfoMixin, Masternode):
	""" Represents a last known state of a masternode with associated information """
	pass

