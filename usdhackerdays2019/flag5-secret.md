## 5 .secret.pdf
At first, I made sure, that .secret.pdf is a real pdf:
```console
id3ar00t@kali:~# file .secret.pdf
.secret.pdf: PDF document, version 1.5
```

In the next step I tried to open the pdf with my pdfviewer, but it was encrypted. 
```console
atril .secret.pdf
```
So let's crack the pdf. There are two methods I'm presenting you. The first is with the simple commandline tool pdfcrack, and the second makes use of hashcat, which is a more advanced tool.

### a) simple option with pdfcrack
For simple dictionary attacks I rely on pdfcrack.
> install: apt install pdfcrack.  

To have a set of wordlists (and other lists with usernames, passwords, ...) I usually refer to the tool [SecLists](https://github.com/danielmiessler/SecLists), which is installed at `/usr/share/seclists/`
> apt install seclists  

Now, we start pdfcrack with a few parameters:
> parameter f: to define the encrypted pdf  
> parameter w: specify the wordlist
```console
id3ar00t@kali:~# pdfcrack -f .secret.pdf -w /usr/share/seclists/Passwords/Leaked-Databases/rockyou.txt
PDF version 1.5
Security Handler: Standard
V: 2
R: 3
P: -3376
Length: 128
Encrypted Metadata: True
FileID: 2b5fe671d087cf1170618521dee75587
U: d09bcf769165fd701c87108e91fdbe5c00000000000000000000000000000000
O: f93207111951f181151cc2cc45c3c60bbe7bd61adb1e63693310acda4ca0d67b
found user-password: 'Hello123'
```

And we receive the password, with which we can open the pdf and get flag.
__usd{9f5f659b1281fdca73b1e35004241847}__

### b) advanced cracking with hashcat
hashcat is an advanced hashcracker and supports gpu cracking, as well as a lot of modification rules.
> install: apt install hashcat  

To convert the encrypted pdf to a "readable" format, we need to use [pdf2john.pl](https://github.com/magnumripper/JohnTheRipper/blob/bleeding-jumbo/run/pdf2john.pl). John the Ripper is another advanced hashcracker. 
The file also comes with an install of John the Ripper (`/usr/share/john/pdf2john.pl`).  
> install: apt install john

As a next step, we extract the hash of our encrypted pdf:
```console
id3ar00t@kali:~# /usr/share/john/pdf2john.pl .secret.pdf 
.secret.pdf:$pdf$2*3*128*-3376*1*16*2b5fe671d087cf1170618521dee75587*32*d09bcf769165fd701c87108e91fdbe5c00000000000000000000000000000000*32*f93207111951f181151cc2cc45c3c60bbe7bd61adb1e63693310acda4ca0d67b
```
and save everything beginning with "$pdf$ ..." to a file. I called mine secretpdfhash.
Now we can use hashcat:
> parameter m: defines the hashtype to be cracked  
> parameter a: defines the attack mode which is used for cracking. 0 means wordlist attack. The path to the wordlist follows directly.  
> parameter: the last parameter is our hash that needs to be cracked.
```console
hashcat -m 10500 -a 0 /usr/share/seclists/Passwords/Leaked-Databases/rockyou.txt secretpdfhash
```
this results in the same password 'Hello123'.

Now, that we have solved all flags, which could be found in the home directory, let's get the last flag: [flag6 - another simpler reversing task](flag6-thide.md)
