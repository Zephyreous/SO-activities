openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/server.key -out certs/server.crt \
  -days 365 -config certs/openssl-san.cnf
