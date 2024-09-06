# Finance-Tracker
Finance-Tracker with SingleStore Kai Augmentation + Gen AI capabilities
1. Create a virtual environment

```shell
python -m venv ~/.venvs/aienv
source ~/.venvs/aienv/bin/activate
```

2. set openai api key:
   ```shell
   export OPENAI_API_KEY='<your_key_here>'
   ```

4. Install libraries

```shell
pip install -r requirements.txt
```

4. Run the application:
```shell
python app .py
```

## Create MongoDB Link and Migrate Data in SingleStore

1. Use the following command to create the MongoDB link in SingleStore. Replace the credentials appropriately before executing:

```sql
CREATE LINK mongo_expensewise AS MONGODB
CONFIG '{
    "mongodb.hosts": "<host_names from your mongo atlas connection >",
    "collection.include.list": "bankapp.transactions, bankapp.users",
    "mongodb.ssl.enabled": "true",
    "mongodb.authsource": "admin",
    "mongodb.members.auto.discover": "false"
}'
CREDENTIALS '{
    "mongodb.user": "<your_mongodb_user>",
    "mongodb.password": "<your_mongodb_password>"
}';
```

2. Create tables and start the migration pipeline:

```sql
CREATE TABLES AS INFER PIPELINE AS LOAD DATA LINK mongo_expensewise '*' FORMAT AVRO;
SHOW PIPELINES;
SHOW TABLES;
START ALL PIPELINES;
```