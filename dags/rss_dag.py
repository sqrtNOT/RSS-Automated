from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
"""
This function essentially does 3 things for every feed in the database:
	1. retrieve the url from the database
	2. fetch and parse the RSS data using feedparser
	3. push the new entries into the videos table in the database
"""
def update_rss_feeds():
	import feedparser
	import mysql.connector
	import re
	from datetime import datetime
	from time import mktime

	#database setup
	conn=mysql.connector.connect(user='claws',password='B7VKx53vi0Ldx29BD5h1vpGozsfGBU3ydxCm41QM9jR3UjIk',host='localhost',database='rss')
	cursor=conn.cursor()

	#get the feed/channel data we need using previously setup channel tags
	cursor.execute(r"select channel_id, url from channels join tags using (channel_id) where tag='video' or tag='audio'")
	data=cursor.fetchall()

	#create a feedparser object for every channel
	feeds = [(channel_id, feedparser.parse(url),) for channel_id, url in data]

	#parse every feed and add the data to the videos table
	for (channel_id, feed) in feeds:
		if feed.get('status') != 200 or feed.get('bozo') != False or feed.get('bozo_exception') != None or feed.get('entries')==[]:
			continue #feed is broken, request failed, or no videos; skipping
		else:
			for entry in feed['entries']:
				title=entry.get('title') or None
				link=entry.get('link') or None

				#niconico and youtube disagree on the format for 'published' so we convert published_parsed instead
				rawtimestamp=entry.get('published_parsed') or None
				published = datetime.fromtimestamp(mktime(rawtimestamp)).isoformat()

				cursor.execute(r'insert ignore into videos (video_url, channel_id, video_title, video_date) values (%s,%s,%s,%s)',
									  (link, channel_id, title, published))
	conn.commit()

with DAG(
	'RSS_parser',
	default_args={
		'depends_on_past': False,
		'retries': 0,
	},
	description='Fetches new entries from RSS feeds',
	schedule_interval='0 */4 * * *', #every 4 hours
	start_date=datetime(2022, 5, 30),
	catchup=False,
) as dag:
	t1 = PythonOperator(
		task_id='update_rss_feeds',
		python_callable=update_rss_feeds,
)

update_rss_feeds
