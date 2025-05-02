# Trader IDP - Backend

## Requirements
- [Docker](https://www.docker.com/)

## Download & Run
```sh
git clone https://github.com/upb-trader-idp/backend.git
cd backend
```

### Docker Compose
```sh
docker-compose -p trader_idp up --build
```

### Docker Swarm
```sh
docker stack deploy -c stack.yml trader_idp
```

## Architecture
- **Authentication microservice**:
    - "auth_service" - handles user registration, login and JWT token generation. Exposes the endpoints:
        - *POST* /register
        - *POST* /login 
<br/>

- **Business Logic microservices**:
    - "business_logic_service" - handles matching buy orders with sell orders and the transfer of money or stocks between the buyer and the seller.
    - "finance_service" - API used for fetching data about stocks from external sources (yfinance). Exposes the endpoints:
        - *GET* /stock/{symbol}
        - *GET* /stock/{symbol}/history
        - *GET* /stock/{symbol}/search
<br/>

- **Database Interaction microservice**:
    - "db_interaction_serivce" - handles database operations such as adding/removing cash balance, adding/removing/editing trades, fetching cash balance, portfolio. Exposes the endpoints:
        - *GET* /get_balance
        - *POST* /add_balance
        - *POST* /remove_balance
        - *POST* /add_trade
        - *PUT* /edit_trade/{trade_id}
        - *DELETE* /delete_trade/{trade_id}
        - *GET* /get_portfolio
<br/>

- **Database microservice**:
    - db_service/postgres - PostgreSQL database that contains three tables that the application uses:
        - *users* - Stores usernames, hashed passwords, cash balance.
        - *trades* - Stores data about trades: username, price, quantity, action, timestamp, etc.
        - *portfolio* - Stores each user's stock holdings: username, symbol, quantity, average price.
<br/>

- **Database management microservice**: Adminer
- **Cluster management microservice**: Portainer
- **API management microservice**: Kong
- **Metric collection and visualization**: Prometheus + Grafana
<br/>

- **Open ports**
    - *auth_service*: 8002
    - *db_interaction_service*: 8003
    - *finance_service*: 8004
    - *Kong*: 8000, 8001, 8443, 8444
    - *Adminer*: 8080
    - *Prometheus*: 9090
    - *Grafana*: 3000
<br/>

- **Networks**
    - *adminer_net*: Adminer, db_service
    - *auth_net*: auth_service, Kong, db_service
    - *business_logic_net*: business_logic_service, db_service
    - *db_interaction_net*: db_interaction_service, Kong, db_service
    - *finance_net*: finance_service, Kong
    - *kong_net*: Kong, Prometheus
    - *monitoring_net*: business_logic_service, auth_service, finance_service, db_interaction_service, Kong, Grafana, Prometheus, Portainer
<br/>

- **Credentials**
    - Grafana:
        - *username*: admin
        - *password*: admin
    - Postgres:
        - *system*: PostgreSQL
        - *server*: db_service
        - *username*: postgres
        - *password*: postgres
        - *database*: main_db
