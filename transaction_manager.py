import os
import csv
from datetime import datetime
from PIL import Image
import cv2
import time
import pandas as pd
import sqlite3
import shutil
import random


class TransactionManager:
    def __init__(self):
        self.base_directory = 'transaction_manager_data'
        self.transaction_directory = None
        self.transactions = []

    def create_customer_directory(self, customer_name):
        customer_directory = os.path.join(self.base_directory, customer_name)
        os.makedirs(customer_directory, exist_ok=True)
        return customer_directory

    def initialize_transaction_files(self):
        self.transaction_directory = os.path.join(self.base_directory, 'transaction_files')
        os.makedirs(self.transaction_directory, exist_ok=True)

    def write_transaction_data(self):
        if not self.transaction_directory:
            self.initialize_transaction_files()
        serial_number = str(len(self.transactions)).zfill(6)
        now = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f'transaction_{serial_number}.csv'
        file_path = os.path.join(self.transaction_directory, file_name)
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Product Name', 'Payment Amount', 'Serial Number', 'Date', 'Details'])
            for transaction in self.transactions:
                writer.writerow([transaction['Product'], transaction['Payment'], serial_number, now, transaction['Details']])
        return serial_number, now, file_path

    def display_bill(self, serial_number, now):
        total = sum(transaction['Payment'] for transaction in self.transactions)
        print("Bill Details")
        print("------------")
        print(f"Serial Number: {serial_number}")
        print(f"Date: {now}")
        print("Product Name\tPayment Amount\tDetails")
        print("------------\t--------------\t-------")
        for transaction in self.transactions:
            print(f"{transaction['Product']}\t\t{transaction['Payment']}\t\t{transaction['Details']}")
        print("------------\t--------------\t-------")
        print(f"Total\t\t{total}")
        print("Thank you for your purchase!")

    def open_payment_scanner_image(self):
        img_payment_scanner = Image.open("payment_scanner_image.jpg")
        img_payment_scanner.show()

    def capture_customer_face(self, customer_name, customer_directory):
        cam = cv2.VideoCapture(0)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        start_time = time.time()
        count = 1
        while True:
            ret, frame = cam.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            current_time = time.time()
            elapsed_time = current_time - start_time
            if elapsed_time >= 3:
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    roi_color = frame[y:y + h, x:x + w]
                    file_name = f"{customer_name}_face_{count}.jpg"
                    file_path = os.path.join(customer_directory, file_name)
                    cv2.imwrite(file_path, roi_color)
                    print(f"Customer's image saved at: {file_path}")
                    count += 1
                    break
            cv2.imshow('Face Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q') or count > 5:
                break
        cam.release()
        cv2.destroyAllWindows()

    def read_csv_using_sql(self, file_path):
        data = pd.read_csv(file_path)
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        data.to_sql('transactions', conn, index=False)
        query = 'SELECT * FROM transactions'
        result = cursor.execute(query).fetchall()
        print("Data from CSV file using SQL")
        for row in result:
            print(row)
        conn.close()

    def add_transaction(self, product_name, payment, details):
        try:
            payment = float(payment)
            self.transactions.append({'Product': product_name, 'Payment': payment, 'Details': details})
            print("Transaction added successfully.")
        except ValueError:
            print("Invalid payment amount. Please enter a valid number.")

    def perform_transaction(self):
        self.initialize_transaction_files()
        while True:
            product_name = input("Enter product name (or 'done' to finish): ")
            if product_name.lower() == 'done':
                break
            payment = input("Enter payment amount: ")
            additional_details = input("Enter additional details: ")
            self.add_transaction(product_name, payment, additional_details)
        if self.transactions:
            serial_number, now, file_path = self.write_transaction_data()
            self.display_bill(serial_number, now)
            self.open_payment_scanner_image()
            customer_name = input("Enter customer name: ")
            customer_directory = self.create_customer_directory(customer_name)
            self.capture_customer_face(customer_name, customer_directory)
            print("\nFiles and Data Locations:")
            print(f"Transaction Data: {file_path}")
            print(f"Customer Directory: {customer_directory}")
            self.read_csv_using_sql(file_path)
        else:
            print("No transactions were added.")


if __name__ == "__main__":
    tm = TransactionManager()
    tm.perform_transaction()
