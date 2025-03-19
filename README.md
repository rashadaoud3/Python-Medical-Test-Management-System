# Python Medical Test Management System

## Description

This project implements a Python-based Medical Test Management System that stores, manages, and retrieves medical test data for individual patients. The system supports a variety of operations such as adding, updating, deleting test records, and retrieving specific test results based on patient ID or test type. It uses object-oriented Python code with a dictionary to store patients' information.

Medical records are stored in a text file named `medicalRecord`, where each line represents a single test. Another file, `medicalTest`, contains details about each test including the normal range, unit, and turnaround time.

## Objective

- Develop a system to efficiently store, manage, and retrieve medical test data for individual patients.
- The system includes functionalities like adding new test results, updating records, deleting outdated entries, filtering tests, generating summary reports, and exporting/importing medical records.
- The system is built using object-oriented Python programming principles, with error handling and data validation.

## Features

- Add, update, and delete medical test records.
- Filter medical tests by multiple criteria such as:
  - Patient ID
  - Test Name
  - Abnormal tests
  - Test status
  - Turnaround time
- Generate summary reports with descriptive statistics such as:
  - Minimum, maximum, and average test values
  - Minimum, maximum, and average turnaround time
- Import and export medical records in CSV format.
- Store medical tests in a dictionary where the patient ID is used as the key.
- Input validation for all user entries.
- Error handling for invalid inputs and file handling errors.


