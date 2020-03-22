#!/usr/bin/env python
from ..interfaces import AbstractStatusService

class VPNStatusService(AbstractStatusService):
	def __init__(self, config, logger, vpn_gateway, metric_service):
		self.config = config
		self.logger = logger
		self.vpn_gateway = vpn_gateway
		self.metric_service = metric_service

	def get_dapp_status(self):
		state_name = 'ACTIVE'

		try:
			server_stats = self.vpn_gateway.get_status()
		except Exception as e:
			server_stats = {}
			state_name = 'INACTIVE'
			self.logger.error('VPNStatusService::dapp_status: Failed to obtain OpenVPN server status: ' + str(e))

		try:
			metrics_stats = {
				'daily': self.metric_service.get_recent_metrics('daily'),
				'hourly': self.metric_service.get_recent_metrics('hourly'),
			}
			global_metrics_stats = {
				'daily': self.metric_service.get_global_metrics('daily'),
			}
		except Exception as e:
			metrics_stats = {}
			state_name = 'INACTIVE'
			self.logger.error('VPNStatusService::dapp_status: Failed to obtain OpenVPN network device status: ' + str(e))

		return {**server_stats, 'metrics': metrics_stats, 'global_metrics': global_metrics_stats, 'state_name': state_name}
