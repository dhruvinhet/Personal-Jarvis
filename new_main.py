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
import cv2
import pandas as pd
import numpy as np  
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import pytesseract
import emoji
import pyperclip
from langdetect import detect
from threading import Thread
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

def clean_data(file_path):
    try:
        df = pd.read_csv(file_path, delimiter=',', on_bad_lines='skip')
        
        speak("I have loaded the dataset. Do you want to proceed with data cleaning? Say yes or no.")
        confirmation = command().lower()
        
        if "no" in confirmation:
            speak("Data cleaning canceled.")
            return
        
        speak("Starting the data cleaning process.")
        
        # Step 1: Remove duplicate rows
        df.drop_duplicates(inplace=True)
        speak("Duplicate rows removed.")
        
        # Step 2: Handle missing values
        df.fillna(method='ffill', inplace=True)  # Forward fill missing values
        df.fillna(method='bfill', inplace=True)  # Backward fill remaining missing values
        speak("Missing values handled Successfully.")
        
        # Step 3: Remove columns with excessive missing values
        threshold = 0.6 * len(df)  # If more than 60% missing, drop column
        df.dropna(thresh=threshold, axis=1, inplace=True)
        speak("Columns with excessive missing values removed.")
        
        # Step 4: Standardize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace(r"[^a-zA-Z0-9_]", "", regex=True)

        speak("Column names standardized.")
        
        # Step 5: Convert categorical variables to lowercase
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.lower().str.strip()
        speak("Categorical variables converted to lowercase.")
        
        # Step 6: Remove outliers using z-score method
        from scipy.stats import zscore
        numeric_cols = df.select_dtypes(include=['number']).columns
        z_scores = df[numeric_cols].apply(zscore)
        df = df[(z_scores.abs() < 3).all(axis=1)]
        speak("Outliers removed using z-score method.")
        
        # Step 7: Convert date columns to datetime format
        for col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass  # Ignore non-date columns
        speak("Date columns converted to datetime format.")
        
        # Step 8: Normalize numerical data
        for col in numeric_cols:
            df[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        speak("Numerical data normalized.")
        
        # Step 9: Encode categorical variables
        # df = pd.get_dummies(df, drop_first=True)
        # speak("Categorical variables encoded.")
        
        # Step 10: Save the cleaned dataset
        cleaned_file_path = file_path.replace(".csv", "_cleaned.csv")
        df.to_csv(cleaned_file_path, index=False)
        
        speak(f"Data cleaning complete. The cleaned file is saved as {cleaned_file_path}")
        print(f"Data cleaning complete. The cleaned file is saved as {cleaned_file_path}")
        generate_data_cleaning_report(file_path)
    except FileNotFoundError:
        speak("File not found. Please check the file name and try again.")
    except Exception as e:
        speak("An error occurred while cleaning the data.")
        print(f"Error: {e}")
        
def generate_data_cleaning_report(file_path):
    try:
        df = pd.read_csv(file_path, delimiter=',', on_bad_lines='skip')
        report_file = file_path.replace(".csv", "_cleaning_report.pdf")
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", style='B', size=16)
        pdf.cell(200, 10, "Data Cleaning Report", ln=True, align='C')
        pdf.ln(10)

        # Data Summary
        pdf.set_font("Arial", size=12)
        missing_values = df.isnull().sum().sum()
        duplicate_rows = df.duplicated().sum()
        pdf.multi_cell(0, 10, f"Total Missing Values: {missing_values}\n")
        pdf.multi_cell(0, 10, f"Total Duplicate Rows: {duplicate_rows}\n")

        # Handling Missing Values (Only for numeric columns)
        numeric_cols = df.select_dtypes(include=['number']).columns
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')  # Convert only numeric columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        df.drop_duplicates(inplace=True)

        # Outlier Detection using IQR Method
        pdf.add_page()
        pdf.set_font("Arial", style='B', size=14)
        pdf.cell(200, 10, "Outlier Analysis", ln=True, align='C')
        outlier_counts = {}
        for col in df.select_dtypes(include=['number']).columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
            outlier_counts[col] = outliers
        pdf.multi_cell(0, 10, f"Outliers per column: {outlier_counts}\n")

        # Correlation Matrix
        pdf.add_page()
        pdf.cell(200, 10, "Correlation Matrix", ln=True, align='C')
        plt.figure(figsize=(10, 8))
        corr_matrix = df[numeric_cols].corr()  # Only include numeric columns
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f')
        corr_img = "correlation_matrix.png"
        plt.savefig(corr_img)
        plt.close()
        pdf.image(corr_img, x=10, w=180)
        os.remove(corr_img)

        # AI-Powered Cleaning Suggestions (Using Z-score Anomaly Detection)
        # AI-Powered Cleaning Suggestions (Using Z-score Anomaly Detection)
        pdf.add_page()
        pdf.cell(200, 10, "AI-Powered Cleaning Suggestions", ln=True, align='C')
        anomalies = {}
        for col in df.select_dtypes(include=['number']).columns:
            z_scores = (df[col] - df[col].mean()) / df[col].std()
            outliers = df[abs(z_scores) > 3][col]
            if not outliers.empty:
                anomalies[col] = {
                    "Outlier Values": outliers.tolist(),
                    "Suggested Fix": f"Consider replacing with median {df[col].median()}"
                }
        pdf.multi_cell(0, 10, f"Potential anomalies detected: {anomalies}\n")


        # Generate Histograms
        pdf.add_page()
        pdf.set_font("Arial", style='B', size=14)
        pdf.cell(200, 10, "Data Distribution (Histograms)", ln=True, align='C')
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            plt.figure()
            sns.histplot(df[col], bins=30, kde=True)
            plt.title(f"Histogram of {col}")
            img_path = f"{col}_hist.png"
            plt.savefig(img_path)
            plt.close()
            pdf.image(img_path, x=10, w=180)
            os.remove(img_path)

        # Save PDF
        pdf.output(report_file)
        return report_file
    
    except Exception as e:
        print(f"Error generating report: {e}")
        return None

def extract_whatsapp_chat():
    # Take screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save("whatsapp_screenshot.png")

    # Load image using OpenCV
    img = cv2.imread("whatsapp_screenshot.png")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    pytesseract.pytesseract.tesseract_cmd = r"F:\Tesseract-OCR\tesseract.exe"
    # Use Tesseract OCR to extract text
    chat_text = pytesseract.image_to_string(gray)
    
    return chat_text


def generate_reply(chat_history):
    # Determine the language of the chat
    language = detect(chat_history)
    
    # Determine the tone based on keywords
    family_keywords = ["papa", "didi", "mummy", "bapu", "bhai"]
    friend_keywords = ["MIT", "mit", "dude", "mate", "pal"]
    
    if any(keyword in chat_history.lower() for keyword in family_keywords):
        tone = "normal"
    elif any(keyword in chat_history.lower() for keyword in friend_keywords):
        tone = "friendly"
    else:
        tone = "casual"
    
    prompt = f"Based on the following chat messages in {language}, suggest a {tone} reply using both text and emojis where appropriate:\n\n{chat_history}\n\nReply:"
    response = get_gemini_response(prompt)

    if isinstance(response, dict) and "choices" in response:  # Handle JSON response
        raw_reply = response["choices"][0]["message"]["content"].strip()
    elif isinstance(response, str):  # Handle plain text response
        raw_reply = response.strip()
    else:
        raw_reply = "I couldn't generate a reply."  # Default if unexpected format

    final_reply = emoji.emojize(raw_reply, language='alias')
    return final_reply

def send_whatsapp_message(message):
    try:
        speak("Do you want to send this message? Say yes or no.")
        confirmation = command().lower()
        
        if "yes" in confirmation:
            pyperclip.copy(message)
            pyautogui.click(500, 800)  # Adjust X, Y based on your screen
            pyautogui.hotkey("ctrl", "v")
            time.sleep(1)
            pyautogui.press("enter")
            speak("Message sent successfully.")
        else:
            speak("Message not sent.")
    except pyautogui.FailSafeException:
        print("PyAutoGUI Failsafe triggered. Exiting.")
        speak("Failsafe triggered. Please move your mouse to the top-left corner to stop.")
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
            request = request.replace("plus", " + ")
            phone_number = command().replace(" ", "")  # Capture number from voice

            speak("What message would you like to send?")
            message = command()

            pwk.sendwhatmsg_instantly(phone_number, message)
            
            time.sleep(5)
            pyautogui.press("enter")
            speak("Message sent successfully.")
            
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
                
        elif "clean data" in request:
            speak("Please say the CSV file name without extension.")
            file_name = command().strip().replace(" ", "")
            file_path = os.path.join(os.getcwd(), f"{file_name}.csv")
            print(file_path)
            clean_data(file_path)
            
        elif "suggest message" in request:
            chat_history = extract_whatsapp_chat()
            reply = generate_reply(chat_history)
            speak(f"Suggested reply: {reply}")
            print(f"Suggested reply: {reply}")
            send_whatsapp_message(reply)
            
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
    try:  # Vosk Model loading within try-except
        q = queue.Queue()
        model = vosk.Model(r"F:\Personal Jarvis\vosk-model-small-en-us-0.15") # Corrected path if necessary
    except Exception as e:
        print(f"Error loading Vosk model: {e}")  # Print detailed error
        speak("There was an error initializing the speech recognition model.")
        exit()
    listen_hotword()
