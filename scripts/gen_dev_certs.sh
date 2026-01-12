#!/bin/bash
# scripts/gen_dev_certs.sh
set -e

mkdir -p dev_certs
cd dev_certs

cat > openssl.cnf <<EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
[req_distinguished_name]
[v3_ca]
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid:always,issuer
basicConstraints = critical,CA:TRUE
keyUsage = critical, digitalSignature, cRLSign, keyCertSign

[v3_req]
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[v3_client]
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
EOF

echo "1. Generating CA..."
openssl genrsa -out ca.key 2048
openssl req -x509 -new -nodes -key ca.key -sha256 -days 365 -out ca.crt -subj "/CN=SimcoDevCA" -config openssl.cnf -extensions v3_ca

echo "2. Generating Server Cert..."
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=localhost" -config openssl.cnf
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -sha256 -extfile openssl.cnf -extensions v3_req

echo "3. Generating Client Cert..."
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=simco-dev-device" -config openssl.cnf
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365 -sha256 -extfile openssl.cnf -extensions v3_client

echo "Done! Certificates generated in dev_certs/ with proper X.509 extensions."
