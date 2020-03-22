#!/usr/bin/env python
import asyncio, sys, json

from .. import version
from .interfaces import AbstractSigningController

class MasternodeStatusController(AbstractSigningController):
	def __init__(self, config, logger, signing_service, core_node, dapp_registry):
		super().__init__(config, logger, signing_service)
		self.core = core_node
		self.dapps = dapp_registry.get_all()

	def set_routes(self, router):
		router.add_get('/api/status', self.handle)

	@asyncio.coroutine
	def handle(self, request):
		try:
			chain_info = self.core.call('getblockchaininfo')
			net_info = self.core.call('getnetworkinfo')
			halving_info = self.core.call('gethalvingstatus')
		except Exception as e:
			return self.error_response('Wallet error', 9255)	# first 4 letters of "wallet" on T9 keyboard

		core_status = {
			'blocks': chain_info['blocks'],
			'bestblockhash': chain_info['bestblockhash'],
			'timeoffset': net_info['timeoffset'],
			'connections': net_info['connections'],
			'relayfee': net_info['connections'],
			'halvings_occured': halving_info['halvings_occured'],
			'blocks_to_next_epoch': halving_info['blocks_to_next_epoch'],
			'epoch_supply_target_reached': halving_info['epoch_supply_target_reached'],
		}
		version_status = {
			'core_version': net_info['version'],
			'protocol_version': net_info['protocolversion'],
			'mn_version': version.mn_version,
			'api_version': version.api_version,		
		}
		
		# MN status
		try:
			mn_status = self.core.call('masternode', ['status'])
		except Exception as e:
			return self.error_response('Wallet error', 9255)

		if mn_status and 'error' in mn_status:
			mn_status = {
				'service': self.config['masternode'].get('server_addr'),
				'status': (mn_status['error']['message'] if 'message' in mn_status['error'] else '')
			}
		mn_status['service'] = mn_status['service'].split(':')[0]	# strip port
		mn_status['signing_key'] = self.config['masternode'].get('signing_key')

		try:
			mn_status['state_name'] = self.core.call('masternodelist', ['status', mn_status['outpoint']])[mn_status['outpoint']]
		except:
			mn_status['state_name'] = 'UNKNOWN'

		# Dapps status
		dapp_status = {}
		for dapp_name, dapp_facade in self.dapps.items():
			dapp_status[dapp_name] = dapp_facade.get_status_service().get_dapp_status()

		return self.response({
			'blockchain': core_status,
			'services': dapp_status,
			'masternode': mn_status,
			'version': version_status
			})
