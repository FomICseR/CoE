import os
import json
import asyncio
from aiohttp import web
import handlers
import globals as g
from handlers import HANDLERS



async def broadcast_state():
    if not g.web_clients:
        return
    msg = json.dumps(g.devices_state, ensure_ascii=False)
    for client in list(g.web_clients):
        try:
            await client.send_str(msg)
        except Exception:
            g.web_clients.discard(client)



async def handle_register(ws, dev_id):
    g.device_clients[dev_id] = ws
    g.device_ids[ws] = dev_id
    print(f"Device {dev_id} registered")
    await ws.send_str(json.dumps({"status": "ok"}))

# ---------- JSON Functions ----------

# json example {"id": "base1","type": "button","op_id": "12","value": "1"}

async def handle_device_message(ws, message_text):
    # TODO: parsing
    try:
        msg = json.loads(message_text)
    except json.JSONDecodeError:
        print("Bad JSON from device")
        return
    dev_id = msg.get("id")
    msg_type = msg.get("type")

    if not dev_id or not msg_type:
        print("JSON have not id or type")
        return


    if dev_id not in g.device_clients:
        await handle_register(ws, dev_id)

    handler = HANDLERS.get(msg_type)
    if handler:
        await handler(ws, dev_id, msg)
    else:
        print(f"Unknown type: {msg_type}")



# json example {"type": , "target": , "command": ,  "value/argument":}

async def handle_web_message(ws, message_text):
    try:
        data = json.loads(message_text)
    except json.JSONDecodeError:
        return

    msg_type = data.get("type")
    if msg_type != "command":
        return

    target_id = data.get("target")
    cmd = data.get("cmd")
    value = data.get("value")

    if not target_id or not cmd:
        return

    # Finding device via ID
    dev_ws = g.device_clients.get(target_id)
    if not dev_ws:
        print(f"Устройство {target_id} не найдено")
        return

    # Preparing payload
    command = {"type": "command", "cmd": cmd}
    if value is not None:
        command["value"] = value

    await dev_ws.send_str(json.dumps(command))
    print(f"Команда {cmd} отправлена на {target_id}")





# ---------- WebSocket-handlers ----------
async def ws_device_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    dev_id = None
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await handle_device_message(ws, msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                print(f"Device WS error: {ws.exception()}")
    finally:
        if dev_id:
            g.device_clients.pop(dev_id, None)
        g.device_ids.pop(ws, None)
    return ws

async def ws_web_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    g.web_clients.add(ws)
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                await handle_web_message(ws, msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                print(f"Web WS error: {ws.exception()}")
    finally:
        g.web_clients.discard(ws)
    return ws

# ---------- HTTP-handlers (web pages) ----------
async def index(request):
    return web.FileResponse('./templates/index.html')

async def settings(request):
    return web.FileResponse('./templates/settings.html')

async def devices_page(request):
    return web.FileResponse('./templates/devices.html')

# ---------- Preparing app and routing ----------
def create_app():
    app = web.Application()

    app.router.add_static('/static/', path='./static', name='static')
    # Pages
    app.router.add_get('/', index)
    app.router.add_get('/settings', settings)
    app.router.add_get('/devices', devices_page)
    # WebSocket
    app.router.add_get('/ws/web', ws_web_handler)
    app.router.add_get('/ws/device', ws_device_handler)
    return app

if __name__ == '__main__':
    print("check http://localhost:8080")
    web.run_app(create_app(), host='0.0.0.0', port=8080)