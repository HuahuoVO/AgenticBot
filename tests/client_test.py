import requests
import json

url = 'http://localhost:8000/chat'

with requests.post(url,
    json={"message": "你好"},
    stream=True,
    headers={"Accept": "text/event-stream"}
) as response:
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                json_data = json.loads(decoded_line[6:])
                print(f"收到消息: {json_data}")