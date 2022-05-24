![Paco](/paco/static/images/brand_identity/logo_whole.png "Paco logo")

Paco is an website written in Flask to manage a peer to peer delivery service.

It is written in Python 3.7. For the whole library requirement list refer to _requirements.txt_

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the Python requirements for Paco.

```bash
pip install -r requirements.txt
```
Then, install the required node modules by moving into the _\'paco/static/assets\'_ directory and run:

```bash
npm install
```

## Environment Variables

The software requires the following environment variables:

* EMAIL_SERVER: the address of your email SMTP mail server 
* EMAIL_USER: your email
* EMAIL_PASS: your email password
* EMAIL_PORT: the port in which the SMTP mail server accepts connections
* EMAIL_SSL: 1 if server needs SSL, else 0
* EMAIL_TLS: 1 if server needs TLS, else 0
* FLASK_SALT_KEY: a salt key for flask encryption 
* FLASK_SECRET_KEY: a secret key for flask encryption 
* GOOGLE_MAPS_API_KEY: your Google Maps API key
* SQLALCHEMY_DATABASE_URI: the URI of the SqlAlchemy Database
* TARGA_USERNAME: a [https://www.regcheck.org.uk/](https://www.regcheck.org.uk/) valid username

If you provde a .env file, then the application automatically loads the environment variables into the project

## Run the server

To run the server in debug mode, use:
```bash
export FLASK_ENV=development
python3 -m flask run
```

To deploy the server, run:
```bash
python -m flask run -h 0.0.0.0 -p 80
```

## Run with Docker

In order to run it with Docker:

1)Create a _.env_ file in the main folder

2)Build the image using ` docker build . -t paco/paco `

3)Run the container using ` docker run -p 80:80 paco/paco `
