
# Хранилища WebSocket-соединений
web_clients = set()          # все подключённые браузеры
device_clients = {}          # {id_устройства: ws}
device_ids = {}              # обратное: {ws: id_устройства}
devices_state = {}           # состояние для отправки веб-клиентам (JSON)