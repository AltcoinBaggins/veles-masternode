#!/usr/bin/env python
from ..interfaces import AbstractFacade

class VPNdAppFacade(AbstractFacade):
	app_name = 'VPN'

	def __init__(self, config, logger, status_service, metric_service):
		self.config = config
		self.logger = logger
		self.logger.debug('VPNdAppFacade: dApp VPN loaded')
		self.status_service = status_service
		self.metric_service = metric_service

	def get_status_service(self):
		return self.status_service

	def get_metric_service(self):
		return self.metric_service
