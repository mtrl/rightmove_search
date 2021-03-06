import urllib2
#import pygame
from os import listdir
from os.path import isfile, join
import shutil
import time
import hashlib
import webbrowser
from BeautifulSoup import BeautifulSoup
import sys

def main():
    # Import settings
    config = {}
    execfile("settings.conf", config)

    #load_alert_sound(config["alert_sound_file"])

    search_home = config["search_home"]
    output_dir = config["output_dir"]
    keywords = config["keywords"]
    root_url = 'http://www.rightmove.co.uk'

    output_file = "property_search_results"
    wait_time = 1 # Pause for x seconds between requests
    user_agent = 'Mozilla/5 (Solaris 10) Gecko'
    headers = { 'User-Agent' : user_agent }

    copy_templates(output_dir)
    output_file = output_file + "_" + sanitise_filename(str(search_home[0])) + ".html"
    output_path = output_dir + output_file

    request = urllib2.Request(root_url + search_home[1] + "&numberOfPropertiesPerPage=50", headers=headers)
    search_html = urllib2.urlopen(request).read()
    search_soup = BeautifulSoup(search_html);

    paging_div = search_soup.findAll('div', {'class':'sliderGallery'})
    page_links = paging_div[0].findAll('a')

    page_urls = [search_home[1]]

    for page_link in page_links:
        page_urls.append(page_link['href'])

    with open("template/head.html", "r") as myfile:
        head_html = myfile.read().replace('\n', '')
        head_html = head_html.replace("[[TITLE]]", search_home[0])

    with open("template/foot.html", "r") as myfile:
        foot_html = myfile.read().replace('\n', '')

    with open(output_path, "w") as text_file:
        #text_file.write('<meta http-equiv="refresh" content="10">')
        text_file.write(head_html)
        text_file.write("<h1>" + search_home[0] + "</h1>")
        text_file.write("<h2>The following property's descriptions contain your search terms</h2>")
        text_file.write("<p><a href='" + root_url + search_home[1] + "' target='_blank'>This is the original search page</a></p>")
        text_file.write("<p>The search terms were <em>" + ", ".join(keywords) + "</em></p>")

        text_file.write('<table class="table table-bordered table-hover">')
        text_file.write('<thead><tr><th>Title</th>')
        text_file.write('<th>Price</th>')
        text_file.write('<th>Image</th>')
        text_file.write('<th>Found search terms</th></tr></thead>')
        text_file.write('<tbody>')

    create_index_file(output_dir, head_html, foot_html)
    # open a browser tab showing the results
    webbrowser.open('file:///' + str(output_dir) + str(output_file), new=2)

    i = 1
    property_links = []
    print "Scraping results page",
    for pageUrl in page_urls:
        # Wait a moment so we don't trigger the bot blocker
        time.sleep(wait_time)
        print (str(i)),
        #print "Waiting " + str(wait_time) + " seconds"
        sys.stdout.flush()
        # get the HTML
        request = urllib2.Request(root_url + pageUrl, headers=headers)
        page_html = BeautifulSoup(urllib2.urlopen(request).read())

        # now we go through each page of results and get the property results one at a time
        properties = page_html.findAll('ol',{'id':'summaries'})

        #print str(len(properties))

        if len(properties) > 0:
            properties = properties[0].findAll('div', {'class':'details clearfix'})

            for property in properties:
                property_link = property.find('a')['href']
                property_links.append(property_link)

            #print str(len(property_links))
        i = i + 1
    print ""
    print "Done. We have " + str(len(property_links)) + " properties to search."

    # now we go through each property and search for keywords
    property_results = []
    i = 1
    j = 1
    print "Searching properties for keywords"

    print("Searching property "),
    for property_link in property_links:
        print (str(i)),
        sys.stdout.flush()
        time.sleep(wait_time)

        request = urllib2.Request(root_url + property_link, headers=headers)
        property_html = BeautifulSoup(urllib2.urlopen(request).read())
        # get the body text
        desc = str(property_html.find('div',{'class':'tabbed-content-tab-content description'}))
        try:
            img = str(property_html.find('a',{'id':'thumbnail-0'}).find('img'))
        except Exception as e:
            print "Whoops. Exception. " + str(e)
            img = "No image"
        # Does it have keyword in the desc?
        results = []
        for word in keywords:
            if str(desc).find(word) > 0:
                results.append(word)

        if(len(results) > 0):
            print(":)"),
            # Play the alert sound
            #pygame.mixer.music.play()
            #while pygame.mixer.music.get_busy() == True:
            #    continue

            result = [root_url + property_link, img, results]
            # Get property info
            price = str(property_html.find('p', { 'id': 'propertyHeaderPrice'}).find('strong').text)
            title = str(property_html.find('h1', { 'class': 'fs-22'}).text)
            subtitle = str(property_html.find('div', { 'class': 'property-header-bedroom-and-price'}).find('address').text)
            property_anchor = '<a href="' + root_url + property_link + '" target="_blank">'

            with open(output_path, "a") as text_file:
                text_file.write('<tr>')
                text_file.write('<td>' + property_anchor + '<strong>' + title + '</strong><br>' + subtitle + '</a></td>')
                text_file.write('<td>' + property_anchor + price + '</a></td>')
                text_file.write('<td>' + property_anchor + img + '</a></td>')
                text_file.write('<td>' + ", ".join(results) + '</td>')
                text_file.write('</tr>')

            property_results.append(result)
            j = j + 1
        i = i + 1

    print "---"
    print "Done. Found " + str(len(property_results)) + " properties. I've written the results to " + output_dir

    with open(output_path, "a") as text_file:
        text_file.write('</tbody></table>')
        text_file.write(foot_html)

#def load_alert_sound(alert_sound_file):
    #pygame.mixer.init()
    #pygame.mixer.music.load(alert_sound_file)


def create_index_file(output_dir, head_html, foot_html):
    results_files = [ f for f in listdir(output_dir) if isfile(join(output_dir,f)) ]
    with open(output_dir + "index.html", "w") as text_file:
        text_file.write(head_html)
        for result_file in results_files:
            if not result_file.startswith('.') and not result_file == "index.html":
                text_file.write('<p><a href="' + result_file + '">' + result_file + "</a></p>")
        text_file.write(foot_html)

def search(text,n):
    #Searches for text, and retrieves n words either side of the text, which are retuned seperatly
    word = r"\W*([\w]+)"
    groups = re.search(r'{}\W*{}{}'.format(word*n,'place',word*n),t).groups()
    return groups[:n],groups[n:]

def sanitise_filename(filename):
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(" ", "_")

def copy_templates(output_dir):
    shutil.rmtree(output_dir + "template", True)
    shutil.copytree('template', output_dir + 'template')

if __name__ == "__main__":
    main()
