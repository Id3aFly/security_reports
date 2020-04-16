## 1. ~/bin/token

### Analyzing the disassembly 
When analyzing token, `file` shows that token is an executable, which is not stripped. This might be an indicator for a reversing challenge.  
```console
id3ar00t@kali:~/usdhackerday2019/bin# file token
token: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 2.6.32, BuildID[sha1]=b377a714ebf675761e953a59bae55ccd38f0d03c, not stripped
```

When running token (you might have to make it executable with `chmod +x token`) it show that a 37 char argument is needed.  
```console
id3ar00t@kali:~/usdhackerday2019/bin# ./token
usage: ./token <37 character key>
```

Providing an arbitrary argument of this length leads to no output at all (except you enter the correct key, which we will see later)
```console
id3ar00t@kali:~/usdhackerday2019/bin# ./token AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
```

So lets start debugging, by opening this file with gdb and disassembling the main method. I won't go through all debugging steps, but I'm going to explain you the most important code parts. You can look at them in a [partial disassembly with gdb](files/flag1_token_disass.txt) or within my [ghidra project](files/flag1_token_ghidra.zip).

> install: apt install gdb
```console
gdb token
gef➤  disass main
```
At first, we see the typical prologue.  
```assembly
Dump of assembler code for function main:  
   0x0000555555554740 <+0>:	push   rbp
=> 0x0000555555554741 <+1>:	mov    rbp,rsp
   0x0000555555554744 <+4>:	sub    rsp,0x10
   ```
   In the next two lines the number of arguments (edi) is saved to [rbp-0x4] and the program path (rsi) to [rbp-0x10]. When starting a program there is always one argument, which is the path of the executable (rsi).  
   As a next step the number of arguments is compared with 0x2.  If there are not exactly 2 arguments, the code will jump into the error routine (main+46) which will print out `usage: ./token <37 character key>`. 
```assembly
   0x0000555555554748 <+8>:	mov    DWORD PTR [rbp-0x4],edi
   0x000055555555474b <+11>:	mov    QWORD PTR [rbp-0x10],rsi
   0x000055555555474f <+15>:	cmp    DWORD PTR [rbp-0x4],0x2
   0x0000555555554753 <+19>:	jne    0x55555555476e <main+46>
   ```
   If there are the required 2 arguments, the address of the program path is loaded, which is the first argument, and add 0x8, to get the address of the second argument. Afterwards this second argument (our input) is loaded to rdi and the length of our input is computed, which will be returned in rax.  
   ```assembly
   0x0000555555554755 <+21>:	mov    rax,QWORD PTR [rbp-0x10]
   0x0000555555554759 <+25>:	add    rax,0x8
   0x000055555555475d <+29>:	mov    rax,QWORD PTR [rax]
   0x0000555555554760 <+32>:	mov    rdi,rax
   0x0000555555554763 <+35>:	call   0x5555555545e0 <strlen@plt>
   ```
   Now, the length of the input is compared with 0x25 (37 in dec) and the jump is taken only, if our input has the length of 37. Otherwise, the next line (main+46) is executed, where the error handling starts.  
   ```assembly
   0x0000555555554768 <+40>:	cmp    rax,0x25
   0x000055555555476c <+44>:	je     0x555555554790 <main+80>
   ```
   The next lines are the error handling: It loads the program path to rsi and a formatstring from [rip+0x5799], which is the error message, to rdi. Then it uses printf to insert the program path in the error message and prints it to the screen.  
   Then it sets eax to 0x1 and jumps to (main+138) to leave the main method.  
   ```assembly
   0x000055555555476e <+46>:	mov    rax,QWORD PTR [rbp-0x10]
   0x0000555555554772 <+50>:	mov    rax,QWORD PTR [rax]
   0x0000555555554775 <+53>:	mov    rsi,rax
   0x0000555555554778 <+56>:	lea    rdi,[rip+0x5799]        # 0x555555559f18
   0x000055555555477f <+63>:	mov    eax,0x0
   0x0000555555554784 <+68>:	call   0x5555555545f0 <printf@plt>
   0x0000555555554789 <+73>:	mov    eax,0x1
   0x000055555555478e <+78>:	jmp    0x5555555547ca <main+138>
   ```
   Now, we reach the interesting part of the file, to which we jump from (main+44) on a 37 chars input. At first, the second parameter (our argument) ([rbp-0x10]+0x8) is loaded to rdi. Then a method check_0 is called with rdi as parameter. What happens in check_0 and all recursive called functions is described later. For the sake of clarity I am going to finish the description of the main method at first.  
   ```assembly
   0x0000555555554790 <+80>:	mov    rax,QWORD PTR [rbp-0x10]
   0x0000555555554794 <+84>:	add    rax,0x8
   0x0000555555554798 <+88>:	mov    rax,QWORD PTR [rax]
   0x000055555555479b <+91>:	mov    rdi,rax
   0x000055555555479e <+94>:	call   0x5555555561f6 <check_0>
   ```
   rax, i.e. al (which is the lowest byte of rax) contains the result of check_0. Test does a bitwise AND of al and al, which is an effective test, if al is 0x0. Test sets the ZF (among others), if al equals zero. Now, we look at the two different cases:  
   1. al is not 0x0: test doesn't set the ZF. Therefore, JE does not jump (and does not skip the third line). In this third line (main+103) the byte success, which is the address [rip+0x209893] points to, is set to 0x1. Next, this success-byte (which is also referenced by [rip+0x20988c]) is moved to eax, with zero extend. This means, we have 0x1 in eax as well. Now, there is a second check if al (the lowest byte in eax) is 0x0. But we know, this is 0x1. Therefore, the ZF flag is not set, and the following jump is not taken, which leads us to (main+121). This line loads the string "Congratulations. This key is valid!" which is subsequently printed to the screen by puts in line (main+128). Then the method is left.  
   2. al is 0x0: test now sets the ZF and JE jumps, such that the third line (main+103) is skipped. That means, we don't change the value of the success byte, which is 0x0 per default. With line 4 we move this value from the success-byte to eax (with zero extend), having 0x0 in eax. The following test on al results in a set of the ZF flag again, as al is 0x0. That means, we follow the jump in main+119 (not printing the success message) and leaving the main method.  
   
   => Summarized we know, that the success message is printed if al (which is returned by check_0) is not 0x0.  
   ```assembly
   0x00005555555547a3 <+99>:	test   al,al
   0x00005555555547a5 <+101>:	je     0x5555555547ae <main+110>
   0x00005555555547a7 <+103>:	mov    BYTE PTR [rip+0x209893],0x1        # 0x55555575e041 <success>
   0x00005555555547ae <+110>:	movzx  eax,BYTE PTR [rip+0x20988c]        # 0x55555575e041 <success>
   0x00005555555547b5 <+117>:	test   al,al
   0x00005555555547b7 <+119>:	je     0x5555555547c5 <main+133>
   0x00005555555547b9 <+121>:	lea    rdi,[rip+0x5778]        # 0x555555559f38
   0x00005555555547c0 <+128>:	call   0x5555555545d0 <puts@plt>
   0x00005555555547c5 <+133>:	mov    eax,0x0
   0x00005555555547ca <+138>:	leave  
   0x00005555555547cb <+139>:	ret    
End of assembler dump.  
```

### Following the recursive calls
Lets look into check_0:  

At first, we start with the prologue again.  
   ```assembly
gef➤  disass check_0
Dump of assembler code for function check_0:  
   0x00005555555561f6 <+0>:	push   rbp
   0x00005555555561f7 <+1>:	mov    rbp,rsp
   0x00005555555561fa <+4>:	sub    rsp,0x20
```
   Now, the parameter, which is the starting address of our input string, is loaded from rdi to rax. In check_0+16 this adress is dereferenced, such that we get the input string and take the first byte of it. This byte is saved to eax through a zero extend. The next line (check_0+19) which is a signextend of this byte (in al) we just copied to eax, is a bit useless. I guess it was added for obfuscation. Since the ASCII-characters (which our flag is made of) make only use of seven bits of a byte, the MSB (most significant bit) shouldn't be set at all.  
```assembly
   0x00005555555561fe <+8>:	mov    QWORD PTR [rbp-0x18],rdi
   0x0000555555556202 <+12>:	mov    rax,QWORD PTR [rbp-0x18]
   0x0000555555556206 <+16>:	movzx  eax,BYTE PTR [rax]
   0x0000555555556209 <+19>:	movsx  eax,al
```

   With `and eax, 0x1` the LSB (least significant bit) of eax is masked, that means we keep the LSB of EAX unmodified, while we set everything else to 0.  
```assembly
   0x000055555555620c <+22>:	and    eax,0x1
```
   At this point we have a case discrimination, which is crucial for understanding and solving the challenge.  
   1. If the LSB is 0, the masking results in eax=0x0. (check_0+25) checks if eax is 0x0, which is the case and therefore, sets the ZF. Setne (set if not equal; set if not zero) sets the given byte address to 1, if the zero flag is not set. Otherwise it does nothing. Because the ZF is set, setne does nothing, and keeps al as it is (al=0x0).  
   2. If the LSB is 1, the masking results in eax=0x1. (check_0+25) checks if eax is 0x0, which is NOT the case and therefore, clears the ZF. Because ZF is not set, setne (set if not equal; set if not zero) sets al to 0x1.  
```assembly
   0x000055555555620f <+25>:	test   eax,eax
   0x0000555555556211 <+27>:	setne  al
```
   Now,  the result of setne is stored to a local variable.  
```assembly
   0x0000555555556214 <+30>:	mov    BYTE PTR [rbp-0x1],al
```
   After this, the address of our input string is loaded to rdi, and check_1 is called. If we look into check_1, we see, that it recursively calls check_2, ... until check_295. I'm going to explain this later, but let's assume we return from check_1 and the result of check_1 is stored in rax.  
```assembly
   0x0000555555556217 <+33>:	mov    rax,QWORD PTR [rbp-0x18]
   0x000055555555621b <+37>:	mov    rdi,rax
   0x000055555555621e <+40>:	call   0x555555554e3c <check_1>
```
   This part of code is similar to what we've already seen in the main method. At first, we test if the result in al is 0x0.  
   1. If al=0x0 , we jump to (check_0+62) and set eax to 0x0. (check_0+67) masks this LSB of eax, which is quite useless, because it is either 0x0 or 0x1 (as we will see soon). Then we are leaving check_0 and return to main with eax=0x0.  
   2. If the result of check_1 is al=0x1, test will not set the ZF and je will not jump. Now, we compare the result, we received in (check_0+27) (before calling check_1) and saved it to the local variable [rbp-0x1], with 0x0. 
      1. If the result was 0: Then the programs jumps to check_0+62, sets eax to 0x0 and returns with eax=0x0 to main.  
      2. If the result was 1: Then the program skips the jump, sets eax=0x1, masks this LSF, and returns with eax=0x1 to main.  
```assembly
   0x0000555555556223 <+45>:	test   al,al
   0x0000555555556225 <+47>:	je     0x555555556234 <check_0+62>
   0x0000555555556227 <+49>:	cmp    BYTE PTR [rbp-0x1],0x0
   0x000055555555622b <+53>:	je     0x555555556234 <check_0+62>
   0x000055555555622d <+55>:	mov    eax,0x1
   0x0000555555556232 <+60>:	jmp    0x555555556239 <check_0+67>
   0x0000555555556234 <+62>:	mov    eax,0x0
   0x0000555555556239 <+67>:	and    eax,0x1
   0x000055555555623c <+70>:	leave  
   0x000055555555623d <+71>:	ret    
End of assembler dump.  
```

### Understanding the return values
Previously we have seen, that main prints the success method, if al(eax) is not 0x0. But check_0 sets al=0x0 in two cases:  
1. check_1 returned 0x0
2. The result of check_0 in line (check_0+27) was 0x0.  
  
That means, we have to make sure, that check_1 returns 0x1 and our line (check_0+27) returns 0x1.  
Let's take have a look into the __first case__:  
check_1 has the same structure as check_0. That means its result depends on the result of check_2 and its own check. This scheme is a recursive call and leads us until check_295. This is the last method, and this one does not depend on any other previous checks. It just returns the value of its own check.  
That means: The information which the callee returns to the calling method, is nothing but the condition that all previous checks returned 0x1. If you think of 0x1=True and 0x=False, it means, that all checks have had to be True so far, starting at the latest called method (check_295).  

In pseudocode this would look like:  
```
main:  
   if(check_0(input_string)):  
      print("success")
      
check_i:  
   return check_i+1(input_string) && check_bit_i(input_string)

check_295:  
   return check_bit_295(input_string)
```

But what is the check_bit_i? This is the __second case__ we want to look at.  
What I called check_bit_i is the check in each method check_i, if the iths bit of the input_string is correct.  
This method is slightly different for every i, but they have a common structure. Each method starts with loading the input_string and ends with the setting of al with the method setne (or sometimes sete).  
For check_0 the part I call check_bit_0 is the following, I already explained above:  
```assembly
   0x0000555555556202 <+12>:	mov    rax,QWORD PTR [rbp-0x18]
   0x0000555555556206 <+16>:	movzx  eax,BYTE PTR [rax]
   0x0000555555556209 <+19>:	movsx  eax,al
   0x000055555555620c <+22>:	and    eax,0x1
   0x000055555555620f <+25>:	test   eax,eax
   0x0000555555556211 <+27>:	setne  al
```
At first, the input_string is loaded to eax, then the bit, the method looks at, is masked, and then setne (or sete) determines if a 0- or 1-bit is correct. setne (or sete) changing al to 0x1 (True) oder 0x0 (False) is responsible for the return value of the check_bit_i method.  
But all check_bit_i methods differ slightly. Lets have a look at the according part of check_10:  
```assembly
   0x0000555555558876 <+12>:	mov    rax,QWORD PTR [rbp-0x18]
   0x000055555555887a <+16>:	add    rax,0x1                   #a) new: responsible for accessing the second byte
   0x000055555555887e <+20>:	movzx  eax,BYTE PTR [rax]
   0x0000555555558881 <+23>:	movsx  eax,al
   0x0000555555558884 <+26>:	and    eax,0x4                   #b) modified: responsible for masking the third bit
   0x0000555555558887 <+29>:	test   eax,eax
   0x0000555555558889 <+31>:	sete   al                        #c) modified: hardcoded routine for the password check
```
<ol type="a">
  <li>Accessing other input_argument bytes</li>
   The check_bit_i function loads always a BYTE PTR (e.g. check_0+16, check_10+20) and checks a specific bit in this byte. To access the correct byte, the address of the pointer to the input_string, which is stored in rax, has to be modified. Since check_0 looks at the first bit (start counting with 0), which is part of the first byte, we don't have to increase the pointer, since the pointer directs by default to the first byte.  
  When checking the 10th bit (which is the 3rd bit of the second byte of our input_argument) we have to modify the pointer, such that it directs to the second byte of the input argument. This is done with line (check_10+16), which increases the pointer in rax by 0x1.  
   
   
  <li>Accessing other bits of the current checked byte</li>
  Every byte consists of 8 bits which have to be checked against the ground truth. By using masking, the fokus is put at a specific bit by nulling out all other bits for the current check. Only the first seven bits are checked through masking. The 8th bit, is (maybe for obfuscation) checked by another routine, which I'm going to explain in c).  
  
  When checking the first bit of a byte (e.g. in check_0 or check_8, ...) the code masks with `and eax, 0x1`,  since 0x1=0x01=00000001.  
  When checking the third bit of a byte (e.g. in check_10 or check_18, ...) the coded masks with `and eax, 0x4`, since 0x4=0x04=00000100

  The masks are for the 1st-7th bit are: 0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40.  
  
  <li>Checking the current bit</li>
  The flag consists of 37 ASCII chars, which have to be checked. To make it not too simple, this is done by obfuscation, by comparing each bit on its own by 296 individual methods. Each one is responsible for checking a single bit.  
  If the check was successfull (the currently checked bit of a char corresponds with the ground truth), the check returns 0x1=True, otherwise 0x0=False.  
The 1st - 7th bit (the least significant bits) can be arbitrary as the ASCII codes are from 0x0 to 0x7F, while the 8th and most significant bit of the ASCII char, is always 0. Therefore, the first seven bits are checked in another way (with sete/setne) than the 8th bin (with not/shr).  

When any of the first seven bits is masked, all other bits are set to 0.  Let's assume the third bit is checked (for example in check_2, see code below). That means masking with 0x4 could lead to 00000000 (e.g. `and 0x4, 01011010`) or 00000100 (e.g. `and 0x4, 01010101`). The test method then checks if eax (the masked result) is 0 or not. That means the combination of the masking (`and`) and the comparison with 0 (`test`) checks exactly if the masked bit is 0 or not. If the third bit of our input_string (in this case) was 0, the whole byte in eax is zero and test will set the ZF flag. Otherwise, the ZF flag won't be set. The third line (which is uniquely hardcoded for every method) carries the information about the correct bit. setne will only result in al=0x1, if the ZF flag is not set, which requires the third bit to be 1. sete (set if equal/set if zero) will only result in al=0x1, if the ZF flag was set, which requires the third bit to be 0. That means sete/setne indicate the value of the ground truth bit.  

```assembly
gef➤  disass check_2
Dump of assembler code for function check_2:  
...  
   0x0000555555558624 <+22>:	and    eax,0x4
   0x0000555555558627 <+25>:	test   eax,eax
   0x0000555555558629 <+27>:	setne  al
...  
```

Checking the 8th bit (check_7, check_15, ...) is a special case. Since all ASCII characters (of which the flag consists) have at max the value 0x7F, we know the highest bit always has to be 0. This information would be enough, as we can set every 8th bit of our input_argument (position 7,15,...) to 0. 
If you are interested read further how the check is conducted:  
To check this 8th bit of every byte the following code for check_bit_i is used.  
  At first, the correct byte (maybe modified like below in (check_15+16) ) is loaded to eax. Then the whole byte is bitwise inverted with not. If an ASCII value was entered the MSB was at first, 0, and is 1 now. By using shr we shift all bits of al 7 places to the right and fill from left with zeros. (e.g. |1xxxxxxx| -> |00000001|xxxxxxx). Through this operation the value of al should be 0x1 as well.  
```assembly
 0x000055555555705a <+12>:	mov    rax,QWORD PTR [rbp-0x18]
   0x000055555555705e <+16>:	add    rax,0x1
   0x0000555555557062 <+20>:	movzx  eax,BYTE PTR [rax]
   0x0000555555557065 <+23>:	not    eax
   0x0000555555557067 <+25>:	shr    al,0x7
``` 
</ol>

 ### Bringing everything together
 We know that 37 ASCII-chars are required as input. Each bit of the 37\*8bit = 296 bit is verified by a check_i method, which has the ground truth encoded. A positive result is only displayed, if each method returns 0x1(=True). The MSB of every byte has to be 0. Every other bit is individually verified by sete/setne, where sete returns 0x1, when the ZF is set requiring the input bit to be 0, and setne returns 0x1, when the ZF is not set, requiring the input bit to be 1.  
 
### Solving the problem
Instead of debugging through all 296 check_i methods, I used python to get the correct flag: Apart from the following [solution with gdb](files/flag1_getTokenFlagsGDB.py), there is a faster, optimized [solution with objdump](files/flag1_getTokenFlagsOBJD.py).  
```python
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
``` 
This leads to the flag:  
__usd{6da01c44955bc76da53dfa6dbcb4444f}__

We found solved the first and hardest challenge! Read on with [flag2](flag2-desktop-usb-img.md), the simplest challenge.
