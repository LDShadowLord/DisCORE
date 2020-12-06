#Add an additional PYTHONPATH area because it can't find my package.
import sys
sys.path.append('/data/packages/')

#External Imports
from bs4 import BeautifulSoup
import urllib

from DisCORE import DisCORE

#Import config files
config = DisCORE.Data_JSON(file="/data/global/config.json").load()

#Set up DisCORE Logs for use
d = DisCORE.Logs(url=config["log_url"], name="UpdateChecker LIT")
d.doDebug(state=False)

#Set up DisCORE Notify for use
notify = DisCORE.Notify(url = config["lit_url"], debug=d.doDebug())

#Import the monitored items as "monitored" using Data_SQL
sql = DisCORE.Data_SQL((
        config["sql_server"]["host"],
        config["sql_server"]["database"],
        config["sql_server"]["username"],
        config["sql_server"]["password"]
    ))
monitored_db = sql.return_dictionary('lit', "SELECT * FROM lit")

has_changed = False

for uid in monitored_db.keys():
    #Download the Webpage, have BS4 read it
    response = urllib.request.urlopen('https://www.literotica.com/stories/memberpage.php?uid='+uid+'&page=submissions')
    value = response.read()
    soup = BeautifulSoup(value, "html5lib")

    for text in soup.findAll('img', {'src': 'https://www.literotica.com/stories/images/memberpage/ico_n.gif'}):
        table = text.findParents('tr')[0]
        author = soup.find("a", {'class': 'contactheader'}).text
        post_title = table.find("td", {'class': 'fc'}).find("a", {'class': 'bb'}).text
        post_link = table.find("td", {'class': 'fc'}).find("a", {'class': 'bb'}, href=True)['href']
        post_date = table.find_all("td")[3].text.split("/")
        out_category = table.find_all("td")[2].find("a").find("span").text

        if monitored_db[uid]["author"] == None:
            monitored_db[uid]["author"] = author
            has_changed = True

        db_json = DisCORE.Data_JSON(monitored_db[uid]["previous_urls"],strip="'").load()

        if post_link not in db_json:
            db_json.append(post_link)
            monitored_db[uid]["previous_urls"] = DisCORE.Data_JSON(db_json).dump()
            has_changed = True

            author = {
                "name":monitored_db[uid]["author"],
                "icon":"https://i0.wp.com/uniquesportsplus.com/wp-content/uploads/2019/01/author-icon.png?fit=512%2C512&ssl=1&w=640",
                "url":"https://www.literotica.com/stories/memberpage.php?uid="+uid
            }
            embed = notify.embed(
                description=out_category,
                title=post_title,
                url=post_link,
                color=0x4a89f3,
                author=author
                )
            notify.notify(embed=embed)
            d.print(content="Notification Sent - "+post_title)
        else:
            d.print(content="Item already notified - "+post_title)
    
if has_changed == True:
    sql.commit_dictionary(monitored_db, "lit")
else:
    pass
    
d.commit()