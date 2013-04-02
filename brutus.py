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

import skein

import socket
import sys
import time
import re
import multiprocessing
import binascii

from common import target, symbols

# Controller address
host_addr = 'beef.olin.edu'
host_port = 1013

bytesDiff = dict()
for i in range(256):
	high = 0;
	for j in range(8):
		high += (i >> j) & 1
	bytesDiff[i] = high

def hamming_distance(lh, rh):
	'''
	Return the binary hamming distance between two hex strings.
	'''
	if(len(lh) % 2 != 0):
		a = [0]
		a.extend(lh)
		lh = a
	if (len(rh) % 2 != 0):
		a = [0]
		a.extend(rh)
		rh = a

	lhb = binascii.unhexlify(lh)
	rhb = binascii.unhexlify(rh)

	if len(lhb)<len(rhb):
		a = [0] * (len(rhb)-len(lhb))
		a.extend(lhb)
		lhb = a
	if len(rhb)<len(lhb):
		a = [0]*(len(lhb)-len(rhb))
		a.extend(rhb)
		rhb = a
	return sum((bytesDiff[x ^ y]) for (x, y) in zip(lhb, rhb))

def nth_plaintext(radix, n):
	syms = []
	for i in range(radix):
		syms.append(symbols[int(n % len(symbols))])
		n = n // len(symbols)
	return ''.join(syms)

def plaintext_range(radix, min_p, max_p):
	for p in range(min_p, max_p):
		yield nth_plaintext(radix, p)

def plaintext_score(pt):
	hash_ = skein.skein1024(pt.encode(), digest_bits=1024).hexdigest()
	return hamming_distance(hash_, target)

def closest_in_set(plaintexts):
	min_score = 1000000
	winner = 'butt'
	for pt in plaintexts:
		score = plaintext_score(pt)
		if score < min_score:
			min_score = score
			winner = pt
	return (winner, min_score)


class Brutus(multiprocessing.Process):
	def run(self):
		print('-- BRUTUS', self.number, '--')
		while True:
			try:
				server = socket.create_connection((host_addr, host_port), 5)
				assignment = server.recv(4096)
				while not '\n' in assignment.decode():
					assignment = assignment + server.recv(4096)
				(radix, minp, maxp) = assignment.decode().rstrip('\n').split(',')
				(text, score) = closest_in_set(plaintext_range(int(radix), int(minp), int(maxp)))
				print (self.number, text, score)
				server.send(('%d,%s\n' % (score, text)).encode())
			except socket.error as e:
				print('socket.error:', e)
				time.sleep(15)
			except KeyboardInterrupt:
				break
			except Exception as e:
				print('Unexpected error:', e)
				time.sleep(60)


def main():
	processes = []
	try:
		cpus = multiprocessing.cpu_count() + 1
	except NotImplementedError:
		cpus = 3
	for i in range(1, cpus + 1):
		proc = Brutus()
		proc.number = i
		proc.start()
		processes.append(proc)


if __name__=='__main__':
	multiprocessing.freeze_support()
	sys.exit(main())
