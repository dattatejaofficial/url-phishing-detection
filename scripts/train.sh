set -ex

echo "=============================="
echo "TRAINING START: $(date)"
echo "User: $(whoami)"
echo "=============================="

WORKDIR="/home/$VM_USERNAME/url-phishing-detection"
cd "$WORKDIR"

[ -z "$MONGODB_URI" ] && echo "MONGODB_URI missing" && exit 1
[ -z "$MLFLOW_TRACKING_URI" ] && echo "MLFLOW_TRACKING_URI missing" && exit 1
[ -z "$AZURE_STORAGE_CONNECTION_STRING" ] && echo "AZURE_STORAGE_CONNECTION_STRING missing" && exit 1
[ -z "$AZURE_ARTIFACT_STORAGE_CONNECTION_STRING" ] && echo "AZURE_ARTIFACT_STORAGE_CONNECTION_STRING missing" && exit 1
[ -z "$AZURE_BLOB_ARTIFACT_CONTAINER" ] && echo "AZURE_BLOB_ARTIFACT_CONTAINER missing" && exit 1
[ -z "$AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER" ] && echo "AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER missing" && exit 1

STORAGE_ACCOUNT_NAME=$(echo "$AZURE_ARTIFACT_STORAGE_CONNECTION_STRING" | grep -oP 'AccountName=\K[^;]+')
ARTIFACT_ROOT="wasbs://$AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER@$STORAGE_ACCOUNT_NAME.blob.core.windows.net/"

echo "Artifact root: $ARTIFACT_ROOT"

echo "=== START MLFLOW ==="

PYTHON_EXEC="./venv/bin/python"

pkill -f "mlflow server" || true

$PYTHON_EXEC -m mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --registry-store-uri sqlite:///mlflow.db \
  --default-artifact-root "$ARTIFACT_ROOT" \
  --host 0.0.0.0 \
  --port 5000 > mlflow.log 2>&1 &

sleep 10

echo "=== RUN TRAINING ==="

if $PYTHON_EXEC -m phishingsystem.pipeline.training_pipeline.pipeline > training.log 2>&1; then
  echo "TRAINING SUCCESS"
else
  echo "TRAINING FAILED"
  pkill -f "mlflow server" || true
  exit 1
fi

pkill -f "mlflow server" || true

echo "=============================="
echo "TRAINING END: $(date)"
echo "=============================="