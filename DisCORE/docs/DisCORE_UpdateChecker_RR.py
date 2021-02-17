#Add an additional PYTHONPATH area because it can't find my package.
import sys
sys.path.append('/data/packages/')

#External Imports
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from bs4 import BeautifulSoup
import urllib3
import os
from subprocess import check_output, STDOUT, call, PIPE

from DisCORE import DisCORE

#Custom RoyalRoad class, based on a script I found that was non-functioning.
#Not sure whose work this was originally, but it's not mine. I just made it work in Python 3.
#Raise an issue if you made this originally so I can add credit to this file.
class RoyalRoad:
    def __init__(self, url=None, is_chapter=False, only_chapter_info=False):
        """
        Scans a RoyalRoad Book or Chapter to Gather Information which is exposed in class variables beginning either 'fiction_' or 'book_' dependant on namespace
        'url' should be a Fully Qualified RoyalRoad URL
        'is_chapter' is a boolean that only returns 'fiction' data when 'True'
        """
        self.local_is_chapter = is_chapter

        self.fiction_url = url
        self.fiction_id = None
        self.fiction_title = None
        self.fiction_author = None
        self.fiction_author_id = None

        self.book_stats = None
        self.book_chapters = None
        self.book_chapter_amount = None
        self.book_description = None
        self.book_genres = [None]
        self.book_cover_image = None
        self.book_is_active = None

        soup = BeautifulSoup(urllib3.PoolManager().request('GET', url).data, "html5lib")

        if only_chapter_info:
            self.chapters(soup)
        elif is_chapter:
            self.fiction(soup)
        elif not is_chapter:
            self.fiction(soup)
            self.book(soup)

    def author(self, soup):
        author = soup.find('span', attrs={'property': 'name'})
        
        if author == None:
            author = soup.find('h3', attrs={'class': 'font-white inline-block'}).text
        else:
            author = author.text
        if author == "":
            author = None

        if author == None:
            return [None, None]
        else:
            new_soup = BeautifulSoup(urllib3.PoolManager().request('GET', "https://www.royalroad.com/user/memberlist?q="+str(author.replace(" ","+"))).data, "html5lib")
            try:
                author_id = int(new_soup.find("tbody").find("tr").find("td").find("a").get("href").split("/")[2])
            except:
                author_id = None

            return [author.strip(), author_id]

    def fiction(self, soup):
        self.fiction_id = (self.fiction_url).strip("https://www.royalroad.com/fiction/").split("/")[0]
        self.fiction_title = soup.find('h1', attrs={'class': 'font-white'}).text.strip()
        author = self.author(soup)
        self.fiction_author = author[0]
        self.fiction_author_id = author[1]

    def book(self, soup):

        self.chapters(soup)

        self.book_stats = [
            stat.text.strip() for stat in soup.findAll('li', attrs={'class': 'bold uppercase font-red-sunglo'})
            ][:6]

        if not soup.find('div', attrs={'class': 'number font-red-sunglo'}):
            self.book_is_active = True
        else:
            self.book_is_active = False

        self.book_description = soup.find('div', attrs={'property': 'description'}).text.strip()

        self.book_cover_image = soup.find('img', attrs={'property': 'image'}).get('src')
        if self.book_cover_image == "undefined":
            self.book_cover_image = "/content/images/nocover-new-min.png"

        for tag in soup.findAll('span', attrs={'class': 'label label-default label-sm bg-blue-hoki'}):
            self.book_genres.append(tag.text.strip())
        for tag in soup.findAll('span', attrs={'property': 'genre'}):
            self.book_genres.append(tag.text.strip())

    def chapters(self, soup):
        self.book_chapters = [
            tag.get("data-url") for tag in soup.findAll('tr', attrs={'style': 'cursor: pointer'})
            ]

        self.book_chapter_amount = len(self.book_chapters)

#Import config files
config = DisCORE.Data_JSON(file="/data/global/config.json").load()

#Set up DisCORE Logs for use
d = DisCORE.Logs(url=config["log_url"], name="UpdateChecker RR")
d.doDebug(state=False)

#Set up DisCORE Notify for use
notify = DisCORE.Notify(url = config["rr_url"], debug=d.doDebug())

#Import the monitored items as "monitored" using Data_SQL
sql = DisCORE.Data_SQL((
        config["sql_server"]["host"],
        config["sql_server"]["database"],
        config["sql_server"]["username"],
        config["sql_server"]["password"]
    ))
monitored = sql.return_dictionary('rr', "SELECT * FROM rr")

known_books = []

for dirname, dirnames, filenames in os.walk("/books"):
  for filename in filenames:
    if filename.endswith(".epub"):
      known_books.append(os.path.join(dirname, filename))
    else:
      pass

#Begin to Iterate through current items
#If this code looks weird, it's ported from another project and modified for use.
has_changed = True

for item in monitored.keys():
    #Check if this is a new entry to the DB, if it is then collect all information.
    #If not, collect only chapter information to speed up the process
    if monitored[item]["fiction_url"] == None or monitored[item]["is_active"] == None:
        is_new = True
        monitored[item]["fiction_url"] = "https://www.royalroad.com/fiction/"+item
        datum = RoyalRoad(url=monitored[item]["fiction_url"])
        d.print("Checking "+datum.fiction_title)
        if monitored[item]["chapter_amount"] == None:
            monitored[item]["chapter_amount"] = 0
    else:
        is_new = False
        datum = RoyalRoad(url=monitored[item]["fiction_url"], only_chapter_info=True)
        d.print("Checking "+monitored[item]["title"])

    datum_links = []

    #If new, put all information into the DB and notify that a new book has been added. Else, carry on.
    if is_new:
        monitored[item]["title"] = datum.fiction_title
        monitored[item]["author"] = datum.fiction_author
        monitored[item]["author_url"] = "https://www.royalroad.com/profile/"+str(datum.fiction_author_id)
        monitored[item]["cover_image"] = datum.book_cover_image
        monitored[item]["is_active"] = datum.book_is_active

        author = {
            "name":monitored[item]["author"],
            "icon":"https://i0.wp.com/uniquesportsplus.com/wp-content/uploads/2019/01/author-icon.png?fit=512%2C512&ssl=1&w=640",
            "url":monitored[item]["author_url"]
        }
        embed = notify.embed(
            description="A New Book Has Been Set for Notifications",
            title=monitored[item]["title"],
            url=monitored[item]["fiction_url"],
            color=0xada638,
            thumbnail=monitored[item]["cover_image"],
            author=author
            )
        notify.notify(embed=embed)

        d.print("New Media Notification Sent - "+monitored[item]["title"])
    else:
        pass

    #Check to see if new chapters have been added and go through the motions
    if datum.book_chapter_amount > monitored[item]["chapter_amount"]:
        d.print("[{datum}] - New Chapters Discovered".format(datum=datum.book_chapter_amount))
        has_changed = True
        for i in range(monitored[item]["chapter_amount"], datum.book_chapter_amount):
            datum_links.append("https://www.royalroad.com"+datum.book_chapters[i])

        #Send a notification for every new chapter
        for y in range(0, len(datum_links)):
            chapter_datum = RoyalRoad(url=datum_links[y],is_chapter=True)
            author = {
                "name":monitored[item]["author"],
                "icon":"https://i0.wp.com/uniquesportsplus.com/wp-content/uploads/2019/01/author-icon.png?fit=512%2C512&ssl=1&w=640",
                "url":monitored[item]["author_url"]
            }
            embed = notify.embed(
                description="An Update For **"+monitored[item]["title"]+"** Has Been Posted",
                title=chapter_datum.fiction_title,
                url=datum_links[y],
                color=0xada638,
                thumbnail=monitored[item]["cover_image"],
                author=author
                )
            notify.notify(embed=embed)
            d.print(content="Notification Sent - "+monitored[item]["title"])
        
        monitored[item]["chapter_amount"] = datum.book_chapter_amount
        monitored[item]["last_chapter_url"] = datum_links[-1]

        search_response = process.extractOne(monitored[item]["title"]+" - "+monitored[item]["author"], known_books, scorer=fuzz.token_sort_ratio)
        try:
            res = check_output('fanficfare -u "{}"'.format(search_response[0]), shell=True, stderr=STDOUT, stdin=PIPE)
            d.print("[OUTPUT] ["+str(search_response[1])+"%]"+str(res))
            d.print(content="Succesfully Updated Book Automatically")
        except:
            d.print(content="Failed to Update Book Automatically")

    #If there has been a database issue (unlikely), fix it and continue.
    #Discovered that if chapters are manually deleted (Damn you Kindle Unlimited) it triggers this.
    elif datum.book_chapter_amount < monitored[item]["chapter_amount"]:
        d.print("[{datum}] < [{item}] - Discovered chapter issue. Resolving.".format(datum=datum.book_chapter_amount, item=monitored[item]["chapter_amount"]))
        monitored[item]["chapter_amount"] = datum.book_chapter_amount
        has_changed = True

        if monitored[item]["last_chapter_url"] != datum.book_chapters[-1]:
            d.print("[WARN] Last Chapter Changed - Potential Database Issue")
            notify.notify(embed=notify.embed("Potential Database Issue. Please Check Logs.","[WARN] UpdateChecker_RR"))

    else:
        d.print("[{item}] - No New Chapters".format(item=monitored[item]["chapter_amount"]))

#Push to the database
if has_changed == True:
    sql.commit_dictionary(monitored, "rr")
else:
    pass
    
d.commit()