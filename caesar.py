# Copyright (c) 2013, Charles O. Goddard
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution. 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import socket
import shelve
import sys
import select

import requests

chunk_size = 5000

from common import target, symbols

def main():
	state = shelve.open('caesar.dat')

	state['radix'] = state.get('radix', 1)
	state['p'] = state.get('p', 0)
	state['min'] = state.get('min', 10000)
	state['min_text'] = state.get('min_text', 'butt')
	state['strays'] = state.get('strays', [])

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	s.bind(('0.0.0.0', 1013))
	s.listen(5)
	s.setblocking(False)

	client_sockets = []
	client_buf = {}
	client_chunk = {}

	try:
		while True:
			(r,w,e) = select.select([s], [], [], 0)
			if r:
				conn, addr = s.accept()
				client_sockets.append(conn)
				client_buf[conn] = b''
				if state['strays']:
					client_chunk[conn] = state['strays'][0]
					state['strays'] = state['strays'][1:]
				else:
					client_chunk[conn] = (state['radix'], state['p'], min(state['p'] + chunk_size, pow(len(symbols), state['radix'])))
				#print('assigning', client_chunk[conn], 'to', addr)
				conn.sendall(('%d,%d,%d\n' % client_chunk[conn]).encode())

				state['p'] = state['p'] + chunk_size
				if state['p'] > pow(len(symbols), state['radix']):
					state['radix'] = state['radix'] + 1
					state['p'] = 0

			if not client_sockets:
				continue

			(read,write,dead) = select.select(client_sockets,client_sockets,client_sockets, 0)
			for client in read:
				new = client.recv(4096)
				if not new:
					dead.append(client)
					continue
				buf = client_buf[client]
				buf = buf + new
				client_buf[client] = buf
				if '\n' in buf.decode():
					try:
						res = buf.decode().rstrip('\n')
						(dist, text) = res.split(',')
						dist = int(dist)
						if dist < state['min']:
							state['min'] = dist
							state['min_text'] = text
							print('!! NEW MINIMUM: %d (%s)' % (dist, text))
							requests.post("http://almamater.xkcd.com/?edu=olin.edu", {'hashable': text})
						state['res_%r'%(client_chunk[client],)] = (dist,text)
					except Exception as e:
						print(e)
						dead.append(client)
					else:
						client.close()
						del client_chunk[client]
						del client_buf[client]
						client_sockets.remove(client)

			for client in dead:
				print(client.getsockname(), 'died, orphaned', client_chunk[client])
				state['strays'] = state['strays'] + [client_chunk[client]]
				del client_chunk[client]
				del client_buf[client]
				client_sockets.remove(client)



	except KeyboardInterrupt:
		return 1

	return 0


if __name__=='__main__':
	sys.exit(main())