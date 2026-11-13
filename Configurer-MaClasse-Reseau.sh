#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
umask 077
LAN_IP="${1:-}"
if [[ -z "$LAN_IP" ]]; then echo "Usage: $0 ADRESSE_IPV4_PRIVEE"; exit 2; fi
if ! .venv/bin/python -c 'import ipaddress,sys; a=ipaddress.ip_address(sys.argv[1]); assert isinstance(a,ipaddress.IPv4Address) and a.is_private and not a.is_loopback and not a.is_link_local and not a.is_multicast and not a.is_unspecified' "$LAN_IP" >/dev/null 2>&1; then
  echo "Adresse IPv4 privée invalide : $LAN_IP"; exit 2
fi
command -v openssl >/dev/null 2>&1 || { echo "OpenSSL est requis."; exit 2; }
TLS_DIR="data/tls"; mkdir -p "$TLS_DIR"
CA_KEY="$TLS_DIR/ca.key"; CA_CERT="$TLS_DIR/ca.crt"
SERVER_KEY="$TLS_DIR/server.key"; SERVER_CSR="$TLS_DIR/server.csr"; SERVER_CERT="$TLS_DIR/server.crt"; EXT="$TLS_DIR/server.ext"
if [[ -f "$CA_KEY" && ! -f "$CA_CERT" ]] || [[ ! -f "$CA_KEY" && -f "$CA_CERT" ]]; then
  echo "Autorité de certification incomplète. Restaure le couple ca.key/ca.crt."; exit 2
fi
if [[ ! -f "$CA_KEY" ]]; then
  echo "Création de l'autorité de certification locale MaClasse…"
  openssl genrsa -out "$CA_KEY" 4096
  openssl req -x509 -new -sha256 -days 3650 -key "$CA_KEY" -out "$CA_CERT" -subj "/CN=MaClasse Local Network CA"
fi
if [[ ! -f "$SERVER_KEY" ]]; then openssl genrsa -out "$SERVER_KEY" 2048; fi
openssl req -new -key "$SERVER_KEY" -out "$SERVER_CSR" -subj "/CN=$LAN_IP"
cat > "$EXT" <<EOF
subjectAltName=IP:$LAN_IP
extendedKeyUsage=serverAuth
keyUsage=digitalSignature,keyEncipherment
EOF
openssl x509 -req -in "$SERVER_CSR" -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial -out "$SERVER_CERT" -days 397 -sha256 -extfile "$EXT"
rm -f "$SERVER_CSR" "$EXT"
chmod 600 "$CA_KEY" "$SERVER_KEY"; chmod 644 "$CA_CERT" "$SERVER_CERT"
echo "Certificat HTTPS généré pour $LAN_IP."
echo "À installer sur chaque appareil client : $CA_CERT"
echo "Ne communique jamais ca.key ni server.key."
