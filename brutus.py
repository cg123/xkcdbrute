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

from common import target, symbols

# Controller address
host_addr = 'beef.olin.edu'
host_port = 1013

# Precalculate hamming distances of hex digits
hd_digits = {}
for lh in '0123456789abcdef':
	for rh in '0123456789abcdef':
		xor = int(lh,16) ^ int(rh, 16)
		ct = 0
		while xor > 0:
			ct = ct + 1
			xor = xor // 2
		hd_digits[lh,rh] = ct

def hamming_distance(lh, rh):
	'''
	Return the binary hamming distance between two hex strings.
	'''
	ll, lr = len(lh), len(rh)
	if ll < lr:
		lh = '0'*(lr-ll) + lh
	elif lr < ll:
		rh = '0'*(ll-lr) + rh
	return sum(hd_digits[x,y] for (x, y) in zip(lh, rh))

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
			except socket.error as e:
				print('socket.error:', e)
				time.sleep(5)
				continue
			assignment = server.recv(4096)
			while not '\n' in assignment.decode():
				assignment = assignment + server.recv(4096)
			(radix, minp, maxp) = assignment.decode().rstrip('\n').split(',')
			(text, score) = closest_in_set(plaintext_range(int(radix), int(minp), int(maxp)))
			print (self.number, text, score)
			server.send(('%d,%s\n' % (score, text)).encode())

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
	sys.exit(main())
