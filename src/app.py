import json
import psycopg2

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
    output = list(map(lambda row: {'name': row[0], 'description': row[1]},  rows))

    return {
        "statusCode": 200,
        "body": json.dumps(output),
        "headers": {"Access-Control-Allow-Origin": "*"}
    }
