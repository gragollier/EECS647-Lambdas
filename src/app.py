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
    cur.execute('''SELECT postId, creator, bio, title, body, timestamp FROM Post P
                JOIN UserBio U ON P.creator = U.username
                WHERE P.forum = %s;''', (sub_name, ))
    rows = cur.fetchall()
    con.commit()

    posts = list(map(lambda row: {
            "postId": str(row[0]),
            "creator": row[1],
            "creatorBio": row[2],
            "title": row[3],
            "body": row[4],
            "timestamp": row[5]
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

def create_user(event, context):
    user = json.loads(event['body'])
    
    cur = con.cursor()
    status_code = 200
    try:
        cur.execute("INSERT INTO UserBio (username, bio) VALUES (%s, %s)", (user['username'], user['bio']))
        con.commit()
    except psycopg2.IntegrityError:
        status_code = 409
        con.rollback()

    return {
        "statusCode": status_code,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(user)
    }

def get_user(event, context):
    username = json.loads(event['body'])['username']

    output = {}

    cur = con.cursor()
    cur.execute('''SELECT commentId, C.body, C.timestamp, P.title, P.forum, P.postId FROM Comment C
                JOIN Post P ON C.postId = P.postId
                WHERE C.username = %s;''', (username, ))
    rows = cur.fetchall()

    output['comments'] = list(map(lambda row: {
        'commentId': str(row[0]),
        'body': row[1],
        'timestamp': row[2],
        'postTitle': row[3],
        'postForum': row[4],
        'postId': str(row[5])
        }, rows))
    
    cur.execute("SELECT postId, forum, title, timestamp FROM Post WHERE creator = %s", (username, ))
    rows = cur.fetchall()
    output['posts'] = list(map(lambda row: {
        'postId': str(row[0]),
        'forum': row[1],
        'title': row[2],
        'timestamp': row[3]
    }, rows))

    cur.execute("SELECT bio FROM UserBio WHERE username = %s", (username, ))
    row = cur.fetchone()
    output['bio'] = row[0]
    output['username'] = username

    con.commit()

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(output)
    }

def get_post(event, context):
    post_id = json.loads(event['body'])['postId']

    output = {}
    
    cur = con.cursor()
    cur.execute('''
            SELECT commentId, body, timestamp, C.username, U.bio FROM Comment C
            JOIN UserBio U ON U.username = C.username
            WHERE C.postId = %s;
    ''', (post_id, ))
    rows = cur.fetchall()

    output['comments'] = list(map(lambda row: {
        'commentId': str(row[0]),
        'body': row[1],
        'timestamp': row[2],
        'username': row[3],
        'userBio': row[4]
    }, rows))

    cur.execute("SELECT creator, forum, title, body, timestamp FROM Post WHERE postId = %s", (post_id, ))
    row = cur.fetchone()
    con.commit()

    output['creator'] = row[0]
    output['forum'] = row[1]
    output['title'] = row[2]
    output['body'] = row[3]
    output['timestamp'] = row[4]
    output['postId'] = post_id

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(output)
    }

def create_comment(event, context):
    comment = json.loads(event['body'])
    comment_id = uuid.uuid4()
    timestamp = datetime.datetime.now().isoformat()

    status_code = 200
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO Comment (commentId, body, timestamp, username, postId) VALUES (%s, %s, %s, %s, %s)", 
            (comment_id, comment['body'], timestamp, comment['username'], comment['postId']))
        con.commit()
    except psycopg2.IntegrityError:
        status_code = 409
        con.rollback()

    comment['commentId'] = str(comment_id)
    comment['timestamp'] = timestamp
    
    return {
        "statusCode": status_code,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(comment)
    }

    
