from flask import Flask, render_template, request
from google.cloud import bigquery
from google.oauth2 import service_account
import os

app = Flask(__name__)

key_path = "/etc/secrets/kidneydisease.json"
credentials = service_account.Credentials.from_service_account_file(key_path)

# Create BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get user input from the form
        age = request.form['age']
        bp = request.form['bp']
        bgr = request.form['bgr']
        bu = request.form['bu']
        sc = request.form['sc']

        # Prepare the query with explicit type casting
        query = f"""
        SELECT
          CENTROID_ID AS predicted_cluster
        FROM
          ML.PREDICT(
            MODEL `kidneydisease-464009.kidneydataset.kidney_kmeans_model`,
            (
              SELECT
                CAST({age} AS INT64) AS age,
                CAST({bp} AS INT64) AS bp,
                CAST({bgr} AS INT64) AS bgr,
                CAST({bu} AS INT64) AS bu,
                CAST({sc} AS FLOAT64) AS sc
            )
          )
        """

        # Execute the query
        query_job = client.query(query)
        result = query_job.result()

        # Get prediction result
        for row in result:
            predicted_cluster = row.predicted_cluster
            break

        return render_template('result.html', cluster=predicted_cluster)

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
