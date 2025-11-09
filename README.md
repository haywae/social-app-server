# **Backend Application README**

This is the backend server for a modern, secure web application. It is built with **Python 3.10+** and the **Flask** micro-framework.

It provides a robust RESTful API, real-time WebSocket communication via **Flask-SocketIO**, and a high-security, stateful authentication system. It is designed to integrate with a PostgreSQL database (with PostGIS), Redis, Amazon S3, and SendGrid for email.

## **🚀 Core Technologies**

* **Framework:** Flask  
* **Language:** Python 3.10+  
* **Web Server (Prod):** Gunicorn with Gevent (for async WebSockets)  
* **Real-time:** Flask-SocketIO (with Redis message queue)  
* **Authentication:** Flask-JWT-Extended (with rotating refresh tokens)  
* **Database:** PostgreSQL  
* **DB Extension:** PostGIS (for geospatial data)  
* **DB Migrations:** Flask-Migrate  
* **Caching:** Redis (for token blocklisting & Socket.IO message queue)  
* **File Storage:** Amazon S3 (managed with Boto3)  
* **Email Service:** SendGrid  
* **Containerization:** Docker

## **🏛️ Architecture Overview**

This backend is built using the **Application Factory** pattern in Flask (create\_app in \_\_init\_\_.py) for a clean, modular, and testable structure.

* **Application Factory (\_\_init\_\_.py):** This is the core of the app. It creates a Flask app instance, loads configuration from config.py, and initializes all necessary extensions (like db, jwt, socketio). It also sets up CORS and environment-aware JWT cookie policies (e..g., Secure and SameSite=None for production).  
* **Configuration (config.py):** All configuration is loaded from environment variables using a central Config class. This includes database URLs, API keys for S3/SendGrid, and JWT secrets.  
* **Extensions (extensions.py):** All Flask extensions (SQLAlchemy, JWTManager, SocketIO, Mail, Migrate) are instantiated in this single file. This prevents circular imports and keeps the app factory clean. A redis\_client is also instantiated here for direct Redis operations.  
* **Entrypoint (run.py):** This file is the main entrypoint for running the application. It imports create\_app and socketio, patches I/O with gevent.monkey.patch\_all(), and starts the server using socketio.run(), which is necessary for development.  
* **Production Server (start.sh & Dockerfile):**  
  * In production, the app is containerized via the Dockerfile, which sets up a secure, non-root Alpine environment.  
  * The container's entrypoint is start.sh. This robust script performs several critical startup tasks:  
   1. **Waits for Services:** It uses pg\_isready and redis-cli ping to ensure the database and cache are fully available before proceeding.  
   2. **Runs Migrations:** It automatically applies database migrations by calling flask db upgrade.  
   3. **Starts Server:** It launches the application using gunicorn with geventwebsocket workers (-k geventwebsocket.gunicorn.workers.GeventWebSocketWorker). This is essential for handling high-concurrency and asynchronous WebSocket traffic efficiently.  
* **Real-time Layer (messaging\_events.py):**  
  * Flask-SocketIO is configured to use the REDIS\_URL as its message\_queue. This allows multiple Gunicorn workers (and multiple server instances) to communicate and broadcast events to all users.  
  * **WebSocket Auth:** Connection is not automatic. The @socketio.on('connect') handler in messaging\_events.py acts as a security checkpoint. It manually extracts the access\_token\_cookie, decodes it with pyjwt to verify its signature, checks if the user exists in the database, and only then allows the connection and joins the user to a private, user-specific room (e.g., join\_room(f"user\_{user\_id}")).

## **🧱 Application Logic (3-Layer Design)**

The application's request handling logic is structured into a clean 3-layer pattern: **Resources**, **Services**, and **Models**. This separation of concerns makes the code more modular, testable, and maintainable.

1. **Resource Layer (e.g., login\_resource.py, profile\_picture\_resource.py)**  
   * **Role:** The API endpoint layer, built using flask\_restful.Resource.  
   * **Responsibilities:**  
     * Defines the HTTP methods (get, post, delete, etc.).  
     * Parses incoming request data (e.g., request.get\_json(), request.files).  
     * Handles authentication and user identity (get\_jwt\_identity()).  
     * Translates service layer outcomes into HTTP responses (e.g., return {'message': '...'}, 404).  
     * Manages the database session lifecycle (db.session.commit(), db.session.rollback()).  
   * It acts as a thin **controller** that delegates all business logic to the service layer.  
2. **Service Layer (e.g., app.services.login\_user, app.services.update\_profile\_picture\_service)**  
   * **Role:** The core business logic layer.  
   * **Responsibilities:**  
     * Contains all complex logic (e.g., validating a password, processing a file for S3, creating notifications).  
     * Is framework-agnostic (pure Python) and has no knowledge of HTTP or flask.  
     * Receives data (like user\_id, file) and the db.session from the Resource layer.  
     * Interacts with the Model layer to fetch or save data.  
     * Communicates success or failure by returning data or raising custom exceptions (e.g., InvalidCredentialsError, UserNotFoundError), which the Resource layer then catches.  
3. **Model Layer (e.g., app.models.User, app.models.Notification)**  
   * **Role:** The data abstraction layer, built using SQLAlchemy.  
   * **Responsibilities:**  
     * Defines the database schema as Python classes.  
     * Handles table relationships, data types, and constraints.  
     * Provides the interface (db.session) for the service layer to perform Create, Read, Update, and Delete (CRUD) operations on the database.

This flow (Resource \-\> Service \-\> Model) ensures that HTTP concerns are isolated in the Resource layer, business logic is isolated in the Service layer, and data structure is isolated in the Model layer.

## **🛡️ Authentication System Overview**

This application implements a high-security, stateful, cookie-based authentication system. It is built on a **"Double Submit Cookie"** pattern for CSRF protection and uses **rotating refresh tokens** with server-side blocklisting to ensure a high level of security.

* **Secure Cookie Storage:** All JWTs (both access and refresh tokens) are stored in **HttpOnly cookies**. This makes them inaccessible to client-side JavaScript, mitigating the risk of XSS attacks.  
* **CSRF Protection (Double Submit Cookie):**  
  * To protect against CSRF attacks, the system complements the HttpOnly cookies with separate CSRF tokens.  
  * Upon login or refresh, the server sends csrf\_access\_token and csrf\_refresh\_token in the JSON response body.  
  * The frontend client is required to read these tokens and send one back in the **X-CSRF-TOKEN** header with every request. The backend validates this header against the JWT cookie to authorize the request.  
* **High-Security Token Rotation:**  
  * To prevent token replay attacks, the system employs token rotation.  
  * When the /refresh-token endpoint is successfully used, the backend immediately **blocklists the incoming refresh token in a Redis database**.  
  * It then issues a brand new set of access and refresh tokens. This ensures that each refresh token is single-use.  
* **Stateful Logout:**  
  * Logging out is a server-side action. The /logout endpoint **blocklists the user's active access token** for its remaining duration.  
  * This ensures that even if a token is stolen, it is invalidated immediately upon logout.  
* **WebSocket Authentication:**  
  * As detailed in the architecture overview, Socket.IO connections are authenticated manually on connect. The handler (messaging\_events.py) decodes the access\_token\_cookie to verify the user's identity before establishing the real-time connection.

## **🚀 Getting Started (Local Setup)**

### **Prerequisites**

* Python 3.10  
* A running PostgreSQL server  
* The **PostGIS** extension must be installed and enabled on your PostgreSQL database.  
* A running Redis server  
* An AWS S3 bucket and credentials  
* A SendGrid API key

### **Installation**

1. Clone the repository:  
   git clone \[your-repo-url\]  
   cd \[your-repo-folder\]

2. Create and activate a virtual environment:  
   python3.10 \-m venv venv  
   source vVenv/bin/activate  
   \# On Windows, use: venv\\Scripts\\activate

3. Install the required modules from requirements.txt:  
   pip install \-r requirements.txt  
   **Note:** If any packages fail to install, you can try installing them individually on the command line without a specific version (e.g., pip install \[package-name\]).  
4. Set up your Environment Variables by creating a .env file in the project root. See the section below for all required variables.  
5. Run the database migrations:  
   flask db upgrade

6. Run the application (with live-reload):  
   flask run

   Or run with the socketio development server:  
   python run.py

## **⚙️ Environment Variables**

Create a .env file in the root of the project and add the following variables.

\# \--- General \---  
\# A strong, random string for Flask app security  
SECRET\_KEY=YOUR\_FLASK\_SECRET\_KEY  
\# The domain of your frontend client (e.g., http://localhost:5173 or \[https://www.yourdomain.com\](https://www.yourdomain.com))  
CLIENT\_DOMAIN=YOUR\_CLIENT\_DOMAIN\_URL

\# \--- Database (PostgreSQL \+ PostGIS) \---  
DB\_HOST=localhost  
DB\_PORT=5432  
DB\_USER=your\_db\_user  
DB\_PASSWORD=your\_db\_password  
DB\_NAME=your\_db\_name  
\# Full database connection string  
PROJECT\_DATABASE\_URL=postgresql://your\_db\_user:your\_db\_password@localhost:5432/your\_db\_name

\# \--- Caching (Redis) \---  
\# Connection string for your Redis server  
REDIS\_URL=redis://localhost:6379/0

\# \--- Authentication (JWT) \---  
\# A separate, strong, random string for signing JWTs  
JWT\_SECRET\_KEY=YOUR\_JWT\_SECRET\_KEY

\# \--- File Storage (AWS S3) \---  
AWS\_ACCESS\_KEY\_ID=YOUR\_AWS\_ACCESS\_KEY  
AWS\_SECRET\_ACCESS\_KEY=YOUR\_AWS\_SECRET\_KEY  
S3\_BUCKET\_NAME=your-s3-bucket-name  
\# S3\_REGION=us-east-1 (Optional, defaults to us-east-1 in config.py)

\# \--- Email (SendGrid) \---  
SENDGRID\_API\_KEY=YOUR\_SENDGRID\_API\_KEY  
\# The email address used for "from" fields (e.g., no-reply@yourdomain.com)  
ADMIN\_EMAIL=your-admin-email@example.com  
\# Often the same as ADMIN\_EMAIL  
MAIL\_DEFAUL\_SENDER=your-admin-email@example.com

## **🐳 Deployment (Docker)**

This backend is designed to be packaged in a Docker image for easy deployment and scaling. The Dockerfile and start.sh script are already configured for production use.

1. **Build the image:**  
   docker build \-t your-backend-image-name .

2. **Push to a repository (e.g., Docker Hub or AWS ECR):**  
   docker push your-backend-image-name

3. Run the container:  
   When running the container, you must provide all the necessary environment variables (e.g., via a \--env-file or your orchestration service).  
   docker run \-d \-p 5000:5000 \--env-file ./.env your-backend-image-name  
