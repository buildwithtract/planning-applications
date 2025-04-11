reset_db:
	docker-compose down
	docker volume rm planning-applications_planning_applications_data
	docker-compose build
	docker-compose up -d

run:
	docker-compose run scraper $(lpa)

run_with_external_db:
	docker-compose run --rm --no-deps scraper $(lpa)