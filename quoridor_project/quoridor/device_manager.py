from .models import Device

class DeviceManager:
    @staticmethod
    def register_device(device_id, name=None):
        device, created = Device.objects.get_or_create(
            device_id=device_id,
            defaults={'name': name}
        )
        return device

    @staticmethod
    def get_device(device_id):
        try:
            return Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return None