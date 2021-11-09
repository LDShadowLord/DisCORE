#Add an additional PYTHONPATH area because it can't find my package.
import sys
sys.path.append('/data/packages/')

#External Imports
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import os
from subprocess import check_output, STDOUT, call, PIPE

from DisCORE import DisCORE
from UCClassDef import ClassDef

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
has_changed = True

for item in monitored.keys():
    provider = monitored[item]["fiction_provider"]

    #Check if this is a new entry to the DB, if it is then collect all information.
    #If not, collect only chapter information to speed up the process
    if monitored[item]["fiction_url"] == None or monitored[item]["is_active"] == None:
        is_new = True
        if provider == "RoyalRoad":
            if not monitored[item]["fiction_url"]:
                monitored[item]["fiction_url"] = "https://www.royalroad.com/fiction/"+monitored[item]["fiction_id"]
            datum = ClassDef.RoyalRoad(url=monitored[item]["fiction_url"])
        elif provider == "ScribbleHub":
            if not monitored[item]["fiction_url"]:
                monitored[item]["fiction_url"] = "https://www.scribblehub.com/series/"+monitored[item]["fiction_id"]
            datum = ClassDef.ScribbleHub(url=monitored[item]["fiction_url"])
        if monitored[item]["chapter_amount"] == None:
            monitored[item]["chapter_amount"] = 0
        d.print("Checking "+datum.fiction_title)
    else:
        is_new = False
        if provider == "RoyalRoad":
            datum = ClassDef.RoyalRoad(url=monitored[item]["fiction_url"], only_chapter_info=True)
        elif provider == "ScribbleHub":
            datum = ClassDef.ScribbleHub(url=monitored[item]["fiction_url"], only_chapter_info=True)
        d.print("Checking "+monitored[item]["title"])

    datum_links = []

    #If new, put all information into the DB and notify that a new book has been added. Else, carry on. Notifications are seperated so that things are colourcoded. A E S T H E T I C S.
    if is_new:
        monitored[item]["title"] = datum.fiction_title
        monitored[item]["author"] = datum.fiction_author
        monitored[item]["author_url"] = datum.fiction_author_url
        monitored[item]["cover_image"] = datum.book_cover_image
        monitored[item]["is_active"] = datum.book_is_active

        author = {
            "name":monitored[item]["author"],
            "icon":"https://i0.wp.com/uniquesportsplus.com/wp-content/uploads/2019/01/author-icon.png?fit=512%2C512&ssl=1&w=640",
            "url":monitored[item]["author_url"]
        }
        if provider == "RoyalRoad":
            embed = notify.embed(
                description="A New Book Has Been Set for Notifications",
                title=monitored[item]["title"],
                url=monitored[item]["fiction_url"],
                color=0xada638,
                thumbnail=monitored[item]["cover_image"],
                author=author
            )
        elif provider == "ScribbleHub":
            embed = notify.embed(
                description="A New Book Has Been Set for Notifications",
                title=monitored[item]["title"],
                url=monitored[item]["fiction_url"],
                color=0x185886,
                thumbnail=monitored[item]["cover_image"],
                author=author
            )
        notify.notify(embed=embed)

        d.print("New Media Notification Sent - "+monitored[item]["title"])
    else:
        pass

    #Check to see if new chapters have been added and go through the motions
    #Also checks to see if the last chapter has been changed (fixes an edge case scenario where a chapter is deleted and a new one immediately uploaded)
    if datum.book_chapter_amount > monitored[item]["chapter_amount"] or monitored[item]["last_chapter_url"] != datum.book_chapters[-1]:
        is_lcm = False
        if datum.book_chapter_amount > monitored[item]["chapter_amount"]:
            d.print("[{datum}] - New Chapters Discovered".format(datum=datum.book_chapter_amount))
            has_changed = True
            for i in range(monitored[item]["chapter_amount"], datum.book_chapter_amount):
                datum_links.append(datum.book_chapters[i])
        elif monitored[item]["last_chapter_url"] != datum.book_chapters[-1]:
            d.print("[{datum}] - New Chapters Discovered (LCM)".format(datum=datum.book_chapter_amount))
            is_lcm = True
            has_changed = True
            datum_links.append(datum.book_chapters[-1])

        #Send a notification for every new chapter
        for y in range(0, len(datum_links)):
            author = {
                "name":monitored[item]["author"],
                "icon":"https://i0.wp.com/uniquesportsplus.com/wp-content/uploads/2019/01/author-icon.png?fit=512%2C512&ssl=1&w=640",
                "url":monitored[item]["author_url"]
            }
            if provider == "RoyalRoad":
                chapter_datum = ClassDef.RoyalRoad(url=datum_links[y],is_chapter=True)
                embed = notify.embed(
                    description="An Update For **"+monitored[item]["title"]+"** Has Been Posted",
                    title=chapter_datum.fiction_title,
                    url=datum_links[y],
                    color=0xada638,
                    thumbnail=monitored[item]["cover_image"],
                    author=author
                    )
            elif provider == "ScribbleHub": 
                chapter_datum = ClassDef.ScribbleHub(url=datum_links[y],is_chapter=True)
                embed = notify.embed(
                    description="An Update For **"+monitored[item]["title"]+"** Has Been Posted",
                    title=chapter_datum.fiction_title,
                    url=datum_links[y],
                    color=0x185886,
                    thumbnail=monitored[item]["cover_image"],
                    author=author
                    )
            if is_lcm:
                embed.add_field("LastChapterModified","An LCM Warning has been generated for this notification.",False)
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