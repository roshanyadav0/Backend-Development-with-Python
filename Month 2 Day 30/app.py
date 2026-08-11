# PostgreSQL, installed and running
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
sudo -u postgres psql -c "SELECT version();"

# SQLAlchemy — an overview, no code

# ORM vs. raw SQL — the actual tradeoff

