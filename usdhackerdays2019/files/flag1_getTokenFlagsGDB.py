#!/usr/bin/env python3
import subprocess
import os

# base of the gdb batch command. Every command following -ex is executed in the provided order.
command = "gdb -batch -ex 'file ./token'" 

# Adds multiple batch commands, to dissassemble the check_i methods in the correct order from 0-295
for i in range(0,296):
        command+=" -ex 'disassemble check_{}'".format(i) 

# execute the gdb batch command, and save the output
output = os.popen(command).read() 
solution = ""  # storing the final solution
binstring = "" # storing the solution in binary form

# splits the output by \n and checks if sete, setne or shr is included and sets the correct bit, which is encoded by the given command
for line in output.split("\n"): 
        if 'sete' in line:
                binstring+="0"
        elif 'setne' in line:
                binstring+="1"
        elif 'shr' in line:
                binstring+="0"

# splits the binary string into bytes
chars = [binstring[i:i+8] for i in range(0,len(binstring), 8)]

# reverses the bits of byte, since the current layout is from [LSB-MSB], converts the bits to a char and joins them to the final solution.
solution = ''.join(chr(int(elem[::-1],2)) for elem in chars)
print(solution)
