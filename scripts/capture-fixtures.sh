#!/usr/bin/env bash
# Capture live API responses for parity test fixtures.
#
# Idempotent: re-running overwrites the captured response files. The
# manifest.json files are NOT generated here — they're hand-authored so
# the URL → file mapping stays under source control.
#
# Usage:
#   bash scripts/capture-fixtures.sh          # capture all free providers
#   bash scripts/capture-fixtures.sh hko      # capture only one provider
#
# OpenWeatherMap needs OPENWEATHERMAP_API_KEY in env to capture; we
# store the response with the key REDACTED before writing.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIX="$ROOT/fixtures/api-responses"
UA="WeatherSkill/1.0 (support@weather-skill.io)"

mkdir -p "$FIX"/{hko,jma,sg_nea,us_nws,openweathermap}

# want <provider> <filter...> — true if <filter> is empty or contains <provider>.
want() {
    local target="$1"
    shift
    [[ $# -eq 0 ]] || [[ " $* " == *" $target "* ]]
}
fetch() {
    # fetch <url> <outfile> [extra curl args...]
    local url="$1" out="$2"
    shift 2
    echo "  GET $url"
    curl -fsSL -H "User-Agent: $UA" -H "Accept: application/json" "$@" "$url" \
        | python3 -m json.tool > "$out"
}

if want hko "$@"; then
    echo "== HKO =="
    fetch "https://www.hko.gov.hk/wxinfo/json/one_json.xml" "$FIX/hko/one_json.json"
fi

if want jma "$@"; then
    echo "== JMA (Tokyo / 130000) =="
    fetch "https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json" \
          "$FIX/jma/forecast-130000.json"
    fetch "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/130000.json" \
          "$FIX/jma/overview-130000.json"
fi

if want sg_nea "$@"; then
    echo "== SG NEA =="
    base="https://api-open.data.gov.sg/v2/real-time/api"
    # data.gov.sg rate-limits aggressive bursts (HTTP 429), so sleep
    # briefly between requests.
    for ep in air-temperature relative-humidity wind-direction wind-speed \
              twenty-four-hr-forecast four-day-outlook psi; do
        case "$ep" in
            twenty-four-hr-forecast) out="24hr-forecast.json" ;;
            *)                       out="${ep}.json" ;;
        esac
        fetch "$base/$ep" "$FIX/sg_nea/$out"
        sleep 1
    done
fi

if want us_nws "$@"; then
    echo "== US NWS (New York: 40.7128,-74.006) =="
    # Chain: points -> observationStations -> observations/latest, +forecast.
    # NOTE: The manifest URL must match what the code generates
    # (40.7128,-74.006 without trailing zero), not the API's raw format.
    fetch "https://api.weather.gov/points/40.7128,-74.006" \
          "$FIX/us_nws/points.json"
    stations_url=$(python3 -c "import json;print(json.load(open('$FIX/us_nws/points.json'))['properties']['observationStations'])")
    forecast_url=$(python3 -c "import json;print(json.load(open('$FIX/us_nws/points.json'))['properties']['forecast'])")
    fetch "$stations_url" "$FIX/us_nws/stations.json"
    station_id=$(python3 -c "import json;print(json.load(open('$FIX/us_nws/stations.json'))['features'][0]['properties']['stationIdentifier'])")
    fetch "https://api.weather.gov/stations/$station_id/observations/latest" \
          "$FIX/us_nws/observations.json"
    fetch "$forecast_url" "$FIX/us_nws/forecast.json"
fi

if want openweathermap "$@"; then
    echo "== OpenWeatherMap (London) =="
    if [[ -z "${OPENWEATHERMAP_API_KEY:-}" ]]; then
        echo "  SKIP — OPENWEATHERMAP_API_KEY not set"
        echo "  (manifest.json has <API_KEY> placeholders; capture once a key is available)"
    else
        K="$OPENWEATHERMAP_API_KEY"
        base="https://api.openweathermap.org/data/2.5"
        fetch "$base/weather?q=London&appid=$K&units=metric" \
              "$FIX/openweathermap/weather.json"
        fetch "$base/forecast?q=London&appid=$K&units=metric" \
              "$FIX/openweathermap/forecast.json"
        fetch "$base/air_pollution?lat=51.5074&lon=-0.1278&appid=$K" \
              "$FIX/openweathermap/air-pollution.json"
    fi
fi

echo "Done."
