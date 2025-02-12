import pyttsx3
import speech_recognition as sr
import random
import webbrowser
import datetime
from plyer import notification
import pyautogui
import os
import google.generativeai as genai
import wikipedia
import pywhatkit as pwk
import time
import user_config
import nltk
from nltk.corpus import wordnet
import operator
import requests
from xml.etree import ElementTree as ET
import re
import sounddevice as sd
import vosk
import queue
from threading import Thread
import pandas as pd
genai.configure(api_key= user_config.genai_api)

engine = pyttsx3.init()

voices = engine.getProperty('voices')       #getting details of current voice
engine.setProperty('voice', voices[0].id)
engine.setProperty("rate", 150)

SENDER_EMAIL = "dhruvin1309@gmail.com"
SENDER_PASSWORD = user_config.gmail_pass

q = queue.Queue()
model = vosk.Model(r"F:\Personal Jarvis\vosk-model-small-en-us-0.15")

environment_active = True  # Flag to keep the script running
assistant_active = False   # Flag to control activation

def define_word(request):
    request = request.lower().strip()  # Normalize input
    
    if "what does" in request and "meaning" in request:
        try:
            # Extract the word to define
            request = request.replace("what does", "").replace("meaning", "").strip()
            
            # Fetch synsets from WordNet
            synsets = wordnet.synsets(request)

            if synsets:
                # Extract the first definition
                meaning = synsets[0].definition()
                speak(f"The meaning of {request} is: {meaning}")
                print(f"The meaning of {request} is: {meaning}")
            else:
                speak("Sorry, I couldn't find the meaning.")
                print("Sorry, I couldn't find the meaning.")

        except Exception as e:
            speak("Error finding the meaning. Please try again.")
            print(f"Error: {e}")
            
def get_gemini_response(prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text

def speak(audio):
    engine.say(audio)
    engine.runAndWait()
    
def command():
    content = " "
    while content == " ":
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Say something!")
            audio = r.listen(source)
        # recognize speech using Google Speech Recognition
        try:
            content = r.recognize_google(audio, language = 'en-in')
            print("You said :" + content)
        except Exception as e:
            print("Please Try Again....")
        return content
    
def listen_hotword():
    global assistant_active, environment_active
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    
    while environment_active:
        with mic as source:
            print("Listening for 'Nova'...")
            audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio, language='en-in').lower()
            print(f"Recognized: {text}")
            
            if "nova" in text:
                speak("Yes sir, How can i assist you today?")
                assistant_active = True
                main_process()
            elif "avjo" in text or "bye" in text:
                speak("Goodbye, but I'm still here if you need me.")
                assistant_active = False
        except sr.UnknownValueError:
            continue
        except sr.RequestError:
            speak("Sorry, there was an issue with recognition.")
    
def main_process():
    global assistant_active
    while assistant_active:
        request = command().lower()
        if "hello" in request:
            speak("Welcome, How can i help you now?")
            
        elif "play music" in request:
            speak("Sure sir! i will play your favourite music.")
            song = random.randint(0,4)
            yt_songs = ["https://www.youtube.com/watch?v=MA0aCUxItYA",
                        "https://www.youtube.com/watch?v=XO8wew38VM8",
                        "https://www.youtube.com/watch?v=bO2pms5R5P0",
                        "https://www.youtube.com/watch?v=Zc_Pi5EbuMw",
                        "https://www.youtube.com/watch?v=YNSYzibbbhE"]
            webbrowser.open(yt_songs[song])
        elif "bye" in request or "byy" in request:
            speak("Goodbye, but I'm still here if you need me.")
            assistant_active = False
            break
            
        elif "tell me current time" in request:
            now_time = datetime.datetime.now().strftime("%H:%M")
            speak("Sure sir! Current time is " +  str(now_time))
            
        elif "tell me today date" in request:
            now_time = datetime.datetime.now().strftime("%d:%m")
            speak("Sure sir! Today's date is " +  str(now_time))
            
        elif "add task" in request:
            task = request.replace("add task","")
            task = task.strip()
            if task != "":
                speak("Adding task: "+ task)
                with open("todo.txt","a") as file:
                    file.write(task + "\n")
                    
        elif "remind me task" in request:
            with open("todo.txt","r") as file:
                speak("Pending Works are : " + file.read())
                
        elif "show me task" in request:
            with open("todo.txt","r") as file:
                tasks = file.read()
                notification.notify(
                    title = "Pending Work",
                    message = tasks
                )
                
        elif "delete task" in request:
            try:
                with open("todo.txt", "r") as file:
                    tasks = file.readlines()
                
                if not tasks:
                    speak("There are no tasks to delete.")
                    print("No tasks found!")
                else:
                    speak("Here are your tasks.")
                    print("Your tasks:")
                    for i, task in enumerate(tasks, start=1):
                        print(f"{i}. {task.strip()}")
                        
                    speak("Please tell me the task you want to delete.")
                    delete_task = command().strip()  # Capturing speech input

                    # Remove the task if found
                    updated_tasks = [task for task in tasks if task.strip().lower() != delete_task.lower()]

                    # Write the updated tasks back to file
                    with open("todo.txt", "w") as file:
                        file.writelines(updated_tasks)

                    if len(tasks) == len(updated_tasks):
                        speak("Task not found. Please try again.")
                    else:
                        speak(f"Task deleted successfully: {delete_task}")

            except FileNotFoundError:
                speak("Task file not found. Please add tasks first.")
                
        elif "open" in request:
            query = request.replace("open","")
            pyautogui.press("super")
            pyautogui.typewrite(query)
            pyautogui.sleep(2)
            pyautogui.press("enter")
        
        elif "explain" in request:  # Example condition for Gemini API response
            topic = request.replace("explain", "").strip()
            response = get_gemini_response(f"Explain {topic} in simple terms with example.")
            print(response)
            speak(response)
        
        elif "what does" in request and "meaning" in request:
            define_word(request)
            
        elif "take screenshot" in request:
           
            base_filename = "my_screenshot" 
            extension = ".png"
            counter = 0
            
            while os.path.exists(f"{base_filename}{counter}{extension}"):
                counter += 1
            screenshot = pyautogui.screenshot()
            
            filename = f"{base_filename}{counter}{extension}"
            screenshot.save(filename)
            speak("Screenshot Saved sir!")
            
        elif "wikipedia" in request:
            request = request.replace("jarvis","")
            request = request.replace("search on wikipedia ","")
            print(request)
            result = wikipedia.summary(request, sentences = 2)
            print(result)
            speak(result)
            
        elif "search on google" in request:
            request = request.replace("jarvis","")
            request = request.replace("search on google ","")
            webbrowser.open("https://www.google.com/search?q=" + request)
            
        elif "send whatsapp message" in request:
            speak("Please say the phone number with country code.")
            phone_number = command().replace(" ", "")  # Capture number from voice

            speak("What message would you like to send?")
            message = command()

            pwk.sendwhatmsg_instantly(phone_number, message)
            
            time.sleep(5)
            pyautogui.press("enter")
            speak("Message sent successfully.")
            
        # elif "send email" in request:
        #     speak("Please say the recipient's email address.")
        #     receiver_email = command()
            
        #     speak("What is the subject of the email?")
        #     subject = command()
            
        #     speak("What is the content of the email?")
        #     content = command()
        #     pwk.send_mail("dhruvin1309@gmail.com", user_config.gmail_pass, subject, content | MIMEText, receiver_email)
        # elif "ask ai" in request:
        #     request = request.replace("jarvis","")
        #     request = request.replace("ask ai ","")
        #     print(request)
        #     response = ai.send_request(request)
        #     print(response)
        #     speak(response)
            
        elif "calculate" in request:
            operations = {
                'plus': operator.add,
                'add': operator.add,
                'minus': operator.sub,
                'subtract': operator.sub,
                'times': operator.mul,
                'multiply': operator.mul,
                'divided': operator.truediv,
                'divide': operator.truediv,
                'mod': operator.mod,
                'modulus': operator.mod,
                'power': operator.pow
            }      

            # Replace symbols with words
            request = request.replace("calculate", "").strip()
            request = request.replace("+", " plus ")
            request = request.replace("-", " minus ")
            request = request.replace("*", " times ")
            request = request.replace("/", " divided ")
            
            print(f"🟢 Debug: Processing Calculation Request: '{request}'")  # Debugging

            try:
                print(f"🔵 Debug: Split Words: {request.split()}")  # Debugging

                # Regex to match patterns like "5 plus 3", "10 divided by 2", etc.
                pattern = r'(\d+(\.\d+)?)\s*(plus|add|minus|subtract|times|multiply|divided|divide|mod|modulus|power)\s*(\d+(\.\d+)?)'
                match = re.search(pattern, request)

                if match:
                    num1 = float(match.group(1))
                    operation = match.group(3).lower()
                    num2 = float(match.group(4))

                    if operation in operations:
                        result = operations[operation](num1, num2)
                        speak(f"The result is {result}")
                        print(f"✅ Success: {num1} {operation} {num2} = {result}")  
                    else:
                        speak("Sorry, I couldn't recognize the operation.")
                        print(f"❌ Error: Operation '{operation}' not found.")  

                else:
                    speak("Sorry, I couldn't understand the calculation. Please say something like '5 plus 3' or '10 divided by 2'.")
                    print("❌ Regex failed to match the calculation request.")

            except Exception as e:
                speak("There was an error with the calculation.")  
                print(f"❌ Error: {e}")  


  
        elif "tell me news" in request:
            bbc_url = 'http://feeds.bbci.co.uk/news/rss.xml'
            try:
                response = requests.get(bbc_url)
                response.raise_for_status()  # Raises an error for bad responses

                tree = ET.fromstring(response.content)
                items = tree.findall('.//item')

                if items:
                    speak("Here are the latest headlines from BBC:")
                    for i, item in enumerate(items[:5], start=1):
                        title = item.find('title')
                        if title is not None:
                            print(f"Headline {i}: {title.text}")
                            speak(f"Headline {i}: {title.text}")
                        else:
                            speak(f"Headline {i}: No title found.")
                else:
                    speak("No headlines found in the BBC feed.")

            except requests.exceptions.RequestException as req_err:
                speak("Network error while fetching BBC news.")
            except ET.ParseError:
                speak("Error parsing the BBC news feed.")
            except Exception as e:
                speak("An unexpected error occurred while fetching BBC news.")  

if __name__ == "__main__":
    listen_hotword()