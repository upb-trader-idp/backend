# Changelog

## [0.1.1] - 01/05/2025

### Added
- Prometheus
- Grafana
- Portainer


## [0.1.0] - 30/04/2025

### Added
- Kong for API routes, JWT, CORS
- Added finance_service
- Added delete_trade, edit_trade endpoints

### Changed
- All container ports


## [0.0.5] - 24/04/2025

### Added
- Completed the business_logic microservice
- Extra exception handling

### Changed
- Merged users_db and trading_db into a single database
- Restructured networks in docker-compose
- Reduced boilerplate: moved database.py, models.py, schemas.py into a "shared" folder,
copied on the auth_service, business_logic_service, db_interaction_service containers

### Fixed
- Refund bug in the business_logic microservice

### Removed
- One of the two Postgres microservices


## [0.0.4] - 24/04/2025

### Added
- Initial business_logic microservice
- Adminer microservice

### Removed 
- blocked_balance endpoint and blocked_balance field


## [0.0.3] - 23/04/2025

### Added 
- Added block_balance endpoint

### Changed
- Moved get_balance, remove_balance, add_trade endpoints to db_interaction microservice
- Restructured networks in docker-compose
- Split database in users_db and trading_db


## [0.0.2] - 23/04/2025

### Added
- Database interaction microservice
- Endpoints: get_balance, add_balance, remove_balance
- blocked_balance field in database

### Changed
- Standardized file names, docker image names 


## [0.0.1] - 22/04/2025

### Added 
- Authentication microservice
- Postgres database microservices
- Added services to docker-compose.yml

### Changed
- Replaced psycopg2 with SQLAlchemy for database interaction

### Fixed
- CORS error when sending API requests from a browser
- Typo in a database connect function
