#!/usr/bin/env python

import importlib

class dAppRegistry(object):
	_dapp_facades = {}
	_dapp_controllers = {}
	_dapp_services = {}

	def __init__(self, config, logger):
		self.config = config
		self.logger = logger

	def register_dapp(self, dapp_provider):
		# todo: do assertions on object base class type
		if dapp_provider.name() in self._dapp_facades:
			self.logger.warning('dAppRegistry::register_dapp: dApp %s is already registered' % dapp_provider.name())

		self.logger.debug('dAppRegistry::register_dapp: Registering dApp %s' % dapp_provider.name())
		self._dapp_facades[dapp_provider.name()] = dapp_provider.make_facade(self)
		self._dapp_controllers[dapp_provider.name()] = dapp_provider.make_controller(self)

	def load_dapps(self, container):
		modules = {}

		for dapp_name in self.config['dapps'].get('enabled').split(','):
			modules[dapp_name.strip()] = importlib.import_module("masternode.dapps.vpn.provider")
			self.register_dapp(modules[dapp_name.strip()].dAppProvider(container))

	def get_all(self):
		return self._dapp_facades

	def get_names(self):
		return self._dapp_facades.keys()

	def get_all_controllers(self):
		return self._dapp_controllers

	def register_service(self, name, service):
		if not name in self._dapp_services:
			self._dapp_services[name] = service

	def get_service(self, name):
		if name in self._dapp_services:
			return self._dapp_services[name]
		return None
