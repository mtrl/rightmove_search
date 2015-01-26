import urllib2
import time
import hashlib
import webbrowser
from BeautifulSoup import BeautifulSoup

def main():
#    search_home = ['10 mile radius Shrewsbury 28k2', '/property-for-sale/find.html?locationIdentifier=REGION%5E1208&maxPrice=280000&minBedrooms=3&displayPropertyType=houses&oldDisplayPropertyType=houses&numberOfPropertiesPerPage=50&radius=10.0&googleAnalyticsChannel=buying']
    search_home = ['north and west of Shrewsbury 4 beds to 375k', '/property-for-sale/find.html?locationIdentifier=USERDEFINEDAREA%5E%7B%22id%22%3A2707198%7D&maxPrice=375000&minBedrooms=4&displayPropertyType=houses&oldDisplayPropertyType=houses&primaryDisplayPropertyType=houses&oldPrimaryDisplayPropertyType=houses&sortType=&numberOfPropertiesPerPage=50']
    
    keywords = ['paddock', 'field', 'acre', 'huge garden', 'large garden']
    root_url = 'http://www.rightmove.co.uk'

    output_file = "property_search_results"
    output_dir = "/Users/mark/Dropbox/rightmove_search/"
    waitSec = 1
    user_agent = 'Mozilla/5 (Solaris 10) Gecko'
    headers = { 'User-Agent' : user_agent }

    output_file = output_file + "_" + sanitise_filename(str(search_home[0])) + ".html"
    output_path = output_dir + output_file

    request = urllib2.Request(root_url + search_home[1], headers=headers)
    search_html = urllib2.urlopen(request).read()
    search_soup = BeautifulSoup(search_html);

    paging_div = search_soup.findAll('div', {'class':'sliderGallery'})
    page_links = paging_div[0].findAll('a')

    page_urls = [search_home[1]]
    for page_link in page_links:
        page_urls.append(page_link['href'])

    with open(output_path, "w") as text_file:
        #text_file.write('<meta http-equiv="refresh" content="10">')
        text_file.write("<h1>" + search_home[0] + "</h1>")
        text_file.write("<h2>Found the following properties with the keywords you are looking for</h2>")
        text_file.write("<p><a href='" + root_url + search_home[1] + "' target='_blank'>This is the original search page</a></p>")

    # open a browser tab showing the results
    webbrowser.open('file:///' + str(output_dir) + str(output_file), new=2)

    i = 1
    property_links = []
    for pageUrl in page_urls:
        # Wait a moment so we don't trigger the bot blocker
        print "About to scrape page " + str(i)
        print "Waiting " + str(waitSec) + " seconds"
        time.sleep(waitSec)

        # get the HTML
        request = urllib2.Request(root_url + pageUrl, headers=headers)
        page_html = BeautifulSoup(urllib2.urlopen(request).read())

        # now we go through each page of results and get the property results one at a time
        properties = page_html.findAll('ol',{'id':'summaries'})

        if len(properties) > 0:
            properties = properties[0].findAll('div', {'class':'photoswrapper'})

            for property in properties:
                property_link = property.find('a')['href']
                property_links.append(property_link)

        i = i + 1

    print "Done. We have " + str(len(property_links)) + " properties to search."

    # now we go through each property and search for keywords
    property_results = []
    i = 1
    j = 1
    print "Parsing properties"
    print "---"

    for property_link in property_links:
        print "About to search property " + str(i) + ". Waiting " + str(waitSec) + " seconds..."
        time.sleep(waitSec)

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
            print "WOOHOOO! I've found a property with keywords " + str(results) + " :)"
            result = [root_url + property_link, img, results]
            # Get property info
            price = str(property_html.find('p', { 'id': 'propertyHeaderPrice'}).find('strong').text)
            title = str(property_html.find('h1', { 'class': 'fs-22'}).text)
            subtitle = str(property_html.find('div', { 'class': 'property-header-bedroom-and-price'}).find('address').text)

            with open(output_path, "a") as text_file:
                text_file.write('<p>' + str(j) + ' <a href="' + root_url + property_link + '" target="_blank"><strong>' + title + '</strong><br>' + subtitle + '<br>' + price + '<br>' + img + '</a><br>' + str(results) + '</p>')

            property_results.append(result)
            j = j + 1
        i = i + 1

    #save the results
    print "---"
    print "Done. Found " + str(len(property_results)) + " properties. I've written the results to " + output_dir

def search(text,n):
    '''Searches for text, and retrieves n words either side of the text, which are retuned seperatly'''
    word = r"\W*([\w]+)"
    groups = re.search(r'{}\W*{}{}'.format(word*n,'place',word*n),t).groups()
    return groups[:n],groups[n:]
    
def sanitise_filename(filename):
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(" ", "_")

main()