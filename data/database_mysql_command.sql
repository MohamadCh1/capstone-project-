create database diabetes;

use diabetes;

CREATE TABLE doctors (
  email VARCHAR(255) PRIMARY KEY,
  name VARCHAR(255),
  specialty VARCHAR(100),
  license_number VARCHAR(100) UNIQUE,
  is_verified BOOLEAN DEFAULT FALSE,
  is_available BOOLEAN DEFAULT TRUE,
  monthly_rate DECIMAL(10,2)
);

CREATE TABLE patients (
  email VARCHAR(255) PRIMARY KEY,
  name VARCHAR(255),
  age INT,
  gender VARCHAR(50),
  ethnicity VARCHAR(100),
  doctor_email VARCHAR(255),
  risk_category ENUM('none', 'low', 'medium', 'high'),
  is_admin BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (doctor_email) REFERENCES doctors(email)
);

CREATE TABLE devices (
  serial_number VARCHAR(100) PRIMARY KEY,
  patient_email VARCHAR(255),
  device_type VARCHAR(50),
  manufacturer VARCHAR(100),
  model VARCHAR(100),
  is_active BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (patient_email) REFERENCES patients(email)
);

CREATE TABLE suggestions (
  id CHAR(36) PRIMARY KEY,
  patient_email VARCHAR(255),
  source_type VARCHAR(50),
  category VARCHAR(50),
  details JSON,
  priority ENUM('none', 'low', 'medium', 'high', 'critical'),
  status ENUM('pending', 'acknowledged', 'accepted', 'dismissed'),
  FOREIGN KEY (patient_email) REFERENCES patients(email)
);
