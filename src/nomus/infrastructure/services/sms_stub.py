import asyncio


class SmsServiceStub:
    async def send_sms(self, phone: str, code: str) -> bool:
        print(f"[SMS] Sending code {code} to {phone}...")
        await asyncio.sleep(0.1)  # Simulate network delay
        print(f"[SMS] Code sent successfully.")
        return True
