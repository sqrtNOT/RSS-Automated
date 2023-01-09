#!/usr/bin/python3.9
"""
The point of this file is to take clawsmail/rssyl xml formatted rss feeds and add them to a mysql database
The target data for every RSS feed in the dataset:
	the RSS feed URL
	the canonical name of the feed in clawsmail
	any user given nickname of the feed
	the hierarchy of nested folders

the folder path is used as a rudimentary tagging system
Given the example: /important/academic/3Blue1Brown/Grant Sanderson

The actual feed is for the Grant Sanderson youtube channel and 3Blue1Brown, academic, and important are stored as tags for that channel

"""

from bs4 import BeautifulSoup
import mysql.connector

# database setup
conn = mysql.connector.connect(
    user="claws",
    password="B7VKx53vi0Ldx29BD5h1vpGozsfGBU3ydxCm41QM9jR3UjIk",
    host="localhost",
    database="rss",
)
cursor = conn.cursor()

# parsing the rssyl xml file
path_to_list = "~/.claws-mail/folderlist.xml"
folderlist = open(path_to_list, "r").read()
soup = BeautifulSoup(folderlist, "lxml")
folder = soup.find("folder", type="rssyl")
feeds = folder.find_all("folderitem")

# feed has been flattened and all the data we care about is in a list of folderitem dictionary objects
for feed in feeds:
    try:
        uri = feed["uri"]
    except:
        continue  # no uri in tree so it's a folder; skipping

    name = feed["name"]
    try:
        canonical_name = feed["official_title"]
    except:
        title = name

    # ignore the root item and the actual channel name for tagging
    tags = feed["path"].split("/")[1:-1]

    cursor.execute(
        r"insert into channels (url, channel_name, alt_name) values (%s,%s,%s)",
        (str(uri), str(canonical_name), str(name)),
    )
    cursor.execute(r"select channel_id from channels where url = %s ", (str(uri),))

    # there should only be one value but if duplicate feeds existed we don't want to fail on that case so fetchall
    channel_id = cursor.fetchall()[0][0]

    for tag in tags:
        cursor.execute(
            r"insert into tags (channel_id, tag) values (%s,%s)",
            (
                str(channel_id),
                str(tag),
            ),
        )

# commit changes at the end only if everything worked so we never write bad data
conn.commit()
