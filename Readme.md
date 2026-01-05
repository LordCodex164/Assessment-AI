# 🎓 Mini Assessment Engine - Acad AI Backend

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14+-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


---

## 🏗️ Architecture

# Mini Acad Engine API

A RESTful assessment platform for managing courses, exams, questions, student submissions, and automated grading. Built with **Django REST Framework (DRF)**, secured using **JWT authentication**, and designed with role-based access control for **students** and **staff**.

---

## ✨ Features

### Core Functionality
- 🔐 **JWT Authentication** - Secure token-based authentication system
- 👥 **Role-Based Access Control** - Separate permissions for students and staff
- 📚 **Course Management** - Organize exams by courses
- 📝 **Exam Creation** - Staff can create exams with multiple question types
- ✍️ **Secure Submissions** - Students can submit answers with validation
- 🤖 **Automated Grading** - AI-powered evaluation with multiple grading strategies
- 📊 **Real-time Results** - Instant feedback and detailed scoring
- 🔍 **Submission Tracking** - Complete audit trail of all submissions

### Advanced Features
- **Multiple Question Types** - Essay, MCQ, Short Answer support
- **Flexible Grading** - Mock algorithms (keyword matching, TF-IDF) or LLM integration
- **Permission System** - Students can only view their own submissions
- **Comprehensive API** - RESTful endpoints for all operations
- **Admin Interface** - Django admin for easy management


## Table of Contents

* [Overview](#overview)
* [Technology Stack](#technology-stack)
* [Base URL](#base-url)
* [Authentication](#authentication)
* [User Roles](#user-roles)
* [API Modules](#api-modules)

  * [Courses](#courses-module)
  * [Exams](#exams-module)
  * [Submissions](#submissions-module)
* [Error Handling](#error-handling)
* [Data Models](#data-models)
* [Local Development](#local-development)
* [Deployment](#deployment)

---

## Overview

Mini Acad Engine is an assessment engine that allows educational platforms to:

* Manage courses and exams
* Create and attach questions to exams
* Allow students to submit exams
* Automatically grade submissions
* Track scores, percentages, and grading status

The API is versioned and designed to be consumed by web or mobile clients.

---

## Technology Stack

* **Backend**: Django, Django REST Framework
* **Authentication**: JWT (JSON Web Tokens)
* **Database**: PostgreSQL (SQLite for local dev)
* **Deployment**: Render

---

## Base URL

```
https://assessment-ai-1.onrender.com
```

Current API Version: **v1.0**

---

## Authentication

### JWT Token Authentication

All protected endpoints require a valid JWT access token.

**Header format:**

```
Authorization: Bearer <access_token>
```

### Register User

**Endpoint:** `POST /auth/register`

```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "user_type": "student"
}
```

**Response:** `201 Created`

---

### Login

**Endpoint:** `POST /auth/login`

```json
{
  "email": "string",
  "password": "string"
}
```

**Response:** `200 OK`

Returns user details and JWT access/refresh tokens.

---

## User Roles

| Role    | Permissions                                            |
| ------- | ------------------------------------------------------ |
| Student | Take exams, submit answers, view own submissions       |
| Staff   | Create courses, exams, questions, view all submissions |

---

## API Modules

## Courses Module

### List All Courses

**Endpoint:** `GET /courses/`

**Authentication:** Required

**Response:** `200 OK`

---

### Get Course Details

**Endpoint:** `GET /courses/{id}/`

Returns course details and associated exams.

---

### Create Course (Staff Only)

**Endpoint:** `POST /courses/`

```json
{
  "name": "string",
  "code": "string",
  "description": "string"
}
```

---

## Exams Module

### Get All Exams

**Endpoint:** `GET /exams/all`

**Query Params:**

* `course_id` (optional)

---

### Get Exam Details

**Endpoint:** `GET /exams/{examId}`

Returns exam metadata and attached questions.

---

### Create Exam (Staff Only)

**Endpoint:** `POST /exams/create`

```json
{
  "course": 1,
  "title": "Jamb Exam",
  "duration_minutes": 60,
  "questions": [
    {
      "text": "What is Python?",
      "question_type": "essay",
      "expected_answer": "Python is a programming language",
      "marks": 10
    }
  ]
}
```

---

### Add Question to Exam (Staff Only)

**Endpoint:** `POST /exams/{examId}/questions`

---

## Submissions Module

### Submit Exam (Student Only)

**Endpoint:** `POST /exams/submissions`

```json
{
  "exam_id": 1,
  "answers": [
    {
      "question_id": 1,
      "answer_text": "Python is a programming language",
      "question_type": "essay"
    }
  ]
}
```

---

### Get All Submissions

**Endpoint:** `GET /exams/submissions`

**Query Params:**

* `exam_id` (optional)
* `student_id` (staff only)

---

### Get Submission Details

**Endpoint:** `GET /exams/submissions/{submissionId}`

Students can only view their own submissions.

---

### Get Answers for a Submission

**Endpoint:** `GET /exams/submissions/{submissionId}/answers`

---

## Error Handling

All errors follow a consistent structure:

```json
{
  "success": false,
  "message": "Error description",
  "errors": {}
}
```

Common HTTP status codes:

* `400` Bad Request
* `401` Unauthorized
* `403` Forbidden
* `404` Not Found
* `500` Internal Server Error

---

## Data Models (High Level)

* **User** (Django built-in, extended with `user_type`)
* **Course**
* **Exam**
* **Question**
* **Submission**
* **Answer**

Relational integrity is enforced via foreign keys.

---

## Local Development

```bash
git clone https://github.com/your-username/assessment-ai.git
cd mini-acad-engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## Deployment

The API is deployed on **Render**.

Environment variables:

* `SECRET_KEY`
* `DATABASE_URL`
* `DEBUG`
* `JWT_SECRET`

---

## License

MIT License

---

## Maintainer

Built and maintained by **Daniel Adeniran**.
