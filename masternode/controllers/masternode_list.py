#!/usr/bin/env python
import asyncio, sys, json

from .. import version
from .interfaces import AbstractSigningController

class MasternodeListController(AbstractSigningController):
	def __init__(self, config, logger, signing_service, mnsync_service):
		super().__init__(config, logger, signing_service)
		self.mnsync_service = mnsync_service

	def set_routes(self, router):
		router.add_get('/api/mn/list', self.handle)
		router.add_get('/api/mn/list/{mode}', self.handle)

	@asyncio.coroutine
	def handle(self, request):
		mode = request.match_info.get('mode', None)
		nested = True

		# Pseudo-modes to affect nesting behaviour
		if not mode:
			nested = False 

		if mode == 'assoc':
			mode = 'full'
			nested = False

		#try:
		mn_list = self.mnsync_service.get_masternode_list(mode).attributes(nested)
		#except Exception as e:
		#	return self.error_response('Failed to obtain masternode list', 559)	# first 4 letters of "wallet" on T9 keyboard

		return self.response(mn_list)
