import random

def rand_number():
    letters = "АВЕКМНОРСТУХ"

    regions = ["77", "97", "177", "197", "777"]

    number = (
        random.choice(letters) +
        f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}" +
        random.choice(letters) + random.choice(letters) + random.choice(regions)  
    )
    
    return number