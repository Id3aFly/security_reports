## 4. ~/Pictures/sloth.jpg

### Extracting the zip

When opening the sloth.jpg, you just see a picture of a sloth and there is nothing special about it.

Neither file results in anything special:
```console
id3ar00t@kali:~/usdhackerday2019/Pictures# file sloth.jpg 
sloth.jpg: JPEG image data, JFIF standard 1.01, resolution (DPI), density 72x72, segment length 16, progressive, precision 8, 3154x2250, components 3
```

nor does exif:
> install: apt install exif

```console
id3ar00t@kali:~/usdhackerday2019/Pictures# exif sloth.jpg 
Beschädigte Daten
Die gelieferten Daten entsprechen nicht der Spezifikation.
ExifLoader: Die übergebenen Daten scheinen keine EXIF-Daten zu enthalten.
```

In such a case I always try to look into the components of a file. Two very useful tools for this are 7zip and binwalk. In many cases you have to deal with compressed files and 7zip is in my opinion very robust and able to dectect nested files. When opening sloth.jpg with 7zip we already get an interesting result:
![Image description](https://github.com/Id3aFly/usdhackerdays2019/blob/master/images/sloth7zip.jpg)
Inside the sloth.jpg somehow is an token.txt file, but unpacking requires a password.
Even more information is available in the archive information, which tells us that there is an encrypted zip file. Additionally it lists the offset, the size of the zip and that there is even more data appended.  


![Image description](https://github.com/Id3aFly/usdhackerdays2019/blob/master/images/sloth7zip2.jpg)


To get more detailed information I use binwalk now. Binwalk parses the content of any file and tries to determine filetype specific headers and footers.  
> install: apt install binwalk  

Binwalk confirms that there is a jpeg file followed by a zip archive containing a file named token.txt. After the footer of the zip file there is another JPEG image (which turns out to be the the same picture as the first one).  

![Image description](https://github.com/Id3aFly/usdhackerdays2019/blob/master/images/slothBinwalk.jpg)

Usually you can use binwalk to autoextract the different contents by using `binwalk -e filename`, which fails in this context.
But we know the offset(501600) and the length(234) of the zip file in bytes, so we are able to extract it manually with dd:

> parameter if: input file  
> parameter of: output file  
> parameter bs: determines the  block size of a unit which is used for the skip and count parameter  
> parameter skip: amount of units to be skipped before the to be extracted bytes  
> parameter count: amount of units to be extracted  

```console
id3ar00t@kali:~/usdhackerday2019/Pictures# dd if=sloth.jpg of=encrypted.zip bs=1 skip=501600 count=234
```
The extracted result is the encrypted.zip file. 

### Crack the password of the zipfile

At first, it is necessary to get the hash of the password, which is used to protect the archive. We can make use of JohnTheRipper which provides the tool zip2john.
> install: apt install john

```console
id3ar00t@kali:~/usdhackerday2019/Pictures# zip2john encrypted.zip 
ver 1.0 efh 5455 efh 7875 encrypted.zip/token.txt PKZIP Encr: 2b chk, TS_chk, cmplen=50, decmplen=38, crc=978C3871
encrypted.zip/token.txt:$pkzip2$1*2*2*0*32*26*978c3871*0*43*0*32*978c*56f6*ca5a20c584c14a89f753015f8ba24d6cf4bcdfb614d6649175e5554e643f96fec275159a4afd58a3c9ad97958ab0a07db910*$/pkzip2$:token.txt:encrypted.zip::encrypted.zip
```

We save the hash (starting with $pkzip2$ and ending with $/pkzip2$) in a separate file called ziphash and crack it afterwards by running JohnTheRipper (hashcat does not support this hashtype yet).
```console
id3ar00t@kali:~/usdhackerday2019/Pictures# john ziphash -wordlist=/usr/share/seclists/Passwords/Leaked-Databases/rockyou.txt
Using default input encoding: UTF-8
Loaded 1 password hash (PKZIP [32/64])
Press 'q' or Ctrl-C to abort, almost any other key for status
bayer04leverkusen (?)
1g 0:00:00:00 DONE (2020-04-21 22:37) 2.272g/s 4546Kp/s 4546Kc/s 4546KC/s baylan..baybie19
Use the "--show" option to display all of the cracked passwords reliably
Session completed
```

Opening the zipfile with the cracked password __bayer04leverkusen__ leads us to the next flag:
__usd{9f776ce487003639f47c29ed7195772e}__

Another option would be to use fcrackzip:
> install: apt install fcrackzip  
> parameter u: since the hash often fails to be uniquely cracked, this flag ensures to test the password candidates  
> parameter D p: uses a wordlist  

```console
id3ar00t@kali:~/usdhackerday2019/Pictures# fcrackzip -u encrypted.zip -D -p rockyou.txt


PASSWORD FOUND!!!!: pw == bayer04leverkusen
```

After this easy flag, we can continue with [flag5: another simple passcracking task](flag5-secret.md)
