# Superjoin Hiring Assignment

## Objective
Build a solution that enables real-time synchronization of data between a Google Sheet and a specified database (e.g., MySQL, PostgreSQL). The solution detects changes in the Google Sheet and updates the database accordingly, and vice versa.

## Problem Statement
Many businesses use Google Sheets for collaborative data management and databases for robust and scalable data storage. However, keeping the data synchronized between Google Sheets and databases is often a manual and error-prone process. This project automates this synchronization, ensuring that changes in one are reflected in the other in real-time.

## Requirements
1. **Real-time Synchronization**
   - Implement a system that detects changes in Google Sheets and updates the database accordingly.
   - Similarly, detect changes in the database and update the Google Sheet.

2. **CRUD Operations**
   - Support Create, Read, Update, and Delete operations for both Google Sheets and the database.
   - Maintain data consistency across both platforms.

## Technology Stack
- **Flask**: A lightweight WSGI web application framework for Python.
- **MySQL**: A popular relational database management system for storing and managing data.
- **Google Sheets API**: Enables interaction with Google Sheets for reading and writing data.
- **MySQL Connector**: Provides connectivity between the Flask application and the MySQL database.

## Inventory Management System
I have created an inventory management system with three sheets in Google Sheets and corresponding tables in MySQL. The system is connected through Google Sheets credentials. 

### Features
- Users can add items and delete items using MySQL, Flask, or Google Sheets.
- All operations maintain data consistency across the three platforms.

## Setup Instructions
1. Clone this repository:
   ```bash
   git clone <repository-url>
