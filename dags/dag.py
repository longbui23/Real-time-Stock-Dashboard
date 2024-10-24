import os
import sys
from datetime import datetime, timedelta
import requests


from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'LongBui',
    'start_date': datetime(2024, 10, 10),
}


def get_data():
    import requests

    res = requests.get("https://random.org/api/")
    res =  res.json()

    return res


def format_data(res):
    data = {}
    location = res['location']
    data['id'] = uuid.uuid4()
    data['first_name'] = res['name']['first']
    data['last_name'] = res['name']['last']
    data['gender'] = res['gender']
    data['address'] = f"{str(location['street']['number'])} {location['street']['name']}, " \
                      f"{location['city']}, {location['state']}, {location['country']}"
    data['post_code'] = location['postcode']
    data['email'] = res['email']
    data['username'] = res['login']['username']
    data['dob'] = res['dob']['date']
    data['registered_date'] = res['registered']['date']
    data['phone'] = res['phone']
    data['picture'] = res['picture']['medium']

    return data


def stream_data():
    import json
    from kafka import KafkaProducer
    import time
    import logging

    producer = KafkaProducer(bootstrap_servers=['broker:29092'], max_block_ms=50000)
    curr_time = time.time()

    while True:
        if time.time() > curr_time + 60:
            break
        try:
            res = get_data()
            res = format_data()

            producer.send('user_created', json.dumps(res).encode('utf-8'))

        except Exception as e:
            logging.erorr(f'An error occured: {e}')
            continue

        with DAG('user_automation',
                 default_args=default_args,
                 schedule_interval = '@daily',
                 catchup=False) as dag:
            
            streaming_task = PythonOperator(
                task_id = 'stream_data_from_api',
                python_callable = stream_data,
            )


