import datetime
import re


class MedicalRecordSystem:
	def __init__(self, test_file='medicalTest.txt', record_file='medicalRecord.txt'):
		self.test_file = test_file
		self.record_file = record_file
		self.tests = self.load_tests()

	def load_tests(self):
		tests = {}
		with open(self.test_file, 'r') as file:
			for line in file:
				try:
					name, range_str, unit, turnaround_time = line.strip().split(';')
					tests[name] = {
						'range': range_str,
						'unit': unit,
						'turnaround_time': turnaround_time
					}
				except ValueError as e:
					print(f"Skipping line due to format issue: {line.strip()}")
					print(f"Error: {e}")
		return tests

	def add_test(self, test_name, range_str, unit, turnaround_time):
		self.tests[test_name] = {
			'range': range_str,
			'unit': unit,
			'turnaround_time': turnaround_time
		}
		with open(self.test_file, 'a') as file:
			file.write(f"{test_name};{range_str};{unit};{turnaround_time}\n")

	def add_patient_record(self, patient_id, test_name, test_date, result, unit, status, result_date=None):
		with open(self.record_file, 'a') as file:
			if result_date:
				file.write(f"{patient_id}: {test_name}, {test_date}, {result}, {unit}, {status}, {result_date}\n")
			else:
				file.write(f"{patient_id}: {test_name}, {test_date}, {result}, {unit}, {status}\n")

	def update_patient_record(self, patient_id, test_name, new_data):
		records = []
		updated = False
		with open(self.record_file, 'r') as file:
			for line in file:
				if line.startswith(f"{patient_id}: {test_name},"):
					line_parts = line.strip().split(', ')
					line_parts[1] = f" {new_data['test_date']}"
					line_parts[2] = f" {new_data['result']}"
					line_parts[3] = f" {new_data['unit']}"
					line_parts[4] = f" {new_data['status']}"
					if 'result_date' in new_data:
						line_parts.append(f" {new_data['result_date']}")
					records.append(','.join(line_parts) + "\n")
					updated = True
				else:
					records.append(line)

		with open(self.record_file, 'w') as file:
			file.writelines(records)

		if not updated:
			print(f"No record found for Patient ID: {patient_id} and Test Name: {test_name}.")

	def filter_tests(self, patient_id=None, test_name=None, abnormal_only=False,
	                 start_date=None, end_date=None, status=None):
		results = []
		with open(self.record_file, 'r') as file:
			for line in file:
				parts = line.strip().split(', ')
				line_id = parts[0].split(':')[0]
				line_test_name = parts[0].split(': ')[1]

				# Parse test date
				line_date_str = parts[1]
				line_date = datetime.datetime.strptime(line_date_str, '%Y-%m-%d %H:%M:%S')

				line_result = float(parts[2])
				line_unit = parts[3]
				line_status = parts[4]

				# Parse result date if available
				result_date_str = parts[5] if len(parts) > 5 else None
				result_date = datetime.datetime.strptime(result_date_str,
				                                         '%Y-%m-%d %H:%M:%S') if result_date_str else None

				if patient_id and line_id != patient_id:
					continue
				if test_name and line_test_name != test_name:
					continue
				if status and line_status.lower() != status.lower():
					continue
				if start_date and line_date < start_date:
					continue
				if end_date and line_date > end_date:
					continue

				if abnormal_only:
					test_info = self.tests.get(line_test_name)
					if test_info:
						ranges = test_info['range'].split(',')
						min_val = float(ranges[0][1:]) if ranges[0][0] == '>' else None
						max_val = float(ranges[1][1:]) if len(ranges) > 1 and ranges[1][0] == '<' else None

						if (min_val and line_result <= min_val) or (max_val and line_result >= max_val):
							results.append(line.strip())
				else:
					results.append(line.strip())

		return results

	def generate_summary(self, records):
		values = []
		turnaround_times = []

		for record in records:
			fields = record.strip().split(', ')

			if len(fields) < 6:
				print(f"Skipping record due to insufficient fields: {record}")
				continue

			# Extract and validate test value
			try:
				test_value_str = fields[2].strip()  # Assuming test value is in the third position
				test_value = float(test_value_str)
				values.append(test_value)
				print(f"Added test value: {test_value}")
			except ValueError:
				print(f"Invalid test value: {test_value_str}")
				continue

			# Extract and convert turnaround time
			try:
				end_time = datetime.datetime.strptime(fields[1].strip(), '%Y-%m-%d %H:%M:%S')
				start_time = datetime.datetime.strptime(fields[5].strip(), '%Y-%m-%d %H:%M:%S')
				turnaround_time = end_time - start_time
				turnaround_times.append(turnaround_time)
				print(f"Added turnaround time: {turnaround_time}")
			except ValueError:
				print(f"Invalid date format: {fields[1]} or {fields[5]}")
				continue

		# Calculate statistics for test values
		if values:
			min_val = min(values)
			max_val = max(values)
			avg_val = sum(values) / len(values)
		else:
			min_val = max_val = avg_val = None

		# Calculate statistics for turnaround times
		if turnaround_times:
			min_ta = min(turnaround_times)
			max_ta = max(turnaround_times)
			avg_ta = sum(turnaround_times, datetime.timedelta()) / len(turnaround_times)

		#Start with timedelta() = 0 days, 0:00:00
		# 0 days, 0:00:00 + 2 days, 5:30:00 = 2 days, 5:30:00
		#2 days, 5:30:00 + 1 day, 3:45:00 = 3 days, 9:15:00
		#3 days, 9:15:00 + 3 days, 7:15:00 = 6 days, 16:30:00
		else:
			min_ta = max_ta = avg_ta = None

		return {
			'min_val': min_val,
			'max_val': max_val,
			'avg_val': avg_val,
			'min_ta': min_ta,
			'max_ta': max_ta,
			'avg_ta': avg_ta
		}

	def record_exists(self, patient_id, test_name):
		with open(self.record_file, 'r') as file:
			for line in file:
				if line.startswith(f"{patient_id}: {test_name},"):
					return True
		return False


def is_valid_test_name(name):
	return bool(name.strip())


def is_valid_range(range_str):
	# Pattern to match >value, <value, or >value,<value in any order
	pattern = r'^((>(-?\d+(\.\d+)?))?(,(<(-?\d+(\.\d+)?)))?|((<(-?\d+(\.\d+)?))?(,(>(-?\d+(\.\d+)?)))?))$'

	if not re.match(pattern, range_str):
		return False

	# Extract the numeric values for validation
	lower_limit = None
	upper_limit = None

	if '>' in range_str:
		lower_limit_str = re.search(r'>(-?\d+(\.\d+)?)', range_str)
		if lower_limit_str:
			lower_limit = float(lower_limit_str.group(1))

	if '<' in range_str:
		upper_limit_str = re.search(r'<(-?\d+(\.\d+)?)', range_str)
		if upper_limit_str:
			upper_limit = float(upper_limit_str.group(1))

	# Ensure that lower limit is less than upper limit
	if lower_limit is not None and upper_limit is not None:
		if lower_limit >= upper_limit:
			return False

	return True


def is_valid_turnaround_time(ta_time):
	try:
		days, hours, minutes = map(int, ta_time.split('-'))
		return days >= 0 and hours >= 0 and hours < 24 and minutes >= 0 and minutes < 60
	except ValueError:
		return False


def is_valid_status(status):
	valid_statuses = {'pending', 'completed', 'reviewed'}
	return status.lower() in valid_statuses


def is_valid_unit(unit, tests):
	valid_units = {test_info['unit'] for test_info in tests.values()}
	if unit not in valid_units:
		print(f"Invalid unit. Valid units are: {', '.join(valid_units)}")
	return unit in valid_units


def is_valid_patient_id(patient_id):
	return len(patient_id) == 7 and patient_id.isdigit()


def is_valid_result(result_str):
	return bool(re.match(r'^-?\d+(\.\d+)?$', result_str))


def is_valid_date(date_str):
	for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
		try:
			datetime.datetime.strptime(date_str, fmt)
			return True
		except ValueError:
			continue
	return False


def add_or_update_test(system, test_name, range_str, unit, turnaround_time):
	if test_name in system.tests:
		print(f"Test with name {test_name} already exists.")
		return
	if not is_valid_test_name(test_name):
		print("Invalid test name.")
		return
	if not is_valid_range(range_str):
		print("Invalid range format. Use the format: '>value,<value' or 'value,<value'")
		return
	if not is_valid_turnaround_time(turnaround_time):
		print("Invalid turnaround time format. Use 'days-hours-minutes' format.")
		return
	system.add_test(test_name, range_str, unit, turnaround_time)
	print("Test added successfully.")


def add_or_update_patient_record(system, patient_id, test_name, test_date_str, result_str, unit, status,
                                 result_date_str=None):
	if not is_valid_patient_id(patient_id):
		print("Invalid patient ID.")
		return
	if test_name not in system.tests:
		print(f"Test with name {test_name} does not exist.")
		return
	if not is_valid_date(test_date_str):
		print("Invalid test date format.")
		return
	if not is_valid_result(result_str):
		print("Invalid result format.")
		return
	if not is_valid_unit(unit, system.tests):
		print("Invalid unit.")
		return
	if not is_valid_status(status):
		print("Invalid status. Valid statuses are: pending, completed, reviewed.")
		return

	test_date = datetime.datetime.strptime(test_date_str, '%Y-%m-%d %H:%M:%S')
	result = float(result_str)

	if status == 'completed' and result_date_str:
		result_date = datetime.datetime.strptime(result_date_str, '%Y-%m-%d %H:%M:%S')
		if result_date <= test_date:
			print("Result date must be after the test date.")
			return
		turnaround_time = result_date - test_date
	else:
		turnaround_time = None

	if system.record_exists(patient_id, test_name):
		update = input("Record exists. Do you want to update the existing record? (y/n): ").lower()
		if update == 'y':
			system.update_patient_record(patient_id, test_name, {
				'test_date': test_date_str,
				'result': result_str,
				'unit': unit,
				'status': status,
				'result_date': result_date_str
			})
			print("Patient record updated successfully.")
		else:
			print("No changes made.")
	else:
		system.add_patient_record(patient_id, test_name, test_date_str, result_str, unit, status, result_date_str)
		print("New patient record added successfully.")


def test_name_exists(test_name, test_file):
	try:
		with open(test_file, 'r') as file:
			for line in file:
				# Assuming each line starts with the test name followed by a separator
				if line.strip().split(';')[0] == test_name:
					return True
	except FileNotFoundError:
		print(f"Error: The file {test_file} does not exist.")
	return False


def main():
	system = MedicalRecordSystem()

	while True:
		print("~~~~~~~~~~~Medical Record Management System~~~~~~~~~~~")
		print("1. Add a new medical test")
		print("2. Add a new patient record")
		print("3. Update an existing patient record")
		print("4. Update an existing test")
		print("5. Filter and display records")
		print("6. Generate summary report")
		print("7. Exit")
		choice = input("Enter your choice: ")

		if choice == '1':
			test_name = input("Enter test name: ")
			while not is_valid_test_name(test_name):
				test_name = input("Invalid test name. Enter again: ")

			if test_name in system.tests:
				print(f"Test {test_name} already exists. It will be updated.")
				with open(system.test_file, 'r') as file:
					lines = file.readlines()

				with open(system.test_file, 'w') as file:
					for line in lines:
						if not line.startswith(f"{test_name};"):
							file.write(line)
						else:
							print(f"Deleted existing record for test: {test_name}")

			range_str = input("Enter test range (e.g., '>13.8,<17.2'): ")
			while not is_valid_range(range_str):
				range_str = input("Invalid range format. Enter again: ")

			unit = input("Enter test unit: ")

			turnaround_time = input("Enter turnaround time (DD-hh-mm): ")
			while not is_valid_turnaround_time(turnaround_time):
				turnaround_time = input("Invalid turnaround time. Enter again: ")

			system.add_test(test_name, range_str, unit, turnaround_time)
			print("Test updated successfully.")

		elif choice == '2':
			# Add a new patient record
			patient_id = input("Enter patient ID: ")
			while not is_valid_patient_id(patient_id):
				patient_id = input("Invalid patient ID. Enter again: ")

			test_name = input("Enter test name: ")
			if not test_name_exists(test_name, system.test_file):
				print(f"Test with name {test_name} does not exist in {system.test_file}.")
				continue  # Go back to the menu

			test_date_str = input("Enter test date and time (YYYY-MM-DD hh:mm or YYYY-MM-DD hh:mm:ss): ")
			if not is_valid_date(test_date_str):
				print("Invalid test date format. Please enter again.")
				continue  # Go back to the menu

			try:
				test_date = datetime.datetime.strptime(test_date_str, '%Y-%m-%d %H:%M:%S')
			except ValueError:
				try:
					test_date = datetime.datetime.strptime(test_date_str, '%Y-%m-%d %H:%M')
				except ValueError:
					print("Invalid date format. Please enter in 'YYYY-MM-DD hh:mm' or 'YYYY-MM-DD hh:mm:ss' format.")
					continue  # Go back to the menu

			result_str = input("Enter result value: ")
			while not is_valid_result(result_str):
				result_str = input("Invalid result value. Enter again: ")
			result = float(result_str)

			unit = input("Enter result unit: ")
			while not is_valid_unit(unit, system.tests):
				unit = input("Invalid unit. Enter again: ")

			status = input("Enter test status (Pending/Completed/Reviewed): ")
			while not is_valid_status(status):
				status = input("Invalid status. Enter again (Pending/Completed/Reviewed): ")
			status = status.capitalize()

			result_date_str = input("Enter result date (YYYY-MM-DD hh:mm) or press enter to skip: ")
			if result_date_str:
				if not is_valid_date(result_date_str):
					print("Invalid result date format. Please enter in 'YYYY-MM-DD hh:mm' format.")
					continue  # Go back to the menu
				result_date = datetime.datetime.strptime(result_date_str, '%Y-%m-%d %H:%M')
				if result_date <= test_date:
					print("Result date must be after the test date.")
					continue  # Go back to the menu
			else:
				result_date = None

			add_or_update_patient_record(system, patient_id, test_name, test_date_str, result_str, unit, status,
			                             result_date_str)


		elif choice == '3':
			patient_id = input("Enter patient ID: ")
			test_name = input("Enter test name: ")
			test_date_str = input("Enter test date and time (YYYY-MM-DD hh:mm): ")
			test_date = datetime.datetime.strptime(test_date_str, '%Y-%m-%d %H:%M:%S')

			result = input("Enter new result value: ")
			while not is_valid_result(result):
				result = input("Invalid result value. Enter again: ")

			unit = input("Enter new result unit (Expected unit: mg/dL): ")
			while not is_valid_unit(unit, system.tests):
				unit = input(
					f"Invalid unit. Expected one of: {[test['unit'] for test in system.tests.values()]}. Enter again: ")

			status = input("Enter new test status (Pending/Completed/Reviewed): ").lower()
			while not is_valid_status(status):
				status = input("Invalid status. Enter again (Pending/Completed/Reviewed): ").lower()

			end_date = None
			if status == 'completed':
				end_date_str = input("Enter result end date (YYYY-MM-DD hh:mm:ss): ")
				while not is_valid_date(end_date_str):
					end_date_str = input("Invalid date format. Enter again (YYYY-MM-DD hh:mm:ss): ")
				end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')

				while end_date <= test_date:
					end_date_str = input(
						"End date must be greater than start date. Enter new result end date (YYYY-MM-DD hh:mm): ")
					while not is_valid_date(end_date_str):
						end_date_str = input("Invalid date format. Enter again (YYYY-MM-DD hh:mm:ss): ")
					end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')

			add_or_update_patient_record(system, patient_id, test_name, test_date_str, result, unit, status, end_date_str)


		elif choice == '4':
			test_name = input("Enter the name of the test to update: ")

			if test_name in system.tests:
				print(f"Test {test_name} found. It will be updated.")
				with open(system.test_file, 'r') as file:
					lines = file.readlines()

				with open(system.test_file, 'w') as file:
					for line in lines:
						if not line.startswith(f"{test_name};"):
							file.write(line)
						else:
							print(f"Deleted existing record for test: {test_name}")

			else:
				print(f"Test {test_name} not found. A new test will be added.")

			range_str = input("Enter new range (e.g., '>13.8,<17.2'): ")
			while not is_valid_range(range_str):
				range_str = input("Invalid range format. Enter again: ")

			unit = input("Enter new unit: ")

			turnaround_time = input("Enter new turnaround time (DD-hh-mm): ")
			while not is_valid_turnaround_time(turnaround_time):
				turnaround_time = input("Invalid turnaround time. Enter again: ")

			system.add_test(test_name, range_str, unit, turnaround_time)
			print("Test updated successfully.")

		elif choice == '5':
			patient_id = input("Enter patient ID (or leave blank): ")
			if patient_id and not is_valid_patient_id(patient_id):
				print("Invalid patient ID. Filtering without patient ID.")
				patient_id = None

			test_name = input("Enter test name (or leave blank): ")
			if test_name and not is_valid_test_name(test_name):
				print("Invalid test name. Filtering without test name.")
				test_name = None

			abnormal_only = input("Filter abnormal results only? (y/n): ").lower() == 'y'

			start_date = input("Enter start date (YYYY-MM-DD) or leave blank: ")
			if start_date and not is_valid_date(start_date + " 00:00"):
				print("Invalid start date. Filtering without start date.")
				start_date = None
			else:
				start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d') if start_date else None

			end_date = input("Enter end date (YYYY-MM-DD) or leave blank: ")
			if end_date and not is_valid_date(end_date + " 23:59"):
				print("Invalid end date. Filtering without end date.")
				end_date = None
			else:
				end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

			# Ensure end date is greater than start date
			if start_date and end_date and end_date <= start_date:
				print("End date must be greater than start date. Please enter valid dates.")
				continue

			status = input("Enter status to filter (or leave blank): ")
			if status and not is_valid_status(status):
				print("Invalid status. Filtering without status.")
				status = None

			records = system.filter_tests(patient_id, test_name, abnormal_only, start_date, end_date, status)

			for record in records:
				print(record)

		elif choice == '6':
			patient_id = input("Enter Patient ID (or press enter to skip): ")
			test_name = input("Enter Test Name (or press enter to skip): ")
			start_date_str = input("Enter Start Date (YYYY-MM-DD) (or press enter to skip): ")
			end_date_str = input("Enter End Date (YYYY-MM-DD) (or press enter to skip): ")

			start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
			end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

			# Ensure end date is greater than start date
			if start_date and end_date and end_date <= start_date:
				print("End date must be greater than start date. Please enter valid dates.")
				continue

			records = system.filter_tests(patient_id=patient_id, test_name=test_name, start_date=start_date,
			                              end_date=end_date)
			summary = system.generate_summary(records)
			print(summary)

		elif choice == '7':
			print("----End of the Medical Test Management System.")
			break

		else:
			print("Invalid choice, please try again.")


if __name__ == "__main__":
	main()
