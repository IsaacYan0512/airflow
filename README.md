# Airflow Setup with Customized Docker Image

## Step 1: Start Minikube

```bash
minikube start 
```
## Step 2: Add and Update Helm Repositories

```bash
helm repo add apache-airflow https://airflow.apache.org
helm repo update
```

## Step 3: Get apache/airflow official Helm Chart

```bash
helm show values apache-airflow/airflow > values.yaml
```

## Step 4: Change the image repo to a customized one

```bash
airflowHome: /opt/airflow

# Default airflow repository -- overridden by all the specific images below
defaultAirflowRepository: isaac3687/airflow-custom #customized docker image

# Default airflow tag to deploy
defaultAirflowTag: "2.9.2"

# Default airflow digest. If specified, it takes precedence over tag
defaultAirflowDigest: ~

# Airflow version (Used to make some decisions based on Airflow Version being deployed)
airflowVersion: "2.9.2"

images:
  airflow:
    repository: isaac3687/airflow-custom #customized docker image
    tag: latest
    # Specifying digest takes precedence over tag.
    digest: ~
    pullPolicy: IfNotPresent

```

## Step 5: Change dags parameters to auto pull the dags task file from git

```bash
dags:
  # Where dags volume will be mounted. Works for both persistence and gitSync.
  # If not specified, dags mount path will be set to $AIRFLOW_HOME/dags
  mountPath: ~
  persistence:
    # Annotations for dags PVC
    annotations: {}
    # Enable persistent volume for storing dags
    enabled: false
    # Volume size for dags
    size: 1Gi
    # If using a custom storageClass, pass name here
    storageClassName:
    # access mode of the persistent volume
    accessMode: ReadWriteOnce
    ## the name of an existing PVC to use
    existingClaim:
    ## optional subpath for dag volume mount
    subPath: ~
  gitSync:
    enabled: true

    # git repo clone url
    # ssh example: git@github.com:apache/airflow.git
    # https example: https://github.com/apache/airflow.git
    repo: https://github.com/apache/airflow.git
    branch: main
    rev: HEAD
    # The git revision (branch, tag, or hash) to check out, v4 only
    ref: v2-2-stable
    depth: 1
    # the number of consecutive failures allowed before aborting
    maxFailures: 0
    # subpath within the repo where dags are located
    # should be "" if dags are at repo root
    subPath: ""
    # if your repo needs a user name password
    # you can load them to a k8s secret like the one below
    #   ---
    #   apiVersion: v1
    #   kind: Secret
    #   metadata:
    #     name: git-credentials
    #   data:
    #     # For git-sync v3
    #     GIT_SYNC_USERNAME: <base64_encoded_git_username>
    #     GIT_SYNC_PASSWORD: <base64_encoded_git_password>
    #     # For git-sync v4
    #     GITSYNC_USERNAME: <base64_encoded_git_username>
    #     GITSYNC_PASSWORD: <base64_encoded_git_password>
    # and specify the name of the secret below
    #
    credentialsSecret: git-credentials
    #
    #
    # If you are using an ssh clone url, you can load
    # the ssh private key to a k8s secret like the one below
    #   ---
    #   apiVersion: v1
    #   kind: Secret
    #   metadata:
    #     name: airflow-ssh-secret
    #   data:
    #     # key needs to be gitSshKey
    #     gitSshKey: <base64_encoded_data>
    # and specify the name of the secret below
    sshKeySecret: airflow-ssh-secret
    #
    # If you are using an ssh private key, you can additionally
    # specify the content of your known_hosts file, example:
    #
    #knownHosts: |
    # interval between git sync attempts in seconds
    # high values are more likely to cause DAGs to become out of sync between different components
    # low values cause more traffic to the remote git repository
    # Go-style duration string (e.g. "100ms" or "0.1s" = 100ms).
    # For backwards compatibility, wait will be used if it is specified.
    period: 60s
    wait: ~

    containerName: git-sync
    uid: 65533

    # When not set, the values defined in the global securityContext will be used
    securityContext: {}
    #  runAsUser: 65533
    #  runAsGroup: 0

    securityContexts:
      container: {}

    # container level lifecycle hooks
    containerLifecycleHooks: {}

    # Mount additional volumes into git-sync. It can be templated like in the following example:
    #   extraVolumeMounts:
    #     - name: my-templated-extra-volume
    #       mountPath: "{{ .Values.my_custom_path }}"
    #       readOnly: true
    extraVolumeMounts: []
    env: []
    # Supported env vars for gitsync can be found at https://github.com/kubernetes/git-sync
    # - name: ""
    #   value: ""

    # Configuration for empty dir volume
    # emptyDirConfig:
    #   sizeLimit: 1Gi
    #   medium: Memory

    resources: {}
    #  limits:
    #   cpu: 100m
    #   memory: 128Mi
    #  requests:
    #   cpu: 100m
    #   memory: 128Mi

```

## Step 6: Create namespace in minikube

```bash
kubectl create namespace airflow

```

## Step 7: Create ssh pub key to access git

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_airflow

kubectl create secret generic airflow-ssh-secret \
  --from-file=gitSshKey=/home/ubuntu/.ssh/id_rsa -n airflow

ssh-keyscan github.com >> ~/.ssh/known_hosts
kubectl create secret generic git-known-hosts --from-file=known_hosts=/home/ubuntu/.ssh/known_hosts -n airflow

rm ~/.ssh/known_hosts
```

## Step 8: Customize the docker image

```bash
FROM apache/airflow:2.9.2

USER airflow

# 安装 clicksend-client 包
RUN pip install clicksend-client psycopg2-binary Jinja2==3.1.2
```

## Step 9: Build and Push the customized image into Docker Hub

```bash
docker build -t isaac3687/airflow-custom:latest .

docker push isaac3687/airflow-custom:latest

```


## Step 10: Build airflow Service via values.yaml

```bash
helm install airflow apache-airflow/airflow -f values.yaml -n airflow
```


## Step 11: Enter the airflow’s Homepage UI, Find Admin -> Variables
Add all the environments below:

```bash
Key: POSTGRES_DB Value: postgres
Key: POSTGRES_USER Value: postgres
Key: POSTGRES_PASSWORD Value: postgres
Key: POSTGRES_HOST Value: 10.105.157.7
Key: POSTGRES_PORT Value: 5432
Key: CLICKSEND_USERNAME Value: 
Key: CLICKSEND_PASSWORD Value: 
Key: CLICKSEND_EMAIL_FROM_ID Value: 
```
