import asyncio
from bleak import BleakClient

# Replace this with your actual BLE device's MAC address
ADDRESS = "08:B6:1F:B9:67:CA"

async def handle_notification(characteristic: str, data: bytearray):
    dataString = data.decode("utf-8")
    if dataString[6] == "n":
        print("Not a number")
    else:
        print(float(dataString[6:-2]))

# Define the main async function for communication
async def run():
    async with BleakClient(ADDRESS) as client:
        print(f"Connected: {client.is_connected}")

        # Get the service and characteristic UUIDs (replace with your specific UUIDs)
        service_uuid = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
        characteristic_uuid = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

        # Set up the notification handler
        await client.start_notify(characteristic_uuid, handle_notification)

        # Wait indefinitely for notifications (you can add a timeout if needed)
        print("Waiting for notifications...")
        await asyncio.sleep(30)  # Keeps the program running for 30 seconds
        # You can adjust this time or use a loop to keep the program running
        await client.stop_notify(characteristic_uuid)

# Run the program
asyncio.run(run())
