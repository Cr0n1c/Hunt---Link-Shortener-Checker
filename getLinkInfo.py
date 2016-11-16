#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python
 import json
 import os
 import re
 import urllib2

 import bs4

 from multiprocessing.dummy import Pool as ThreadPool
 from optparse import OptionParser
 from pprint import pprint

 api_url = "http://www.getlinkinfo.com/info?link="

 def safe_check(string):
     if re.search('Safe', string): return 'Safe'
     elif re.search('Unsafe', string): return 'Unsafe'
     else: return 'Unknown'

 def run_query(query_url):
     data = { "title": "",
              "description": "",
              "url": query_url,
              "url_status": "Unknown",
              "effective_url": "",
              "redirections": {},
              "external_links": {},
              "safe_browsing": "",
              "overall_status": ""
             }

     full_url = api_url + query_url
     url = urllib2.urlopen(full_url)

     content = url.read()
     soup = bs4.BeautifulSoup(content, "lxml")

     #Getting title
     try:    data['title'] = soup.find("dd").get_text()
     except: pass

     #Getting description
     try:    data['description'] = soup.find_all("dd")[1].get_text().strip()
     except: pass

     #Getting url status
     try:    data['url_status'] = safe_check(soup.find_all("dd")[2].get_text().split(u'\xa0')[-1])
     except: pass

     #Getting effective_url
     try:    data['effective_url'] = soup.find_all("dd")[3].get_text().split(u'\xa0')[0].strip()
     except: pass
     
     #Getting redirections
     try:
         for link in soup.find("dd", class_="redirections-list").get_text().split('http')[1:]:
             fixed_link = 'http'+link.split(u'\xa0')[0].strip()
             data['redirections'][fixed_link] = safe_check(link.split(u'\xa0')[-1])
     except:
         pass

     #Getting external links
     try:
         for link in soup.find("dd", class_="external-links-list").get_text().split('http')[1:]:
             fixed_link = 'http'+link.split(u'\xa0')[0].strip()
             data['external_links'][fixed_link] = safe_check(link.split(u'\xa0')[-1])
     except:
         pass

     #Getting safe_browsing
     try:    data['safe_browsing'] = soup.find("dd", class_="badware-details-unsafe").get_text()
     except: pass

     #status checking
     if data['url_status'] == 'Unsafe':
         data['overall_status'] = 'Unsafe'
         return data
     elif re.search('WARNING!', data['safe_browsing']):
         data['overall_status'] = 'Unsafe'
         return data

     for link, status in data['redirections'].items():
         if status == 'Unsafe':
             data['overall_status'] = 'Unsafe'
             return data

     for link, status in data['external_links'].items():
         if status == 'Unsafe':
             data['overall_status'] = 'Unsafe'
             return data

     if data['url_status'] == 'Safe':
         data['overall_status'] = 'Safe'
     else:
         data['overall_status'] = 'Unknown'

     return data

if __name__ == '__main__':
     parser = OptionParser(usage="usage: %prog [options]")
     parser.add_option('-i', '--inputfile', dest='infile', action="store", type="string", help='file that contains urls')
     parser.add_option('-o', '--outputfile', dest='outfile', action="store", type="string", help='file to write results to')
     parser.add_option('-t', '--threads', dest='threads', action="store", type="int", help='number of threads to use')

     (opts, args) = parser.parse_args()

     if not opts.infile:
         print '[!] You did not specify an inputfile'
         print parser.print_help()
         exit()
     elif not os.path.isfile(opts.infile):
         print '[!] Input file does not exist'
         print parser.print_help()
         exit()

     if opts.threads: pool = ThreadPool(opts.threads)
     else: pool = ThreadPool(100)

     urls = []
     with open(opts.infile) as f: g = f.readlines()

     for i in g: urls.append(i.strip())

     results = pool.map(run_query, urls)
     for i in results:
         if opts.outfile:
             with open(opts.outfile, 'a') as f: f.write(json.dumps(i) + '\n')
         else: pprint(i)
