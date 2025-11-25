import asyncio


class PaymentServiceStub:
    async def process_payment(self, amount: int, currency: str = "UZS") -> bool:
        print(f"[PAYMENT] Processing payment of {amount} {currency}...")
        await asyncio.sleep(1)  # Simulate bank processing delay as per requirements
        print(f"[PAYMENT] Payment successful.")
        return True
