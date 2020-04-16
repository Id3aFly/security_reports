#!/usr/bin/env python3
import os
import re
import binascii

command = "objdump -S token"
output = os.popen(command).read()

pattern = r'<check_(\d+)>:.*?(set\w+|retq)'
matches = re.findall(pattern, output, re.S)
matches.sort(key = lambda x: int(x[0]))
text_result = zip(*matches)[1]

bin_result = map(lambda x:  "1" if x == "setne" else "0", text_result)
binstring = ''.join(bin_result)
chars = [binstring[i:i+8] for i in range(0,len(binstring), 8)]
solution = ''.join(chr(int(elem[::-1],2)) for elem in chars)
print(solution)

