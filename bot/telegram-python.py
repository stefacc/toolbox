import json
import os
import urllib.request
from urllib.parse import urlencode

BOT_TOKEN = os.environ.get('TOKEN')

def request(_chat_id, _message):
    params = urlencode({'text': _message})
    url = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage?chat_id=' + _chat_id + \
                '&parse_mode=HTML&' + params
    
    req = urllib.request.Request(url, headers={'content-type': 'application/json'})
    response = urllib.request.urlopen(req)
    return response

def lambda_handler(event, context):
    request_body = json.loads(event['body'])

    chat_id = json.dumps(request_body['message']['chat']['id'])
    msg = json.dumps(request_body['message']['text']).strip('"')

    # msg == command and remove '/'
    command = msg[1:]
    if command == 'start':
        message = "Welcome to my Bot!"
        request(chat_id, message)
    elif command == 'stop':
        try:
            message = "bye bye"
            request(chat_id, single)
        except Exception as e:
            print(e)
            message = "Try again!"
            request(chat_id, message)
    else:
        message = "Try again!"
        request(chat_id, message)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
