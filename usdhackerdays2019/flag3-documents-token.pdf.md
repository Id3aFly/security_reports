
## 3. ~/Documents/token.pdf.enc & ~/Documents/encrypt-pdf.py

When looking into the Documents folder we have two files. The .enc file is just recognized as "data". Even strings, zip or binwalk don't show helpful information.
```console
id3ar00t@kali:~/usdhackerday2019/Documents# file token.pdf.enc 
token.pdf.enc: data
```

However the py file seems to be a regular python file.
```console
id3ar00t@kali:~/usdhackerday2019/Documents# file encrypt-pdf.py 
encrypt-pdf.py: Python script, ASCII text executable
```
The content of the python file:
```python
import os, sys
from Crypto.Cipher import AES

fn = sys.argv[1]
data = open(fn, 'rb').read()

secret = os.urandom(16)
crypto = AES.new(os.urandom(32), AES.MODE_CTR, counter=lambda: secret)

encrypted = crypto.encrypt(data)

open(fn+'.enc','wb').write(encrypted)
```
The file takes one argument, which has to be the path to a valid file, and reads the content of the file.  
As second step is the generation of a random value of 16 bytes, which is saved as `secret`.  
Then a new AES encrytion is initialized and saved to `crypto`. The input data is now encrypted with AES, through the settings provided in crypto and saved to a file, named like the input file followed by a '.enc'.  
This could mean that token.pdf.enc is the encrypted version of a token.pdf, in which the token is saved. But how can we decrypt AES without knowing the random secret and the counter? Luckily there is a weekness in this implementation.

### Finding the implementation vulnerability

AES is a symmetric block chiffre, which has block size of 16 Byte. For the encryption a random 32-byte master key is used. Additionally AES uses MODE_CTR, the Counter-Mode, which works as followed:    
AES works with rounds, where each round is responsible to encrypt 16 bytes. At first, the secret master key and the counter-variable are the input for the __block cipher encryption__. This results in a 16-byte round key, depending on this two variables. Now, the first 16 bytes of the __plaintext__ data, that shall be encrypted, are xored with the round key. Thus, we got the __ciphertext__ for the first 16 bytes of the input data.  
In the second round, we use the master key again and the counter-variable to generate the next round key through the block __cipher encryption__. This round key is xored with the next 16-bytes of the plain text input, and so on.
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/CTR_encryption_2.svg/601px-CTR_encryption_2.svg.png">  

[Image from Wikipedia](https://de.wikipedia.org/wiki/Counter_Mode)  

Now,  let's have a look at the counter variable. It has to be known for encryption and decryption. That means it has to be provided to the decryptor, or could somehow be derived (from the master key) or is a predefined method (like counting: 0,1,2, ... and increasing the value of the counter each round). What it shouldn't happen is, that the counter is a constant.  
And exactly this is happening here, since counter is a lambda method, always returning `secret`. Through using two constant parameters as input for the __block cipher encryption__ the resulting round key will always be the same. That is a problem, since once we have found the round key, we can use it for all blocks for decryption.
 
|  | secure (varying counter) | insecure (constant counter) |
|-------------|----------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| Encryption | plaintext1 XOR roundkey1 = ciphertext1<br>plaintext2 XOR roundkey2 = ciphertext2<br>plaintext3 XOR roundkey3 = ciphertext3 | plaintext1 XOR __roundkey__ = ciphertext1<br>plaintext2 XOR __roundkey__ = ciphertext2<br>plaintext3 XOR __roundkey__ = ciphertext3 |
| Decryption: | ciphertext1 XOR roundkey1 = plaintext1<br>ciphertext2 XOR roundkey2 = plaintext2<br>ciphertext3 XOR roundkey3 = plaintext3 | ciphertext1 XOR __roundkey__ = plaintext1<br>ciphertext2 XOR __roundkey__ = plaintext2<br>ciphertext3 XOR __roundkey__ = plaintext3 |

As seen in the table, it is sufficient to find the roundkey once, and xor all other 16-byte blocks of ciphertext with it, to receive the plaintext.

### Get the constant roundkey
Let's look at a single encryption scheme:  
`ciphertext1 = plaintext1 XOR roundkey` (\*1)  
What we know so far, is the ciphertext (which is saved in the encrypted file we have). If we just knew the 16 bytes of the plaintext1, we could xor the ciphertext1 with the plaintext1. This would result in the roundkey.  
`ciphertext1 XOR plaintext1 =*1= (plaintext1 XOR roundkey) XOR plaintext1 = roundkey`

The good thing is that we know the first 16 bytes, of the plaintext. The original file seems to be a pdf and all pdf (of the same version) share the same header (which is e.g. used by file to determine the filetype). At this [page](https://resources.infosecinstitute.com/pdf-file-format-basic-structure/) Dejan Lukan describes the layout of a pdf file.
If we assume, that the encrypted pdf has the same version like the other pdf (.secret.pdf), we just can extract the header from .secret.pdf and use it as our plaintext1. This is done with [a python script](files/flag3_decryptAES.py):

```python
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
```
The script extracts the bytes of the roundkey (`40 9a bd 77 42 49 f0 df 87 27 99 bf c7 47 ad 7d`) and saves a file called token.pdf. When opening this file, we see the third flag: __usd{2897e41d02805d36be78abbb0bc0311a}__

The challenge scheme was already part of a [CTF in 2017](https://ctftime.org/writeup/7199). Instead of using the python script, one could also use the tool [OTP PWN](https://github.com/derbenoo/otp_pwn) to get the round key.

As this flag might have been challenging to you, let's continue with flag 4: [a simple password cracking challenge](flag4-sloth.md)
