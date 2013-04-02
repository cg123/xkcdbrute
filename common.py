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

target = '5b4da95f5fa08280fc9879df44f418c8f9f12ba424b7757de02bbdfbae0d4c4fdf9317c80cc5fe04c6429073466cf29706b8c25999ddd2f6540d4475cc977b87f4757be023f19b8f4035d7722886b78869826de916a79cf9c94cc79cd4347d24b567aa3e2390a573a373a48a5e676640c79cc70197e1c5e7f902fb53ca1858b6'
symbols = '0123456789+abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

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

def plaintext_score(pt):
	hash_ = skein.skein1024(pt.encode(), digest_bits=1024).hexdigest()
	return hamming_distance(hash_, target)