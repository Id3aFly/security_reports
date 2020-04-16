
## 2. ~/Desktop/USB_IMG.img:

There are two ways to get this flag:

### a) Unpack the image

What I usually always do at first, is to check the type of the file.

```console
id3ar00t@kali:~/usdhackerday2019/Desktop# file USB_IMG.img 
USB_IMG.img: Linux rev 1.0 ext4 filesystem data, UUID=ebf34c32-9a04-43ee-a4b1-0cc21daca1fa (extents) (64bit) (large files) (huge files)
```

As it is detected as an ext4 file, I try to mount it:
```console
id3ar00t@kali:~/usdhackerday2019/Desktop# mkdir mount
id3ar00t@kali:~/usdhackerday2019/Desktop# mount -o loop USB_IMG.img  mount/
```

Now,  I'm able to look inside the mounted filesystem with tree.
> install: apt install tree  
> parameter -a: show all files, including hidden files
```console
id3ar00t@kali:~/usdhackerday2019/Desktop/mount# tree -a
.
├── lost+found
└── .Trash-0
    ├── files
    │   └── token.txt
    └── info
        └── token.txt.trashinfo
```

The token.txt looks interesting, and after opening it, we see the first flag:
```console
id3ar00t@kali:~/usdhackerday2019/Desktop# cat mount/.Trash-0/files/token.txt 
usd{f8839ce04fd9443f295224b843f9b21d}
```

### b) Quick string search

If you search inside the file for all strings, you directly get the second flag:

```console
id3ar00t@kali:~/usdhackerday2019/Desktop# strings USB_IMG.img 
/id3ar00t/Desktop/mount
lost+found
token.txt
.Trash-0xt.swp
info
files
token.txt.trashinfo
token.txt.trashinfo.M9FIZZ
token.txt
[Trash Info]
Path=token.txt
DeletionDate=2019-04-08T16:32:14
usd{f8839ce04fd9443f295224b843f9b21d}
/id3ar00t/Desktop/mount
lost+found
token.txt
.token.txt.swp
/media/usb
/media/usb
MUMJ
lost+found
token.txt
.token.txt.swp
/media/usb
```

Now,  we found this simple flag, we can go on with [flag 3: an aes crypto challenge](flag3-documents-token.pdf.md)
