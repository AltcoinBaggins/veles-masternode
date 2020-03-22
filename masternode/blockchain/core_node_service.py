""" Module to handle communication with wallet/node daemon """
from .core_node_rpc import CoreNodeRPCClient

class CoreNodeService(object):
	""" Service to communicate with the Veles Core daemon """
	def __init__(self, config, logger):
		""" Constructor """
		self.core_node = CoreNodeRPCClient(
	        host=config['wallet'].get('rpchost', '127.0.0.1'),
	        port=config['wallet'].get('rpcport', '21338'),
	        username=config['wallet'].get('rpcuser'),
	        password=config['wallet'].get('rpcpassword'),
	        )
		self.config = config
		self.logger = logger

	def call(self, command, args = []):
		""" Calls a command on daemon with given arguments through RPC """
		return self.core_node.call(command, args)
		