#!/bin/bash

function init() {
    echo Performing initialization...
    cat > ca.conf <<EOF
[ ca ]
default_ca = ca_default
[ ca_default ]
dir = ./ca
certs = \$dir
new_certs_dir = \$dir/ca.db.certs
database = \$dir/ca.db.index
serial = \$dir/ca.db.serial
RANDFILE = \$dir/ca.db.rand
certificate = \$dir/ca.cert.pem
private_key = \$dir/ca.key.pem
default_days = 365
default_crl_days = 30
default_md = md5
preserve = no
policy = generic_policy
[ generic_policy ]
countryName = optional
stateOrProvinceName = optional
localityName = optional
organizationName = optional
organizationalUnitName = optional
commonName = optional
emailAddress = optional
EOF

    mkdir ca
    mkdir ca/ca.db.certs
    touch ca/ca.db.index
    echo 1000 > ca/ca.db.serial
    openssl req -x509 -newkey rsa:4096 -keyout ca/ca.key.pem -out ca/ca.cert.pem -sha256 -days 365 -subj '/CN=ca' -nodes
    chmod 644 ca/ca.key.pem
}

function mkcert {
    CN="$1"
    openssl req -new -newkey rsa:1024 -nodes -keyout $CN.key.pem -out $CN.csr.pem -subj "/CN=$1" -nodes
    openssl ca -batch -config ca.conf -out $CN.cert.pem -infiles $CN.csr.pem
}

if [[ ! -e "initialized" ]]; then
    init
    touch initialized
fi

if [[ "$1" == "init" ]]; then
    exit 0
elif [[ "$1" == "mkcert" ]]; then
    if [[ ! "$2" =~ ^[a-z0-9]+$ ]]; then
        echo -e "Error. Usage: $0 mkcert <cn>\ncn: Can only be the characters a-z0-9"
        exit 1
    fi

    mkcert "$2"
else
    echo -e "Error. Usage $0 <cmd>\ncmd: Must be one of init, mkcert"
fi
