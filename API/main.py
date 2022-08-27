from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import json
import mysql.connector

app = FastAPI()
templates = Jinja2Templates(directory='jinja/')


@app.get("/")
def root(request: Request):
    conn = mysql.connector.connect(user='subsapi', password='nLzM6KaoC50tOuKUPTvFl3WjIRYI4vac63vLwbpeCQvF5T6k', host='localhost', database='rss')
    cursor = conn.cursor()
    cursor.execute("select json_object('channel', channel_name, 'video', video_title, 'url', video_url) from videos join channels using (channel_id) where status is NULL order by video_date desc;")
    response = cursor.fetchall()
    if(len(response) == 0):
        videos = [{'No new videos': None}]
    else:
        videos = []
        for item in response:
            videos.append(json.loads(item[0]))
    return templates.TemplateResponse('subs.jinja', {'request': request, 'videos': videos})
