#Local Imports
import pkg.DisCORE.DisCORE as DisCORE

#External Imports
import praw
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

#Import config files
config = DisCORE.Data_JSON(file="examples/config.json").load()

#Set up DisCORE Logs for use
d = DisCORE.Logs(url=config["log_url"], name="UpdateChecker HFY")
d.doDebug(state=False)

#Set up DisCORE Notify for use
notify = DisCORE.Notify(url = config["hfy_url"], debug=d.doDebug())

#Set up PRAW from the Config
reddit = praw.Reddit(
    client_id=config["reddit"]["client_id"], 
    client_secret=config["reddit"]["client_secret"], 
    user_agent=config["reddit"]["user_agent"], 
    username=config["reddit"]["username"], 
    password=config["reddit"]["password"]
)

#Import the monitored items as "monitored" using Data_SQL
sql = DisCORE.Data_SQL((
        config["sql_server"]["host"],
        config["sql_server"]["database"],
        config["sql_server"]["username"],
        config["sql_server"]["password"]
    ))
monitored = sql.return_dictionary('hfy', "SELECT * FROM hfy")

#Begin to Iterate through current items
#If this code looks weird, it's ported from another project and modified for use.
has_changed = False

for item in monitored.keys():
    d.print("Checking "+monitored[item]["title"])
    last_creation_time = monitored[item]["unix"]
    recent_submissions = {}
    for submission in reddit.redditor(monitored[item]["author"]).submissions.new():
        if submission.created_utc < monitored[item]["unix"] and submission.subreddit.display_name == "HFY":
            pass
        else:
            test_submission = fuzz.token_sort_ratio(monitored[item]["title"], str(submission.title))
            if test_submission > 60:
                recent_submissions[submission.title] = "https://reddit.com" + submission.permalink
                if submission.created_utc > last_creation_time:
                    last_creation_time = submission.created_utc + 1
                    d.print("Updating last_creation_time...")
            else:
                pass

    if len(recent_submissions.keys()) > 0:
        d.print("New Chapters Discovered")
        has_changed = True
        for submission in recent_submissions:
            author = {
                "name":monitored[item]["author"],
                "icon":"https://i0.wp.com/uniquesportsplus.com/wp-content/uploads/2019/01/author-icon.png?fit=512%2C512&ssl=1&w=640",
                "url":"https://www.reddit.com/user/"+monitored[item]["author"]
            }
            embed = notify.embed(
                description="An Update For **"+monitored[item]["title"]+"** Has Been Posted",
                title=submission,
                url=recent_submissions[submission],
                color=0xffffff,
                thumbnail=reddit.redditor(monitored[item]["author"]).icon_img,
                author=author
                )
            notify.notify(embed=embed)
            d.print(content="Notification Sent - "+submission)
        monitored[item]["unix"] = last_creation_time
    else:
        d.print("No New Chapters")

if has_changed == True:
    sql.commit_dictionary(monitored, "hfy")
else:
    pass
    
d.commit()
