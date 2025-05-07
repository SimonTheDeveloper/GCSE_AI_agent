# Airline Test

## Description
Coding test set by ajaali consulting.

## Requirements
- Python 3.9
- Poetry (version 1.1.0 or later)
- Node.js (version 16.x or later)
- AWS CDK CLI (version 2.166.0)
- AWS CLI (configured with appropriate credentials)

## Setup

0. **Install Poetry**:
    Open a terminal and run the following command to install Poetry:
    ```sh
    curl -sSL https://install.python-poetry.org | python3 -
    ```

1. **Install dependencies using Poetry**:
    Open a terminal and run the following command to install the project dependencies using Poetry:
    ```sh
    poetry install
    ```

2. **Install dependencies using pip**:
    If you prefer to use `pip`, follow these steps:

    a. Create a virtual environment:
    ```sh
    python3 -m venv venv
    ```

    b. Activate the virtual environment:
    - On macOS and Linux:
      ```sh
      source venv/bin/activate
      ```
    - On Windows:
      ```sh
      .\venv\Scripts\activate
      ```

    c. Install the dependencies listed in the [requirements.txt](http://_vscodecontentref_/0) file:
    ```sh
    pip install -r requirements.txt
    ```

3. **Create a [.env](http://_vscodecontentref_/1) File**:
    Create a [.env](http://_vscodecontentref_/2) file in the root of your project directory and add your AWS credentials and other necessary environment variables.
    ```env
    AWS_ACCESS_KEY_ID=your_access_key_id
    AWS_SECRET_ACCESS_KEY=your_secret_access_key
    AWS_DEFAULT_REGION=your_default_region
    ```

4. **Install Node.js and AWS CDK CLI**:
    Ensure you have Node.js 16.x or later and the AWS CDK CLI version 2.166.0 installed.

    a. Install Node.js using `nvm`:
    ```sh
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
    export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 16
    nvm use 16
    ```

    b. Install AWS CDK CLI:
    ```sh
    npm install -g aws-cdk@2.166.0
    ```

5. **Configure AWS CLI**:
    Ensure your AWS CLI is configured with appropriate credentials:
    ```sh
    aws configure
    ```

6. **Bootstrap the Environment**:
    Run the following command to bootstrap the environment:
    ```sh
    cdk bootstrap aws://ACCOUNT-NUMBER/REGION
    ```

    Replace `ACCOUNT-NUMBER` with your AWS account number and `REGION` with the AWS region you are deploying to (e.g., `eu-west-2`).

7. **Activate the virtual environment**:
    Ensure the virtual environment is activated before running any commands:
    - On macOS and Linux:
      ```sh
      source venv/bin/activate
      ```
    - On Windows:
      ```sh
      .\venv\Scripts\activate
      ```

8. **Deploy using CDK**:
    Run the following command to deploy the infrastructure:
    ```sh
    cdk deploy
    ```

9. **Generate stub data**:
    After deploying the infrastructure, generate the stub data by running the following command from the base directory:
    ```sh
    python backend/load_flight_data.py
    ```

10. **Run the FastAPI server**:
    Start the FastAPI server by running the following command:
    ```sh
    poetry run uvicorn backend.app.main:app --reload
    ```

## Frontend

### For a Simple Static Site

1. **Install HTTP Server**:
    ```sh
    npm install -g http-server
    ```

2. **Serve the Frontend Files**:
    Run the following command from the base directory.
    ```sh
    http-server
    ```

    Open the provided URL (e.g., `http://localhost:8080/frontend`) in your browser to view the application.

    This will start the development server and open your application in the default web browser.