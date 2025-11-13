#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "❌ GITHUB_TOKEN ortam değişkenini ayarlayın (repo 'pages:write' iznine sahip bir PAT gerekir)." >&2
  exit 1
fi

OWNER="${REPO_OWNER:-yafurkan}"
REPO="${REPO_NAME:-su-takip-website}"
DOMAIN="${CUSTOM_DOMAIN:-suuapp.com}"
API_ROOT="https://api.github.com/repos/${OWNER}/${REPO}/pages"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

json_request() {
  local method="$1"
  local url="$2"
  local data="${3:-}"
  local body_file="$TMP_DIR/response.json"

  if [[ -n "$data" ]]; then
    printf '%s\n' "$data" > "$TMP_DIR/payload.json"
    http_code=$(
      curl -sS -w "%{http_code}" -o "$body_file" \
        -X "$method" \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        -d @"$TMP_DIR/payload.json" \
        "$url"
    )
  else
    http_code=$(
      curl -sS -w "%{http_code}" -o "$body_file" \
        -X "$method" \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        "$url"
    )
  fi

  RESPONSE_BODY="$(cat "$body_file")"
  echo "$http_code"
}

echo "➡️  GitHub Pages sitesi oluşturuluyor/yeniden etkinleştiriliyor..."
create_code=$(json_request "POST" "$API_ROOT" '{"build_type":"workflow"}')

case "$create_code" in
  201|202|204)
    echo "✅ Pages build türü 'workflow' olarak ayarlandı."
    ;;
  409)
    echo "ℹ️  Pages sitesi zaten mevcut, devam ediliyor..."
    ;;
  *)
    echo "❌ Pages sitesi oluşturulamadı (HTTP $create_code)." >&2
    echo "$RESPONSE_BODY" >&2
    exit 1
    ;;
esac

read -r -d '' update_payload <<JSON
{
  "cname": "$DOMAIN",
  "https_enforced": true
}
JSON

echo "➡️  Özel domain ($DOMAIN) ve HTTPS zorlaması ayarlanıyor..."
update_code=$(json_request "PUT" "$API_ROOT" "$update_payload")

if [[ "$update_code" != "200" && "$update_code" != "202" ]]; then
  echo "❌ Domain yapılandırması başarısız oldu (HTTP $update_code)." >&2
  echo "$RESPONSE_BODY" >&2
  exit 1
fi

echo "✅ Domain yapılandırması gönderildi. DNS kayıtları doğruysa Pages birkaç dakika içinde aktif olacaktır."
echo "🔁 Gerekirse yeni bir commit/push ile mevcut deploy workflow'unu tetikleyin."
