import datetime
import json
import uuid

import psycopg2
import psycopg2.extras

psycopg2.extras.register_uuid()

with open("config.json") as file:
    config = json.load(file)

db_config = config['database']

con = psycopg2.connect(database=db_config['database'],
    user=db_config['user'],
    password=db_config['password'],
    host=db_config['host'])

def create_sub_hackit(event, context):
    body = json.loads(event['body'])

    cur = con.cursor()
    status_code = 200
    try:
        cur.execute('INSERT INTO Forum (name, description) VALUES (%s, %s);', (body['name'], body['description']))
        con.commit()
    except psycopg2.IntegrityError:
        status_code = 409
        con.rollback()
    
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {"Access-Control-Allow-Origin": "*"}
    }

def list_sub_hackits(event, context):
    cur = con.cursor()
    cur.execute("SELECT name, description FROM Forum LIMIT 50;")
    rows = cur.fetchall()
    con.commit()
    output = list(map(lambda row: {'name': row[0], 'description': row[1]},  rows))

    return {
        "statusCode": 200,
        "body": json.dumps(output),
        "headers": {"Access-Control-Allow-Origin": "*"}
    }

def create_post(event, context):
    req = json.loads(event['body'])
    post_id = uuid.uuid4()
    creator = req['creator']
    sub = req['sub']
    title = req['title']
    body = req['body']
    time = datetime.datetime.now().isoformat()

    cur = con.cursor()
    cur.execute("INSERT INTO Post (postId, creator, forum, title, body, timestamp) VALUES (%s, %s, %s, %s, %s, %s);", (post_id, creator, sub, title, body, time))
    con.commit()

    output = req
    output['timestamp'] = time
    output['postId'] = str(post_id)

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(output)
    }


def get_sub_hackit(event, context):
    sub_name = json.loads(event['body'])['name']
    
    cur = con.cursor()
    cur.execute("SELECT postId, creator, title, body, timestamp FROM Post WHERE forum = %s;", (sub_name, ))
    rows = cur.fetchall()
    con.commit()

    posts = list(map(lambda row: {
            "postId": str(row[0]),
            "creator": row[1],
            "title": row[2],
            "body": row[3],
            "timestamp": row[4]
        }, rows))

    cur.execute("SELECT name, description FROM Forum WHERE name = %s;", (sub_name, ))
    row = cur.fetchone()
    con.commit()

    output = {
        "name": row[0],
        "description": row[1],
        "posts": posts
    }

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(output)
    }
