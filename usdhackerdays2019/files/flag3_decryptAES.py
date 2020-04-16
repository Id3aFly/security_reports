#!/usr/bin/env python3
from itertools import cycle
import os

# xors the two bytearrays byte1 and byte 2 and returns the result as bytearray
def xor_bytes(byte1, byte2):
	# cycle is to to repeat byte2 that it has the same length as byte1
	return bytearray(a ^ b for a, b in zip(byte1, cycle(byte2)))

with  open(".secret.pdf", "rb") as realpdf:
	# .secret.pdf contains the correct pdf header, from which the first 16 bytes are read
	pdfheader = bytearray(realpdf.read(16))

	with open("token.pdf.enc", "rb") as encryptedpdf:
		# open and read all bytes from the encrypted pdf "token.pdf.enc" to  a bytearray
		ciphertext = bytearray(encryptedpdf.read())

		# determine the constant roundkey by xoring the first bytes of the ciphertext with the pdfheader (the correct plaintext)
		roundkey = xor_bytes(ciphertext[:16], pdfheader)

		#decrypt the ciphertext, by xoring each block of 16 bytes with the constant roundkey
		solution = xor_bytes(ciphertext, roundkey)
		# save the decrypted bytes to token.pdf
		with open("token.pdf", 'wb') as d:
			d.write(solution)