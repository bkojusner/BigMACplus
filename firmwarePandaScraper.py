import requests, os, time
from bs4 import BeautifulSoup

# Global Lists
googleLinks = []
mediafireLinks = []
androidfilehostLinks = []
other = []

def mediafireDL(vendor):
    # Original file name is necessary so using spaghetti code
    print("Downloading MediaFire Firmware for " + vendor)
    for file in mediafireLinks:
        dpage = requests.get(file)
        dsoup = BeautifulSoup(dpage.content, "html.parser")
        dresults = dsoup.find(id="downloadButton")
        dlink = str(dresults).split('\"')[5]
        #print(dlink) # Here for debugging purposes
        os.system('%s %s "%s"' % ('wget -P', vendor, dlink))

def download(vendor):
    if len(mediafireLinks) != 0:
        mediafireDL(vendor)
    if len(googleLinks) != 0:
        print("No support for Google yet")
    #    googleDL()
    if len(androidfilehostLinks) != 0:
    #    afhDL()
        print("No support for AndroidFileHost yet")

def cleanupLists():
    googleLinks.clear()
    mediafireLinks.clear()
    androidfilehostLinks.clear()
    other.clear()

def printLists():
    print("---MediaFire---")
    print(mediafireLinks)
    print("---Google---")
    print(googleLinks)
    print("---AndroidFileHost---")
    print(androidfilehostLinks)
    print("---Other---")
    print(other)

def getFinalLinks(waitingLinks):
    for w in waitingLinks:
        wpage = requests.get(w)
        wsoup = BeautifulSoup(wpage.content, "html.parser")
        wresults = wsoup.find(class_="site-inner")
        wfiltered = wresults.find_all("a", class_="btn btn-success fp-download-link")
        
        #print("Currently on " + str(wfiltered)) # Here for debugging purposes
        if len(wfiltered) == 0:
            continue
        
        wlink = str(wfiltered).split()[5].split('\'')[1]
        if "mediafire" in wlink:
            mediafireLinks.append(wlink)
        elif "drive.google" in wlink:
            googleLinks.append(wlink)
        elif "androidfilehost" in wlink:
            androidfilehostLinks.append(wlink)
        else:
            other.append(wlink)

def getWaitingLinks(filteredLinks):
    # Get the link for the 20 second wait page, aka each unique firmware link
    waitingLinks = []
    for l in filteredLinks:
        lpage = requests.get(l)
        lsoup = BeautifulSoup(lpage.content, "html.parser")
        lresults = lsoup.find(id="genesis-content")
        lfiltered = lresults.find_all("div", class_="fp-download-section")

        counter = 0
        getLinkIndicator = []
        for c in lfiltered[0].find_all('p'):
            # Only works on pages that have the Android OS Version available
            # Usually when the Android OS Version is not there it is old but this needs fixing
            if "Android OS Version" in str(c):
                counter = counter + 1
                #print("Currently at ", c) # Here for debugging purposes
                try:
                    # The OS Version is NA
                    if "NA" in str(c):
                        continue
                    elif int(str(c).split(':')[1].strip()[0]) >= 7:
                        #print(c) # Print the Android OS Version it found for debugging purposes
                        getLinkIndicator.append(counter)
                except ValueError:
                    # The OS Version string is malformatted
                    if (str(c).split(':')[1].strip()) == '</p>':
                        continue
                    elif int(str(c).split('>')[3].split('.')[0]) >= 7:
                        #print(c) # Print the Android OS Version it found for debugging purposes
                        getLinkIndicator.append(counter)

        tempCounter = 0
        for d in lfiltered[0].find_all('a', href=True):
            tempCounter = tempCounter + 1
            if tempCounter in getLinkIndicator:
                # Sometimes there are links to flashers instead of firmware
                # Removing the links we don't want Note: This means that just
                # because you saw Android 7.0 was detected, doesn't mean it will
                # be downloaded
                if "https://firmwarepanda.com" not in d['href']:
                    #print("https://firmwarepanda.com" + d['href']) # Here for debugging purposes
                    waitingLinks.append("https://firmwarepanda.com" + d['href'])
    return waitingLinks

# Remove any redundant links or unnecessary links from list
def cleanupURLS(vendor, linksList):
    filteredLinks = []
    for i in linksList:
        tmp1 = "https://firmwarepanda.com/"
        tmp2 = "https://firmwarepanda.com/device/" + vendor + "/"
        if i == tmp1 or "/page/" in i or i == tmp2:
            continue
        if i not in filteredLinks:
            filteredLinks.append(i)
    return filteredLinks

# Traverese every page, starting from the last page going back
def traversePages(pages, pageURL, linksList):
    for n in range(pages, 1, -1):
        npage = requests.get(pageURL + str(n) + '/')
        nsoup = BeautifulSoup(npage.content, "html.parser")
        nresults = nsoup.find(id="genesis-content")
        for a in nresults.find_all('a', href=True):
            linksList.append(a['href'])
    return linksList

def getPages(linksList, traverse):
    tmp = []
    for i in linksList:
        if "page/" in i:
            tmp.append(i.split('/')[-2])
    try:
        pages = int(max(tmp))
    except ValueError:
        # One page or vendor does not exist
        traverse = False
        return traverse
    return pages

def start(vendor):
    print("Starting extraction for " + vendor)
    baseURL = "https://firmwarepanda.com/device/"
    linksList = []
    URL = baseURL + str(vendor) + '/'
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(id="genesis-content")
    pageURL = URL + "page/"

    # Get all the a href that are found on the first page
    for a in results.find_all('a', href=True):
        linksList.append(a['href'])

    traverse = True
    print("Getting Pages")
    pages = getPages(linksList, traverse)
    if pages:
        print("Traversing Pages")
        linksList = traversePages(pages, pageURL, linksList)
    print("Cleaning up URLS")
    filteredLinks = cleanupURLS(vendor, linksList)
    print("Obtaining Panda Links")
    waitingLinks = getWaitingLinks(filteredLinks)
    print("Getting Final List")
    getFinalLinks(waitingLinks)

def main():
    s = time.time()
    #vendor = str(input("Vendors: "))
    vendors = list(map(str,input("Vendors: ").strip().split()))
    for vendor in vendors:
        start(vendor)
        print("---BAG SECURED---")
        printLists()
        #download(vendor)
        cleanupLists()
        print("---" + vendor + " Done---")
    e = time.time()
    print(f"Runtime of the program is {e - s}")

main()

"""
STATUS:
Right now it extracts all the links that are on FirmwarePanda for any given vendor
It will specifically look for links to images that are equal to or greater than Android 7
It currently is only capable of downloading MediaFire links

TODOs:
x Get Google download working
x Get Android File Host working
x Do preliminary test to see if it can get all URLS and downloads for all vendors
x Leave running on Frank
x Start trying to get it to work on FirmwareFile
"""