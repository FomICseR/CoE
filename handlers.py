import globals as g
import json

async def handle_button(ws, dev_id, data):
    pin = data.get("op_id")
    value = data.get("value")
    print(f"Button event from {dev_id}, pin {pin}, value {value}")
    g.devices_state['last_button_event'] = {
        'device': dev_id, 'pin': pin, 'value': value
    }
    await g.broadcast()

async def handle_temp(ws, dev_id, data):
    try:
        temp = float(data.get("value", 0))
    except (ValueError, TypeError):
        return
    sensors = g.devices_state.setdefault('sensors', {})
    sensors[f"{dev_id}_temp"] = temp
    await g.broadcast()

HANDLERS = {
    "button": handle_button,
    "temp": handle_temp,
}