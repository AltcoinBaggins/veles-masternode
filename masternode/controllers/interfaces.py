#!/usr/bin/env python
import asyncio, sys, json, time
from aiohttp import web
from abc import ABCMeta, abstractmethod
from masternode import version 		# local modules

class AbstractController(object, metaclass=ABCMeta):
	headers_common = {"Server": "lighttpd/1.4.45"}
	headers_json = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
	headers_html = {"Content-Type": "text/html"}

	## Required abstract methods
	@abstractmethod
	@asyncio.coroutine
	def handle(self, request):
		""" Accepts web.Request and should return web.Response object """
		pass

	@abstractmethod
	def set_routes(self, router):
		""" Accepts aiohttp.Router and defines routes used by controller """
		pass

	## Common controller functionality implementation
	def __init__(self, config, logger):
		self.config = config
		self.logger = logger
		self.init_headers()

	def init_headers(self):
		# Add own Masternode IP to the header, for use with proxies etc.
		self.headers_common.update({
			"X-Veles-Masternode-Ip": self.config['masternode'].get('server_addr'),
			"X-Veles-Api-Version": version.api_version
			})

	def response(self, data, headers=None, extra_headers={}):
		if headers:
			return web.Response(
				text=data,
				headers=self.add_signature_headers({**self.headers_common, **headers}, data, cb='relaxed')
				)
		else:
			return self.json_response({
				'status': 'success' if data else 'error',
				'result': data
				}, extra_headers=extra_headers)


	def error_response(self, message, code=-8673, extra_headers={}):
		return self.json_response({
			'status': 'error',
			'error': {'message': str(message), 'code': code},
			'result': None
			}, extra_headers=extra_headers)

	def html_response(self, text, extra_headers={}):
		return web.Response(text=text, headers=self.add_html_headers(extra_headers, text))

	def json_response(self, data, extra_headers={}):
		text = json.dumps(data, sort_keys = True, indent = 4)
		return web.Response(text=text, headers=self.add_json_headers(extra_headers, text))

	def add_html_headers(self, extra_headers, body=None):
		return {**self.headers_common, **self.headers_html, **extra_headers}

	def add_json_headers(self, extra_headers, body=None):
		return {**self.headers_common, **self.headers_json, **extra_headers}


class AbstractSigningController(AbstractController, metaclass=ABCMeta):
	def __init__(self, config, logger, signing_service):
		self.signing_service = signing_service
		super().__init__(config, logger)

	def add_html_headers(self, extra_headers, body=None):
		if body:
			return self.add_signature_headers({**self.headers_common, **self.headers_html, **extra_headers}, body)
		else:
			return {**self.headers_common, **self.headers_html, **extra_headers}

	def add_json_headers(self, extra_headers, body=None):
		if body:
			return self.add_signature_headers({**self.headers_common, **self.headers_json, **extra_headers}, body, cb='json')
		else:
			return {**self.headers_common, **self.headers_json, **extra_headers}

	def add_signature_headers(self, headers, body, headers_format='Masternode-Ip:Api-Timestamp', ch='relaxed', cb='simple'):
		timestamp = int(time.time())
		headers.update({'X-Veles-Api-Timestamp': str(timestamp)})
		to_sign = headers_format.replace('X-Veles-', '').strip()
		err = ''

		for hdr_name, hdr_value in headers.items():
			to_sign = to_sign.replace(hdr_name.replace('X-Veles-', ''), hdr_value.strip())

		# Remove duplicate or trailing whitespaces according to the context (ch, cb)
		if ch == 'relaxed':
			to_sign = " ".join(to_sign.split())
		elif ch == 'simple':
			to_sign = to_sign.strip()

		if cb == 'relaxed':
			body = " ".join(body.split())
		elif cb == 'simple':
			body = body.strip()
		elif cb == 'json':		# re-encodes to json with sorted keys and no extra indent
			try:
				body = json.dumps(json.loads(body), sort_keys = True)
			except Exception as e:
				body = " ".join(body.split())	# use relaxed as fallback if cannot parse
				err = '; e=json/relaxed'

		return {
			**headers,
			'X-Veles-Api-Signature': "v=0.99; a=vls-ecdsa; mn=%s; c=%s/%s; t=%i; h=%s; b=%s; bh=%s" % (
				self.config['masternode'].get('server_addr'),
				ch,
				cb,
				timestamp,
				headers_format,
				self.signing_service.sign(to_sign),
				self.signing_service.sign(body)
				) + err
		}
