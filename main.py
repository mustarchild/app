from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock

from jnius import autoclass
import threading

# Android Bluetooth classes
BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
UUID = autoclass('java.util.UUID')

class BluetoothApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.label = Label(text="Not Connected", font_size=20)
        self.add_widget(self.label)

        self.btn = Button(text="Connect HC-06", size_hint=(1, 0.2))
        self.btn.bind(on_press=self.connect_bt)
        self.add_widget(self.btn)

        self.socket = None
        self.input_stream = None

    def connect_bt(self, instance):
        self.label.text = "Connecting..."
        threading.Thread(target=self.bt_thread).start()

    def bt_thread(self):
        try:
            adapter = BluetoothAdapter.getDefaultAdapter()
            device = adapter.getRemoteDevice("00:21:13:01:23:45")  # 🔴 CHANGE MAC

            uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
            self.socket = device.createRfcommSocketToServiceRecord(uuid)
            self.socket.connect()

            self.input_stream = self.socket.getInputStream()

            Clock.schedule_once(lambda dt: setattr(self.label, 'text', 'Connected'))

            self.read_data()

        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.label, 'text', f"Error: {e}"))

    def read_data(self):
        buffer = bytearray(1024)

        while True:
            bytes_available = self.input_stream.available()
            if bytes_available > 0:
                num = self.input_stream.read(buffer)
                data = buffer[:num].decode('utf-8', errors='ignore')

                Clock.schedule_once(lambda dt, d=data: self.update_label(d))

    def update_label(self, data):
        self.label.text = f"Received:\n{data}"

class HC06App(App):
    def build(self):
        return BluetoothApp()

if __name__ == "__main__":
    HC06App().run()
