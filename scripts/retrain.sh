set -e

echo "=== DEBUG INFO ==="
echo "User: $(whoami)"
echo "MLFLOW_TRACKING_URI=$MLFLOW_TRACKING_URI"

WORKDIR="/home/$USER/url-phishing-detection"
cd $WORKDIR

rm -f TRAINING_DONE TRAINING_FAILED

if [ -z "$MONGODB_URI" ]; then
  echo "ERROR: MONGODB_URI missing"
  touch TRAINING_FAILED
  exit 1
fi

if [ -z "$MLFLOW_TRACKING_URI" ]; then
  echo "ERROR: MLFLOW_TRACKING_URI missing"
  touch TRAINING_FAILED
  exit 1
fi

if [ -z "$AZURE_STORAGE_CONNECTION_STRING" ]; then
  echo "ERROR: AZURE_STORAGE_CONNECTION_STRING missing"
  touch TRAINING_FAILED
  exit 1
fi

if [ -z "$AZURE_ARTIFACT_STORAGE_CONNECTION_STRING" ]; then
  echo "ERROR: AZURE_ARTIFACT_STORAGE_CONNECTION_STRING missing"
  touch TRAINING_FAILED
  exit 1
fi

if [ -z "$AZURE_BLOB_ARTIFACT_CONTAINER" ]; then
  echo "ERROR: AZURE_BLOB_ARTIFACT_CONTAINER missing"
  touch TRAINING_FAILED
  exit 1
fi

if [ -z "$AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER" ]; then
  echo "ERROR: AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER missing"
  touch TRAINING_FAILED
  exit 1
fi

STORAGE_ACCOUNT_NAME = $(echo "$AZURE_ARTIFACT_STORAGE_CONNECTION_STRING" | grep -oP 'AccountName=\K[^;]+')
ARTIFACT_ROOT = "wasbs://$AZURE_BLOB_MLFLOW_ARTIFACT_CONTAINER@$STORAGE_ACCOUNT_NAME.blob.core.windows.net/"

echo "Using artifact root: $ARTIFACT_ROOT"

echo "=== SYNC REPO ==="
git fetch origin
git reset --hard origin/main
git clean -fd -e venv -e mlruns

PYTHON_EXEC="./venv/bin/python"

echo "=== START MLFLOW ==="

pkill -f "mlflow server" || true

nohup $PYTHON_EXEC -m mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --registry-store-uri sqlite:///mlflow.db \
  --default-artifact-root "$ARTIFACT_ROOT" \
  --host 0.0.0.0 \
  --port 5000 \
  > mlflow.log 2>&1 &

for i in {1..20}; do
  if curl -s http://127.0.0.1:5000 > /dev/null; then
    echo "MLflow is up"
    break
  fi
  sleep 3
done

echo "=== RUN TRAINING ==="

if $PYTHON_EXEC -m phishingsystem.pipeline.retraining_pipeline.pipeline > training.log 2>&1; then
  echo "=== TRAINING SUCCESS ==="
  touch TRAINING_DONE
else
  echo "=== TRAINING FAILED ==="
  touch TRAINING_FAILED
  exit 1
fi

pkill -f "mlflow server" || true

echo "=== DONE ==="