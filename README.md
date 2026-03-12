# Pantry Planner

Pantry Planner is a web application that helps users discover recipes using ingredients they already have at home. By selecting ingredients from a list, users can quickly find recipes that match their pantry and reduce unnecessary grocery trips.

The application integrates with **TheMealDB API** to retrieve recipe information and allows users to bookmark recipes and maintain a grocery list.

---

# Features

- Ingredient browser with search (`/ingredients`)
- User authentication
  - Register
  - Login
  - Logout
- Recipe bookmarking
- Grocery list with:
  - add / remove items
  - check / uncheck
  - print view
- Admin panel
  - ingredient sync
  - user management
  - pantry edits
  - ingredient blacklist

---

# Tech Stack

## Backend
- Python
- Flask

## Database
- SQLite

## External API
- TheMealDB API

## Tools
- GitHub (version control)
- GitHub Projects (task tracking)
- PyTest / unittest (testing)
- GitHub Actions (CI automation)

---

# Quickstart

## 1. Clone the Repository

git clone https://github.com/PiFusion/Pantry-Planner.git
cd Pantry-Planner


---

## 2. Create Virtual Environment

python -m venv .venv

---

## 3. Install Dependencies

pip install -r requirements.txt


---

## 4. Initialize the Database

flask --app pantry_planner init-db
flask --app pantry_planner sync-ingredients


---

## 5. Run the Application

flask --app pantry_planner run --debug


Open in browser:

http://127.0.0.1:5000/ingredients


---

# Admin Setup

By default, newly registered users are created with the role **user**.

To promote a user to admin:

flask --app pantry_planner make-admin


Enter the username you registered with.

Admin users can access:

/admin


Admin actions include confirmation prompts for destructive changes.

---

# Usage Notes

- Anonymous users can browse ingredients, but selections are stored in session only.
- Logged-in users get persistent pantry selections, bookmarks, and grocery lists.
- The grocery list page appears only for logged-in users.
- Admin tools allow managing users and ingredient data.

---

# Product Vision

Pantry Planner provides a simple and efficient way for users to discover meals using ingredients they already own.

The goal is to reduce wasted food and eliminate the need to search through large recipe sites when trying to decide what to cook.

The system focuses on **ingredient-based recipe discovery**, allowing users to quickly find meals they can prepare with what they already have.

---

# Target Users

Pantry Planner is designed for:

- Home cooks looking for quick meal ideas
- Users trying to reduce food waste
- People who want to organize ingredients and grocery lists
- Anyone looking for recipes based on available ingredients

---

# Stakeholders

- Application users
- Development team
- Product owner
- Course instructor

---

# Project Goals

The main goals of Pantry Planner are:

- help users discover recipes using existing ingredients
- reduce time spent searching for recipes
- allow users to bookmark favorite meals
- provide a simple grocery list tool
- demonstrate collaborative software development using Scrum

---

# Release Plan

## Sprint 1

Goal: Project setup and ingredient selection.

Completed tasks:
- Flask application setup
- GitHub repository creation
- database initialization
- ingredient selection interface

---

## Sprint 2

Goal: Recipe discovery functionality.

Completed tasks:
- TheMealDB API integration
- recipe matching logic
- recipe filtering and sorting

---

## Sprint 3

Goal: User accounts and interface improvements.

Completed tasks:
- authentication system
- bookmarking recipes
- recipe details page
- UI styling improvements

---

## Sprint 4

Goal: Final features and stabilization.

Completed tasks:
- grocery list feature
- bug fixes
- testing
- documentation

---

# Coding Standards

The project follows the **PEP8 Python style guide**.

Standards used:

- snake_case naming conventions
- descriptive variable names
- modular Flask structure
- consistent indentation
- comments for complex logic

These standards ensure readable and maintainable code.

---

# Documentation Standards

Documentation includes:

- README instructions
- inline comments in source code
- sprint reports documenting development progress

---

# Development Environment

The application was developed using:

- Python 3.x
- Flask
- SQLite
- GitHub
- GitHub Projects for task management

---

# Deployment Environment

The application runs on desktop environments with Python installed.

Recommended environment:

- Python 3.10+
- Flask
- SQLite
- modern web browser

The application currently runs locally using the Flask development server.

---

# Version Management

Version control is handled using **Git and GitHub**.

Workflow:

1. create feature branch
2. implement feature
3. open pull request
4. review changes
5. merge into main branch

---

# Architectural Design

Pantry Planner follows a **Flask-based MVC-style architecture**.

### Frontend

HTML templates rendered with Flask.

### Backend

Flask routes process user requests and business logic.

### Database

SQLite stores user accounts, bookmarks, pantry selections, and grocery lists.

### External Services

TheMealDB API provides recipe and ingredient data.

---

# Detailed Design

Project structure:

pantry_planner/
│
├── auth/
├── recipes/
├── grocery/
├── bookmarks/
├── admin/
│
├── db.py
└── init.py


Each module handles a specific portion of the application.

---

# Database Design

## Users

Stores account information.

Fields:

- id
- username
- password_hash
- role

---

## Bookmarks

Stores saved recipes.

Fields:

- id
- user_id
- recipe_id

---

## Pantry

Stores ingredients selected by a user.

Fields:

- user_id
- ingredient_id

---

## Grocery List

Stores grocery list items.

Fields:

- user_id
- ingredient
- checked

---

# UI / UX Design

The interface was designed to be simple and easy to navigate.

Design goals:

- quick ingredient selection
- clear recipe results
- minimal navigation complexity
- consistent layout across pages

---

# Test Plan

Testing was performed using **PyTest and unittest**.

## Test Types

- unit tests for backend logic
- route testing for Flask endpoints
- authentication tests
- database interaction tests

## Running Tests

python -m unittest discover -s tests -v


---

# Change Management

GitHub Issues were used to track bugs and feature requests.

Workflow:

1. issue created
2. feature branch created
3. code implemented
4. pull request submitted
5. review performed
6. merge into main branch

---

# Definition of Ready

A user story is ready when:

- the feature is clearly described
- acceptance criteria exist
- dependencies are identified
- the task can be completed within a sprint

---

# Definition of Done

A task is complete when:

- feature is implemented
- application runs without errors
- tests pass successfully
- code is pushed to GitHub
- pull request is reviewed and merged

---
# Running Tests

python -m unittest discover -s tests -v

---

# Team Members

- Garrett Hutchinson
- Noah Williams
- Toby Crabtree
- Chloe Fenner
- Joseph Rutherford
