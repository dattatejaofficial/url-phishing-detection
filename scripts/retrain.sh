set -euo pipefail

echo "=============================="
echo "RETRAINING START: $(date)"
echo "User: $(whoami)"
echo "=============================="

WORKDIR="/home/$VM_USERNAME/url-phishing-detection"
cd "$WORKDIR"

[ -z "${MONGODB_URI:-}" ] && echo "MONGODB_URI missing" && exit 1
[ -z "${MLFLOW_TRACKING_URI:-}" ] && echo "MLFLOW_TRACKING_URI missing" && exit 1
[ -z "${AZURE_STORAGE_CONNECTION_STRING:-}" ] && echo "AZURE_STORAGE_CONNECTION_STRING missing" && exit 1
[ -z "${AZURE_ARTIFACT_STORAGE_CONNECTION_STRING:-}" ] && echo "AZURE_ARTIFACT_STORAGE_CONNECTION_STRING missing" && exit 1
[ -z "${AZURE_BLOB_ARTIFACT_CONTAINER:-}" ] && echo "AZURE_BLOB_ARTIFACT_CONTAINER missing" && exit 1
[ -z "${AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER:-}" ] && echo "AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER missing" && exit 1

STORAGE_ACCOUNT_NAME=$(echo "$AZURE_ARTIFACT_STORAGE_CONNECTION_STRING" | grep -oP 'AccountName=\K[^;]+')
ARTIFACT_ROOT="wasbs://$AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER@$STORAGE_ACCOUNT_NAME.blob.core.windows.net/"

echo "Artifact root: $ARTIFACT_ROOT"

PYTHON_EXEC="./venv/bin/python"

echo "=== STOP EXISTING MLFLOW ==="
pkill -f "mlflow server" || true
sleep 5

echo "=== START MLFLOW ==="
$PYTHON_EXEC -m mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --registry-store-uri sqlite:///mlflow.db \
  --default-artifact-root "$ARTIFACT_ROOT" \
  --host 0.0.0.0 \
  --port 5000 > mlflow.log 2>&1 &

echo "=== WAITING FOR MLFLOW SERVER ==="
for i in {1..30}; do
  if curl -s http://127.0.0.1:5000 >/dev/null; then
    echo "MLflow is up!"
    break
  fi
  echo "Waiting... ($i)"
  sleep 2
done

if ! curl -s http://127.0.0.1:5000 >/dev/null; then
  echo "MLflow failed to start"
  cat mlflow.log
  exit 1
fi

echo "=== RUN RETRAINING ==="

set +e
$PYTHON_EXEC -m phishingsystem.pipeline.retraining_pipeline.pipeline 2>&1 | tee training.log
EXIT_CODE=${PIPESTATUS[0]}
set -e

if [ $EXIT_CODE -ne 0 ]; then
  echo "RETRAINING FAILED (exit code: $EXIT_CODE)"
  echo "===== LAST 100 LINES OF LOG ====="
  tail -n 100 training.log
  pkill -f "mlflow server" || true
  exit $EXIT_CODE
fi

echo "RETRAINING SUCCESS"

echo "=== STOP MLFLOW ==="
pkill -f "mlflow server" || true

echo "=============================="
echo "RETRAINING END: $(date)"
echo "=============================="