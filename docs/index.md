# Planning Applications

## Dependencies

We use [uv](https://docs.astral.sh) to manage dependencies. Follow their [setup guide](https://docs.astral.sh/uv/getting-started/installation) to get started.

## Project layout

    docs/                  # Documentation
    db                     # Database files
    planning_applications/ # Scrapy project
    tests/                 # Tests
    mkdocs.yml             # Documentation config
    .env                   # Environment variables

## Getting up and running as a new developer

1. Download [Docker](https://www.docker.com/products/docker-desktop/)

2. `git clone https://github.com/buildwithtract/planning_applications && cd planning_applications`

3. Run `cp .env.example .env` to create a new .env file.

4. Create a [Zyte account](https://www.zyte.com/sign-up/) and paste your API key into the .env file

5. Run `make reset_db` to set up a fresh postgres instance

You should see something like the following output eventually:

```
database   | 2024-12-28 14:33:31.524 UTC [1] LOG:  database system is ready to accept connections
```

### Running the scraper in Docker

If you want to test the scraper end to end you probably want to run it in a Docker container.

To do this, set `POSTGRES_HOST=db` in the .env file.

Then run `make run lpa=<LPA_NAME>` to run the scraper.

### Running scraper in Docker with a separate database

Change your your POSTGRES_HOST from 127.0.0.1 to host.docker.internal in the .env file.

Then run:

```bash
docker-compose build scraper

docker-compose run --rm --no-deps scraper --lpas-from-earliest sheffield westminster cambridge
```

### Running the scraper outside of Docker

If you are actively developing, you probably don't want to have to rebuild the scrapy container every time you make a change.

That's okay, because you can still run the scraper outside of the container, but keep it writing to the database inside.

To do this, set `POSTGRES_HOST=localhost` in the .env file.

Then run `uv run scrapy crawl <LPA_NAME>` to run the scraper.

## Saving Files to S3

By default, the scraper will not scrape files and save them to S3.

You can enable this by setting the following environment variables:

- `DOWNLOAD_FILES=true`

You'll also need to configure an AWS profile for the scraper to use. You can do this by setting the `AWS_PROFILE` environment variable:

- `AWS_PROFILE=tract-staging`

And allowing the `boto3` library to access your AWS credentials.

Alternatively, you can set the `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_REGION` environment variables, and the scraper will use these credentials directly.

## Documentation

We are using [mkdocs](https://www.mkdocs.org/) to build the documentation site.

### Commands

- `mkdocs serve` - Start the live-reloading docs server.
- `mkdocs build` - Build the documentation site.
- `mkdocs -h` - Print help message and exit.
