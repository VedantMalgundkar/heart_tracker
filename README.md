# API Documentation

This document provides detailed information about the API routes available in the application. Each route is described with its purpose, request format, and example responses.

## Table of Contents

1. [Register User](#register-user)
2. [Login (Get Token)](#login-get-token)
3. [Add Patient](#add-patient)
4. [Add Device](#add-device)
5. [Add Heart Rate Reading](#add-heart-rate-reading)
6. [Get Patients with Latest Heart Rate Readings](#get-patients-with-latest-heart-rate-readings)
7. [Get All Heart Rate Readings for a Patient](#get-all-heart-rate-readings-for-a-patient)
8. [Logout](#logout)

---

## Register User

### Purpose
Register a new user in the system.

### Route
`POST /register`

### Request Format
```
Request

{
  "email": "test123@gmail.com",
  "password": "test123@"
}

Example Response

{
  "message": "User created successfully",
  "user": "test123@gmail.com"
}
```

### Login (Get Token)
Purpose
Authenticate a user and generate access and refresh tokens.


Route

`POST /token`

Request Format

```
Request

{
  "email": "test123@gmail.com",
  "password": "test123@"
}

Example Response

{
  "user": {
    "email": "test123@gmail.com"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0MTIzQGdtYWlsLmNvbSIsImV4cCI6MTczOTM3MTIyOX0.l8S3Wh8NVa2DH0tqXc36clbSJB6FJ0L3KqBEKOAcDHU",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0MTIzQGdtYWlsLmNvbSIsImV4cCI6MTczOTQ1NTgyOX0.-G6hkcyX8OGbRLkp8yvJ6HJ2HyXKGtFZYak5ecqC0Ts"
}
```

### Add Patient

Purpose
Add a new patient to the system.

Route POST 

`/patients/add_patients`

```
Request Format

{
  "name": "vedant Malgundkar",
  "age": 22,
  "gender": "M"
}

Example Response

{
  "id": 1,
  "name": "vedant Malgundkar",
  "age": 22,
  "user_id": 1,
  "device_id": null
}
```

### Add Device

Purpose

Add a new device to the system and associate it with a patient.

Route POST 

`/devices/add_devices`

Request Format
```
{
  "patient_id": 1,
  "status": "Active"
}

Example Response

{
  "patient_id": 1,
  "status": "Active",
  "id": 1,
  "created_at": "2025-02-12T19:42:31.993887Z"
}
```

### Add Heart Rate Reading
Purpose

Add a heart rate reading for a patient using a specific device.

Route POST 

`/heart_readings`

Request Headers `device-id: 1`

Request Format

```
{
  "patient_id": 1,
  "heart_rate": 72
}

Example Response

{
  "patient_id": 1,
  "heart_rate": 72,
  "id": 3,
  "device_id": 1,
  "recorded_at": "2025-02-12T19:47:43.731487Z"
}
```


### Get Patients with Latest Heart Rate Readings

Purpose

Fetch details of all patients along with their two latest heart rate readings.

Route GET 

`/patients/get-patients`

```
Example Response

[
  {
    "id": 1,
    "name": "vedant Malgundkar",
    "age": 22,
    "gender": "M",
    "user_id": 1,
    "created_at": "2025-02-12T19:41:40.866153Z",
    "heart_rate_readings": [
      {
        "patient_id": 1,
        "heart_rate": 72,
        "id": 3,
        "device_id": 1,
        "recorded_at": "2025-02-12T19:47:43.731487Z"
      },
      {
        "patient_id": 1,
        "heart_rate": 80,
        "id": 2,
        "device_id": 1,
        "recorded_at": "2025-02-12T19:44:23.285198Z"
      }
    ]
  }
]
```

### Get All Heart Rate Readings for a Patient

Purpose

Fetch all heart rate readings for a specific patient.

Route GET 

`/heart-readings/{patient_id}`


```
Example Response

{
  "id": 1,
  "name": "vedant Malgundkar",
  "age": 22,
  "gender": "M",
  "user_id": 1,
  "created_at": "2025-02-12T19:41:40.866153Z",
  "heart_rate_readings": [
    {
      "patient_id": 1,
      "heart_rate": 72,
      "id": 3,
      "device_id": 1,
      "recorded_at": "2025-02-12T19:47:43.731487Z"
    },
    {
      "patient_id": 1,
      "heart_rate": 80,
      "id": 2,
      "device_id": 1,
      "recorded_at": "2025-02-12T19:44:23.285198Z"
    },
    {
      "patient_id": 1,
      "heart_rate": 75,
      "id": 1,
      "device_id": 1,
      "recorded_at": "2025-02-12T19:44:03.405574Z"
    }
  ],
  "device_id": 1
}
```

### Logout

Purpose
Log out the current user by invalidating the refresh token.

Route

`POST /logout`

```
Example Response

{
  "message": "Logged out successfully"
}
```

This concludes the API documentation. Each route is designed to handle specific functionalities within the application, ensuring a seamless experience for managing users, patients, devices, and heart rate readings.