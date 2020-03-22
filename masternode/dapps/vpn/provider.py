#!/usr/bin/env python

from ..interfaces import AbstractProvider
from . import facade, status_service, metric_service, certificate_service, config_service, gateway
from .controllers import dvpn_config

class dAppProvider(AbstractProvider):
	dapp_name = 'VPN'
	services = {}

	def __init__(self, container):
		self.container = container

	def name(self):
		return self.dapp_name

	def register_services(self, dapp_registry):
		dapp_registry.register_service('VPNManagementGateway', gateway.VPNManagementGateway(
			config=self.container.app_config(), 
			logger=self.container.logger(),
			))
		dapp_registry.register_service('VPNMetricService', metric_service.VPNMetricService(
			config=self.container.app_config(), 
			logger=self.container.logger(),
			metric_repository=self.container.metric_repository(),
			mnsync_service=self.container.mn_sync_service(),
			mn_gateway=self.container.masternode_gateway(),
			))
		dapp_registry.register_service('VPNStatusService', status_service.VPNStatusService(
			config=self.container.app_config(), 
			logger=self.container.logger(),
			vpn_gateway=dapp_registry.get_service('VPNManagementGateway'),
			metric_service=dapp_registry.get_service('VPNMetricService'),
			))
		dapp_registry.register_service('CertificateProvisioningService', certificate_service.CertificateProvisioningService(
			config=self.container.app_config(), 
			logger=self.container.logger(),
			))
		dapp_registry.register_service('ConfigProvisioningService', config_service.ConfigProvisioningService(
			config=self.container.app_config(), 
			logger=self.container.logger(),
			))

	def make_facade(self, dapp_registry):
		self.register_services(dapp_registry)

		# Return main dApp facade that will act as API between other
		# parts of system and internal services registered here.
		return facade.VPNdAppFacade(
			config=self.container.app_config(), 
			logger=self.container.logger(),
			status_service=dapp_registry.get_service('VPNStatusService'),
			metric_service=dapp_registry.get_service('VPNMetricService')
			)

	def make_controller(self, dapp_registry):
		self.register_services(dapp_registry)

		# Return main dApp facade that will act as API between other
		# parts of system and internal services registered here.
		return dvpn_config.ConfigProvisioningController(
			config=self.container.app_config(), 
			logger=self.container.logger(),
			signing_service=self.container.mn_signing_service(),
			certificate_service=dapp_registry.get_service('CertificateProvisioningService'),
			config_service=dapp_registry.get_service('ConfigProvisioningService'),
			)
