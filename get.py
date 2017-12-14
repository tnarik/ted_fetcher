#!/usr/bin/env python
import argparse
from bs4 import BeautifulSoup

import requests
import time
from tqdm import tqdm


parser = argparse.ArgumentParser(description="TED fetcher")
parser.add_argument('-n', '--dry-run', help='do not actually download',
    action='store_true', dest='dryrun', default=None)
args = parser.parse_args()

page = 1
while True:
    list_url = 'https://www.ted.com/talks/quick-list?page={}'.format(page)
    print("Trying '{}'".format(list_url))
    response = requests.get(list_url)
    
    soup = BeautifulSoup(response.content, "html.parser")
    all_rows = soup.find_all('div', class_='quick-list__container-row')    
    if len(all_rows) == 0:
        if response.status_code == 429:
            print('... Too many requests. sleep and retry')
            time.sleep(15)
            continue
        else:
            break

    hrefs = []
    ccm = 0
    cch = 0
    for row in all_rows:
        link_list = row.find_next('ul', class_='quick-list__download')
        links = link_list.find_all('a')
        href = None
        for l in links:
            if l.text == 'Medium' and href is None:
                ccm +=1
                href = l['href']
            if l.text == 'High':
                cch +=1
                href = l['href']
        if href is not None:
            hrefs.append(href)
        else:
            print("... On site video only : https://www.ted.com{}".format(row.find_next('a')['href']))
    
    print("... Found {} entries, {} medium and {} high. {} will be fetched, preferring high.".format(
            len(all_rows), ccm, cch, len(hrefs)))

    if not args.dryrun:
        for url in hrefs:
            if url.find('/'):
                filename = url.rsplit('/')[-1]
                filename = filename.split('?')[0]
            r = requests.get(url, allow_redirects=True, stream=True)
            size = int(r.headers['Content-Length'].strip())

            pbar = tqdm(total=size, desc=filename, unit_scale=True, unit='B')
            with open("vids/{}".format(filename), 'wb') as f:
                for buf in r.iter_content(1024):
                    if buf:
                        f.write(buf)
                        pbar.update(len(buf))
            pbar.close()

    page += 1