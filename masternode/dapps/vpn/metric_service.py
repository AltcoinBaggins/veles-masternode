"""dVPN Metric Service to collect, store and retrieve dApp metrics"""

from datetime import datetime, timedelta

from ..interfaces import AbstractGlobalMetricService

class VPNMetricService(AbstractGlobalMetricService):
	data_prefix = 'vpn'
	intervals = {
		'hourly': 3600,
		'daily': 3600*24
	}

	def __init__(self, config, logger, metric_repository, mnsync_service, mn_gateway):
		""" Constructor """
		self.config = config
		self.logger = logger
		self.repo = metric_repository
		self.mnsync_service = mnsync_service
		self.mn_gateway = mn_gateway

	def get_recent_metrics(self, interval_name):
		""" Retrieves metrics for the last specified time interval """
		self._assert_interval_supported(interval_name)
		
		now = datetime.now()

		if interval_name == 'hourly':
			key_timeformat = "hourly:%m-%d_%H"
			last_time = now - timedelta(hours=1)
			last_time_since = last_time - timedelta(hours=1)
		elif interval_name == 'daily':
			key_timeformat = "daily:%m-%d"
			last_time = now - timedelta(days=1)
			last_time_since = last_time - timedelta(days=1)
		else:
			return {}	# this should not happen

		last_metrics_key = '{}:{}'.format(self.data_prefix, last_time.strftime(key_timeformat))

		if not self.repo.exists(last_metrics_key):
			self.logger.info('VPNMetricService::get_recent_metrics: No recent metrics in database for interval ' + interval_name)
			return {}

		return self.repo.get(last_metrics_key)


	def update_recent_metrics(self, interval_name):
		""" Calculates and updates metrics for the last specified time interval """
		self._assert_interval_supported(interval_name)
		
		now = datetime.now()

		if interval_name == 'hourly':
			key_timeformat = "hourly:%m-%d_%H"
			prev_time = now - timedelta(hours=1)
		elif interval_name == 'daily':
			key_timeformat = "daily:%m-%d"
			prev_time = now - timedelta(days=1)
		else:
			self.logger.debug('VPNMetricService::update_recent_metrics: No action for interval ' + interval_name)
			return

		prev_metrics_key = '{}:{}'.format(self.data_prefix, prev_time.strftime(key_timeformat))
		cur_metrics_key = '{}:{}'.format(self.data_prefix, now.strftime(key_timeformat))
		cur_metrics_state = self._get_current_metrics()

		if self.repo.exists(cur_metrics_key + ':state'):
			self.logger.info('VPNMetricService::update_recent_metrics: Metrics state already saved for interval ' + interval_name)
			return

		self.repo.store(cur_metrics_key + ':state', cur_metrics_state)

		if self.repo.exists(prev_metrics_key + ':state'):
			prev_metrics_state = self.repo.get(prev_metrics_key + ':state')

		else:
			self.logger.debug('VPNMetricService::update_recent_metrics: No previous metric records found for interval ' + interval_name)
			return

		self.repo.store(cur_metrics_key, {
			'interval_since': prev_time.isoformat().split('.')[0],	# remove miliseconds
			'interval_until': now.isoformat().split('.')[0],
			**self._compare_metrics(prev_metrics_state, cur_metrics_state)
			})

	def get_global_metrics(self, interval_name):
		""" Retrieves global metrics for the last specified time interval """
		self._assert_interval_supported(interval_name, exclude=["hourly"])

		now = datetime.now()
		yesterday = now - timedelta(days=1)
		metrics_key = 'global:daily:{}:{}'.format(self.data_prefix, yesterday.strftime("%m-%d"))

		if not self.repo.exists(metrics_key):
			self.logger.info('VPNMetricService::get_global_metrics: No recent metrics in database for interval ' + interval_name)
			return {}

		return self.repo.get(metrics_key)

	def update_global_metrics(self, interval_name):
		""" Updates global metrics from all the masternodes, could be time consuming"""
		self._assert_interval_supported(interval_name, exclude=["hourly"])

		now = datetime.now()
		yesterday = now - timedelta(days=1)
		metrics_key = 'global:daily:{}:{}'.format(self.data_prefix, yesterday.strftime("%m-%d"))

		if self.repo.exists(metrics_key):
			self.logger.info('VPNMetricService::update_global_metrics: Found already existing metrics in database for interval ' + interval_name)
			return

		self.repo.store(metrics_key, {
			'interval_since': yesterday.isoformat().split('.')[0],	# remove miliseconds
			'interval_until': now.isoformat().split('.')[0],
			**self._collect_global_metrics(interval_name)
			})


	# Private methods
	def _get_current_metrics(self):
		"""Returns current dVPN metric state, as per OS internal counter"""
		interface = self.config['dapps.vpn'].get('tun_interface', 'tun1')
		bytes_in, bytes_out = self._get_network_bytes(interface)
		return { 'bytes_in': bytes_in, 'bytes_out': bytes_out}

	def _compare_metrics(self, previous_metrics, current_metrics):
		"""Returns delta of two dVPN metric states, eg. of both components bytes_in and bytes_out"""
		try:
			if current_metrics['bytes_in'] < previous_metrics['bytes_in'] or current_metrics['bytes_out'] < previous_metrics['bytes_out']:
				self.logger.info('VPNMetricService::_compare_metrics: VPN metrics have been reset within last hour, not enough data')
				return { 'bytes_in': 0, 'bytes_out': 0}

			return {
				'bytes_in': current_metrics['bytes_in'] - previous_metrics['bytes_in'],
				'bytes_out': current_metrics['bytes_out'] - previous_metrics['bytes_out'],
			}
		except Exception as e:
			raise Exception('VPNMetricService::_compare_metrics: Failed to compare given metrics: ' + str(e))

	def _get_network_bytes(self, interface):
		"""Returns number of bytes in and out of specified network interface since boot/ifup"""
		for line in open('/proc/net/dev', 'r'):
			if interface in line:
				data = line.split('%s:' % interface)[1].split()
				rx_bytes, tx_bytes = (data[0], data[8])
				return (int(rx_bytes), int(tx_bytes))
		raise Exception('VPNMetricService::_get_network_bytes: Network interface not found: ' + interface)

	def _collect_global_metrics(self, interval_name):
		"""Collects the global metrics from all of the service nodes, should be run from async job"""
		self._assert_interval_supported(interval_name, exclude=["hourly"])
		global_metrics = {}
		scalar_params = ['bytes_in', 'bytes_out']

		for ip, mn in self.mnsync_service.get_masternode_list(status_filter='ACTIVE').items():
			self.logger.debug('Collecting global metrics from node ' + ip)
			
			response = self.mn_gateway.webapi_query(ip) 

			if response.error:
				self.logger.warning('Failed to collect VPN metrics from the node: ' + ip + ': ' + str(response.error))
				continue

			for param in scalar_params:
				try:
					value = response.result['services']['VPN']['metrics'][interval_name]['bytes_in']

				except Exception as e:
					self.logger.warning('Failed to parse VPN metrics info from node: ' + ip + ': ' + str(e))
					continue

				if param not in global_metrics:
					global_metrics[param] = value
				else:
					global_metrics[param] += value

		return global_metrics

	def _assert_interval_supported(self, interval_name, exclude = None):
		if not interval_name in self.intervals or exclude and interval_name == exclude:
			raise Exception('VPNMetricService::update_recent_metrics: Unsupported interval ' + interval_name)

