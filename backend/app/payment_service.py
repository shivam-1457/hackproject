import uuid

def simulate_payment(amount:float, method:str):
    return f"SIM-{uuid.uuid4().hex[:12].upper()}", "paid"
