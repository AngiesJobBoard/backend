
# Angies Job Board Backend

This repository stores the API, database connectors, business logic, and async data handling for the HR platform AngiesJobBoard.


## Features

- Create and manage Job Posts
- Upload and scan resumes of candidates
- Automatically score and match candidates to job posts
- Track candidates through full hiring cycle using custom candidate statuses
- Custom data integrations with any incoming or outgoing source
- Inbound email parsing for candidates to send resumes
- Support for public job posting pages
- Inviting and manage recruiters in your company


## Tech Stack

Python3

FastAPI

ArangoDB

OpenAI

Sendgrid

Stripe

Kafka

Containerized and deployed to Heroku



## Run Locally

Start database and kafka services locally with docker

```bash
  docker compose up -d
```

Install dependencies

```bash
  pipenv install -d
```

Start the server

```bash
  pipenv run localapi
```

Run testing, linting, and type checking

```bash
  pipenv run check_all
```

## Authors

- [@mikeshanahan](https://www.github.com/mikeshanahan)

