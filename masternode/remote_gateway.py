""" Gateway to communicate with remote masternode """
import requests, json, time

from . import version

class MasternodeApiResponse(object):
	""" Represents a response from Veles Masternode API, returned by
	    RemoteMasternodeGateway """
	def __init__(self, result, success = True, latency = None, error = None, headers = {}, protocol = 'https/json'):
		self.result = result
		self.success = success
		self.latency = latency
		self.error = error
		self.headers = headers
		self.protocol = protocol
		self.received_at = time.time()

class RemoteMasternodeGateway(object):
	""" Communicates with remote masternode """
	webapi_base_uri = 'api'
	http_request_headers = {'User-Agent': 'VelesMasternode/%s' % version.mn_version}

	def __init__(self, config, logger):
		self.config = config
		self.logger = logger

	def webapi_query(self, ip, method = 'status', argument = None):
		""" Sends API query over HTTPS GET request to remote masternode """

		# If we're trying to contact our own server IP, use localhost to avoid routing issues
		if ip == self.config['masternode'].get('server_addr', ''):
			ip = '127.0.0.1'

		if argument:
			url = 'https://%s/%s/%s/%s' % (ip, self.webapi_base_uri, method, argument)
		else:
			url = 'https://%s/%s/%s' % (ip, self.webapi_base_uri, method)

		error = None
		result = None
		request_start = time.time()

		try:
			response = requests.get(url, headers=self.http_request_headers, verify=False, timeout=int(self.config['masternode'].get('query_timeout', 10)))
		except Exception as e:
			self.logger.error('RemoteMasternodeGateway::query_dapp_status: Query error: ' + str(e))
			error = 'Query error: ' + str(e)

		if not error:
			try:
				parsed = response.json()
			except Exception as e:
				self.logger.error('RemoteMasternodeGateway::query_dapp_status: Query error: JSON parser: ' + str(e))
				error = 'Query error: JSON parser: ' + str(e)

		if not error:
			if 'error' in parsed and parsed['error'] != None:
				self.logger.error('RemoteMasternodeGateway::query_dapp_status: Remote error: ' + parsed['error'])
				error = parsed['error']
			elif 'result' not in parsed:
				self.logger.error('RemoteMasternodeGateway::query_dapp_status: Unsupported reply format: missing "result" field')
				error = 'Query error: Unsupported reply format: missing "result" field'
			else:
				result = parsed['result']

		request_end = time.time()

		return MasternodeApiResponse(
			result,
			success = False if error else True,
			latency = round((request_end - request_start) * 1000),
			error = error,
			protocol = 'https/json',
			)


