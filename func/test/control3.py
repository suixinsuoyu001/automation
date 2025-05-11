from pynput import mouse

def on_click(x, y, button, pressed):
    if pressed:
        print(f"鼠标点击位置：({x}, {y})")

with mouse.Listener(on_click=on_click) as listener:
    listener.join()