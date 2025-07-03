# 🎓 University Programming Course Platform – System Documentation

This document provides a comprehensive overview of the software system designed to support programming courses at universities. The platform facilitates student submissions, automated testing, and course content management, while offering tools for lecturers, tutors, and students alike.

---

## 📌 Overview

The platform is tailored to the needs of academic programming courses and supports structured content delivery, student evaluation, and seamless integration with Git-based workflows. Key features include:

- A robust backend for course and user management
- Deep GitLab integration for version control and assignment storage
- A Visual Studio Code extension for role-specific workflows
- A React-based Web UI for dashboards and administrative tools
- Automated test infrastructure for evaluating student submissions

---

## 🏗️ System Architecture

The system is composed of several loosely coupled components, each responsible for specific functionality:

- **Backend**: Implemented in Python using FastAPI. Handles business logic, database access, and API routing.
- **Database**: PostgreSQL is used to persist all structured data. Redis serves as a cache layer.
- **Background Task Management**: Long-running tasks, such as automated testing, are orchestrated using Prefect 2.
- **Storage Layer**: GitLab is used as the primary storage backend for repositories and course content. The architecture is designed to support other Git-based systems in the future.
- **VSCode Extension**: Written in TypeScript, the extension provides a rich UI for students, tutors, and lecturers within their IDE (separate Repository, url coming soon).
- **Web Dashboard**: A React application (early in development) to visualize user progress, view metrics, and offer admin functionality.

---

## 🐍 Backend

The backend is the core of the system, providing RESTful APIs and managing the connection between users, course content, and GitLab repositories.

### Key Technologies

- **FastAPI** for high-performance HTTP services
- **PostgreSQL** for persistent structured data
- **Redis** for caching
- **Prefect 2** for orchestrating background tasks (e.g., tests, cloning repositories)

The backend is also responsible for authenticating users via their GitLab Personal Access Tokens (GLPATs) and managing course-related data models.

---

## 🧩 Visual Studio Code Extension

The Visual Studio Code extension serves as the main interface for most users. It is built using TypeScript and offers different views based on the user’s role:

- **Student View**: Students can log in with their GitLab credentials and interact with their cloned repository. They can also trigger automated tests on their submissions.
- **Tutor View**: Tutors have access to submission lists, can provide feedback, and use filters to work with specific course groups.
- **Lecturer View**: Designed for course administrators and teaching assistants who create and manage assignments. New units and assignments can be created directly through the extension, which recognizes directory structures and `meta.yaml` configuration files.

---

## 🖥️ Web UI

The web interface is implemented in React and TypeScript and is intended to serve as a dashboard for all user roles.

### Current and Planned Features

- Role-based dashboards with individualized progress tracking
- Administrative tools for managing courses and users
- Visual metrics and analytics
- Flexible filtering and navigation

Although still in early stages, the dashboard is designed to complement the VSCode interface with broader overviews and aggregated data.

---

## 🗃️ Database Model

The database schema is structured around the hierarchical organization of academic institutions and their courses.

### Hierarchy

- **Organizations**: Represent university departments or institutes. Each organization defines its GitLab group and access tokens.
- **Course Categories**: Represent recurring course formats (e.g., a lecture held every summer semester).
- **Courses**: Specific course instances tied to a semester (e.g., “Programming 101 – Winter 2024”).

This hierarchy is mirrored in GitLab as nested groups:

Organization → Course Category → Course → Projects


### Projects

Each course typically includes several GitLab projects. The most important is:

- **`assignments`**: A project containing all course content, organized into `units` and `assignments`.

These content items are defined both in the Git repository structure and in the database using the `CourseContent` model.

---

## 📁 Course Content & Structure

Course content is represented using a hierarchical model stored in the database with PostgreSQL's `ltree` type.

### Course Content Types

- **Units**: Logical groupings, e.g., "Week 1". Can contain other units or assignments.
- **Assignments**: The actual tasks to be completed by students.
- **Folders & Quizzes**: Additional planned types.

Each content node is configured using a `meta.yaml` file. These files define metadata such as:

- Title and description
- Type (e.g., unit, assignment)
- Custom tags and icons (e.g., `mandatory`, `weekly`)
- Properties for future grading logic

The system allows deep nesting of units, while assignments can only exist under the root or directly under a unit.

---

## 🧪 Automated Testing Infrastructure

**Important Note**: Both testing infrastructures **are not included** in the github repository yet. They will be added as soon as possible.

Automated tests are handled by Prefect flows and run on dedicated worker nodes. Two test systems are currently supported:

### Python

- Implemented as a native Prefect flow
- Executes tests written in Python

### MATLAB

- MATLAB runs as a background daemon on the Prefect worker node
- Python communicates with the daemon using **Pyro5**
- Test execution is handled by the MATLAB Python Engine

### Test Workflow

1. The student’s solution is cloned using their personal GitLab token.
2. The reference solution (if applicable) is cloned using the organization's token.
3. Both repositories are provided to the test system in a temporary directory.
4. The test is executed and results are returned.

All test systems follow a common interface for input and output, ensuring modularity and extensibility.

---

## 🔐 Authentication & User Management

The platform includes a flexible user model with support for multiple GitLab accounts.

### Data Model

- **User**: Core user profile.
- **Account**: Links a user to a GitLab account, storing username and host.

### Course Membership

Users can join one or more courses and are assigned to course-specific groups:

- **CourseGroup**: Represents practical groups or lecture slots (e.g., "Group A1").
- Tutors and lecturers can use this grouping to filter student lists and manage grading.

### Authentication Flow

- Authentication is performed via GitLab Personal Access Tokens (GLPATs).
- Tokens are sent in API headers and validated against stored account data.

---

## 🔮 Future Features & Extensions

The following enhancements are planned or partially implemented:

- Full-featured Web UI with interactive dashboards and course management
- Support for alternative Git-based storage systems (e.g., GitHub)
- Additional testing backends for other programming languages (e.g., Java, C++)

---

## 📝 License & Contribution

This project is licensed under the [MIT License](../LICENSE).

Contributions are very welcome!
If you have ideas, suggestions, or improvements:
- Feel free to open an Issue
- Or submit a Pull Request

---