
## 6. thide

In the user directory we were able to find 5 flags, so one flag is missing. To find this last flag I was looking through the whole image for files containing 'usd'.
```console
user@hdc:~$ find / -xdev -type f -exec grep -w 'usd' {} \; 2> /dev/null
```
find is used to iterate over all files, starting in the root directory /. -xdev keeps the search on the local filesystem not following other links, while -type f just looks for regular files and no symlinks, etc. Wih exec all files matching this pattern are sent to grep. The flag -w selects only such lines containing matches that are the beginning or end of a string.

This lead to multiple results, e.g. the USB_IMG.img we already discussed, a /usr/bin/thide and two other files, which seem not interesting. So I focussed on thide.

Since thide is placed in the /usr/bin folder it can be executed via command line. "user@hdc:~$ thide" gives us nothing but a waiting shell. It looks like it might be waiting for inputs, but nothing happens. Also simple parameters seem not to have any effect, as well as long parameters which may trigger a buffer overflow. That's why I scp-ed the file to my local system.
```console
scp user@hdc:/usr/bin/thide /local/path
```

file confirms the file as executable, and gives the hint "not stripped". That means there is still debugging information inside the executable.

```console
id3ar00t@kali:~/usdhackerday2019# file thide
thide: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2, for GNU/Linux 2.6.32, BuildID[sha1]=224455d46c856e49c8d75156465e2348a96874c2, not stripped
```

strings gives us further insights on contained functions and strings like
```console
id3ar00t@kali:~/usdhackerday2019# strings thide
[...]
MD5_Final
MD5_Init
MD5_Update
socket
htons
connect
inet_pton
send
Connect to server
Hello from client
 Socket creation error 
127.0.0.1
Invalid address/ Address not supported 
usd{
str2md5
[...]
```
Apart from methods referring to MD5, we also see some methods and strings regarding sockets and as well the beginning of our flag scheme 'usd{'. This looks like a debugging excercise, so let's start with gdb [(disassembly)](files/flag6_thide_disass_gdb.txt) and ghidra [(project files)](files/flag6_thide_ghidra.zip):

```console
gdb thide
b *main
run
```

With ni you can get to the next line of the current method, with si you can step into a method, with finish you can step out of a method.
In parallel I opened ghidra and loaded thide as well. Ghidra is quite powerfull and you are able to add comments or rename methods and variables. You can find my annotated ghidra project here.

For a short overview I give you the disassembly of gdb:
After the prologue the String "Connect to server" is loaded (+29) and used as input of the method str2md5 (+36). The result of this method, as supposed a md5 hash, is saved to [rbp-0x10] in (+41). This will be important for later.  
```assembly
gef➤  disass main
Dump of assembler code for function main:
   0x0000555555554beb <+0>:	push   rbp
   0x0000555555554bec <+1>:	mov    rbp,rsp
   0x0000555555554bef <+4>:	sub    rsp,0x460
   0x0000555555554bf6 <+11>:	mov    DWORD PTR [rbp-0x454],edi
   0x0000555555554bfc <+17>:	mov    QWORD PTR [rbp-0x460],rsi
   0x0000555555554c03 <+24>:	mov    esi,0x11
   0x0000555555554c08 <+29>:	lea    rdi,[rip+0x1fe]        # 0x555555554e0d  -> String "Connect to server"      
   0x0000555555554c0f <+36>:	call   0x555555554af0 <str2md5>                 -> Call method str2md5
   0x0000555555554c14 <+41>:	mov    QWORD PTR [rbp-0x10],rax                 -> "Save result in rbp-0x10"    
   ```
   In the next two lines, two variables are set. 0xa is the amount of seconds to wait and [rbp-0x14] stores the socket number later on.
   ```assembly
   0x0000555555554c18 <+45>:	mov    DWORD PTR [rbp-0x4],0xa                    
   0x0000555555554c1f <+52>:	mov    DWORD PTR [rbp-0x14],0x0
   ```
   As a next step the String "Hello from client" is loaded in +59, but nothing interesting is done with it.
   ```assembly
   0x0000555555554c26 <+59>:	lea    rax,[rip+0x1f2]        # 0x555555554e1f  -> String "Hello from client" 
   0x0000555555554c2d <+66>:	mov    QWORD PTR [rbp-0x20],rax
   ```
 This is followed by an annoying method in (+90) which may hinder debugging a bit. In place of using ni, I set a new breakpoint with b *main+93 and continued the programm execution until this line was reached with continue.
   ```assembly
   0x0000555555554c31 <+70>:	lea    rdx,[rbp-0x450]
   0x0000555555554c38 <+77>:	mov    eax,0x0
   0x0000555555554c3d <+82>:	mov    ecx,0x80
   0x0000555555554c42 <+87>:	mov    rdi,rdx
   0x0000555555554c45 <+90>:	rep stos QWORD PTR es:[rdi],rax                 -> "Annoying method" 
   ```
   The next lines of code, from (+93) until (+112), make the programm sleep for 10=0xa seconds. This variable was first set in (+45).
   ```assembly
   0x0000555555554c48 <+93>:	jmp    0x555555554c57 <main+108>
   0x0000555555554c4a <+95>:	mov    eax,DWORD PTR [rbp-0x4]
   0x0000555555554c4d <+98>:	mov    edi,eax
   0x0000555555554c4f <+100>:	call   0x555555554960 <sleep@plt>              -> Sleeps for a specific amount of thime    
   0x0000555555554c54 <+105>:	mov    DWORD PTR [rbp-0x4],eax
   0x0000555555554c57 <+108>:	cmp    DWORD PTR [rbp-0x4],0x0
   0x0000555555554c5b <+112>:	jne    0x555555554c4a <main+95>
   ```
   (+114) until (+134) executes the method socket(2,1,0), which returns a socket number, which is saved in [rbp-0x14].
   ```assembly
   0x0000555555554c5d <+114>:	mov    edx,0x0
   0x0000555555554c62 <+119>:	mov    esi,0x1
   0x0000555555554c67 <+124>:	mov    edi,0x2
   0x0000555555554c6c <+129>:	call   0x555555554980 <socket@plt>             -> "Creates a socket(2,1,0)"    
   0x0000555555554c71 <+134>:	mov    DWORD PTR [rbp-0x14],eax
   ```
   A possible error is handled within lines (+137) and (+155), which checks if the socket number is smaller zero and shows an error message, if necessary.
   ```assembly
   0x0000555555554c74 <+137>:	cmp    DWORD PTR [rbp-0x14],0x0
   0x0000555555554c78 <+141>:	jns    0x555555554c8b <main+160>
   0x0000555555554c7a <+143>:	lea    rdi,[rip+0x1b0]        # 0x555555554e31   
   0x0000555555554c81 <+150>:	call   0x5555555548f0 <puts@plt>
   0x0000555555554c86 <+155>:	jmp    0x555555554d7a <main+399>
   ```
(+160) until (+182) prepare a space of 4 words for the following placement of the target address.
   ```assembly
   0x0000555555554c8b <+160>:	lea    rax,[rbp-0x50]
   0x0000555555554c8f <+164>:	mov    edx,0x10
   0x0000555555554c94 <+169>:	mov    esi,0x30
   0x0000555555554c99 <+174>:	mov    rdi,rax
   0x0000555555554c9c <+177>:	call   0x5555555548c0 <memset@plt>                 
   0x0000555555554ca1 <+182>:	mov    WORD PTR [rbp-0x50],0x2
   ```
   (+188) is very important, as 0xf765 (63333 in dec) is the port address, the socket connects to. This hex value is converted to network byte order and saved to the according place within (+193) and (+198).
   ```assembly
   0x0000555555554ca7 <+188>:	mov    edi,0xf765                                   
   0x0000555555554cac <+193>:	call   0x555555554900 <htons@plt>               -> hton converts 0xf765 (= 63333 in dec) to network byte order
   0x0000555555554cb1 <+198>:	mov    WORD PTR [rbp-0x4e],ax
   ```
   The next lines from +202 up zo +230 convert the target Ip 127.0.0.1 to network byte order as well, and save it to the correct place.
   ```assembly
   0x0000555555554cb5 <+202>:	lea    rax,[rbp-0x50]
   0x0000555555554cb9 <+206>:	add    rax,0x4
   0x0000555555554cbd <+210>:	mov    rdx,rax
   0x0000555555554cc0 <+213>:	lea    rsi,[rip+0x183]        # 0x555555554e4a  -> String "127.0.0.1" 
   0x0000555555554cc7 <+220>:	mov    edi,0x2
   0x0000555555554ccc <+225>:	mov    eax,0x0
   0x0000555555554cd1 <+230>:	call   0x5555555548e0 <inet_pton@plt>           -> inet_pton converts the ip to the network byte order
   ```
   This is followed by error handling (+235) to (+246).
   ```assembly
   0x0000555555554cd6 <+235>:	test   eax,eax
   0x0000555555554cd8 <+237>:	jg     0x555555554ce6 <main+251>  
   0x0000555555554cda <+239>:	lea    rdi,[rip+0x177]        # 0x555555554e58
   0x0000555555554ce1 <+246>:	call   0x5555555548f0 <puts@plt>
   ```
   If no error succeeded so far,the lines (+251) to (+268) are responsible for connecting to the IP 127.0.0.1:63333.
   ```assembly
   0x0000555555554ce6 <+251>:	lea    rcx,[rbp-0x50]
   0x0000555555554cea <+255>:	mov    eax,DWORD PTR [rbp-0x14]
   0x0000555555554ced <+258>:	mov    edx,0x10
   0x0000555555554cf2 <+263>:	mov    rsi,rcx
   0x0000555555554cf5 <+266>:	mov    edi,eax
   0x0000555555554cf7 <+268>:	call   0x555555554970 <connect@plt>             -> Tries to connect to the given address 127.0.0.1:63333
   ```
   This is followed by error handling again.
   ```assembly
   0x0000555555554cfc <+273>:	test   eax,eax
   0x0000555555554cfe <+275>:	js     0x555555554d79 <main+398>
   ```
   Now,  we should be connected to the socket and can send strings to it. This is now done three times.
   (+277) - (+299), (+304 - (+333) and (+338)- (+360). 
What is done in each case is to load the socket number from [rbp-0x14] to eax , set the flags parameter (ecx) to 0, set the length of the buffer to edx, and place the buffer address in rsi.
The first time 'usd{' (4 Bytes) is send.
   ```assembly
   0x0000555555554d00 <+277>:	mov    eax,DWORD PTR [rbp-0x14]
   0x0000555555554d03 <+280>:	mov    ecx,0x0
   0x0000555555554d08 <+285>:	mov    edx,0x4
   0x0000555555554d0d <+290>:	lea    rsi,[rip+0x16d]        # 0x555555554e81  -> String "usd{" 
   0x0000555555554d14 <+297>:	mov    edi,eax
   0x0000555555554d16 <+299>:	call   0x555555554990 <send@plt>                -> Sends string
   ```
   The second time the programm sends the buffer in [rbp-0x10], which is the md5 that was saved in (+41).
   To determin the length of this buffer strlen is called at first.
   ```assembly
   0x0000555555554d1b <+304>:	mov    rax,QWORD PTR [rbp-0x10]
   0x0000555555554d1f <+308>:	mov    rdi,rax
   0x0000555555554d22 <+311>:	call   0x555555554930 <strlen@plt>
   0x0000555555554d27 <+316>:	mov    rdx,rax
   0x0000555555554d2a <+319>:	mov    rsi,QWORD PTR [rbp-0x10]                 -> Loads the md5 which was saved in +41
   0x0000555555554d2e <+323>:	mov    eax,DWORD PTR [rbp-0x14]
   0x0000555555554d31 <+326>:	mov    ecx,0x0
   0x0000555555554d36 <+331>:	mov    edi,eax
   0x0000555555554d38 <+333>:	call   0x555555554990 <send@plt>                -> Sends string
   ```
   In the end, the terminating } and a null byte (2 Bytes) are sent.
   ```assembly
   0x0000555555554d3d <+338>:	mov    eax,DWORD PTR [rbp-0x14]
   0x0000555555554d40 <+341>:	mov    ecx,0x0
   0x0000555555554d45 <+346>:	mov    edx,0x2
   0x0000555555554d4a <+351>:	lea    rsi,[rip+0x135]        # 0x555555554e86  -> String "}" 
   0x0000555555554d51 <+358>:	mov    edi,eax
   0x0000555555554d53 <+360>:	call   0x555555554990 <send@plt>                -> Sends string
   ```
   This lines are epilog, and restart the method, after any input was read.
   ```assembly
   0x0000555555554d58 <+365>:	lea    rcx,[rbp-0x450]
   0x0000555555554d5f <+372>:	mov    eax,DWORD PTR [rbp-0x14]
   0x0000555555554d62 <+375>:	mov    edx,0x400
   0x0000555555554d67 <+380>:	mov    rsi,rcx
   0x0000555555554d6a <+383>:	mov    edi,eax
   0x0000555555554d6c <+385>:	call   0x555555554910 <read@plt>
   0x0000555555554d71 <+390>:	mov    DWORD PTR [rbp-0x24],eax
   0x0000555555554d74 <+393>:	jmp    0x555555554c18 <main+45>
   0x0000555555554d79 <+398>:	nop
   0x0000555555554d7a <+399>:	jmp    0x555555554c18 <main+45>
End of assembler dump.
```


This means, if we debug until main+41 and take the md5 in rax, which result from str2md5, we know the flag. This is possible very easily and one has not to set up a serversocket, thide could connect to.
This leads us to the flag: __usd{2fd91fce1071390b3945c4abac9da836}__

To prove this result, we can easily set up a serversocket with netcat or python, which prints the incoming bytes to the shell, after we ran thide and waited for ~10s:


Netcat
```console
id3ar00t@kali:~/usdhackerday2019# nc -k -l 127.0.0.1 -p 63333
```

[Python script](files/flag6_python_socket.py) to start a socket server
```python
#!/usr/bin/env python3

import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 63333        # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(data.decode("utf-8"))
```

Congratulations, now we have solved all the challenges!
