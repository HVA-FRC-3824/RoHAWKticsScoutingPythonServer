import usb1
import logging

from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


class Accessory:
    def __init__(self, **kwargs):
        self.vid = kwargs.get('vid', '')
        self.pid = kwargs.get('pid', '')

    def __str__(self):
        return "Accessory {0:s}:{1:s}".format(self.vid, self.pid)

class InternetBridge:
    def __init__(self):
        self.context = usb1.USBContext().__enter__()

    def hotplug_callback(self, context, device, event):
        if event == usb1.LIBUSB_HOTPLUG_EVENT_DEVICE_ARRIVED:
            logger.info("usb plugged in")
            self.on_device_connected(device)
        else:
            logger.warning("Unknown libusb_hotplug_event: {}".format(event))

        return 0

    def on_device_connected(self, device):
        accessory = Accessory(vid=device.device_descriptor.idVendor, pid=device.device_descriptor.idProduct)
        print(accessory)
