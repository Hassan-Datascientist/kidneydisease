from flask import Flask, request, render_template, redirect, url_for, flash
from google.cloud import bigquery
from google.oauth2 import service_account
import os

app = Flask(__name__)



PRODUCTION = True
key_path = None 
credentials = None
if PRODUCTION: 
  key_path = '/etc/secrets/kidneydisease.json'
else:
  key_path = 'kidneydisease.json'


credentials = service_account.Credentials.from_service_account_file(key_path)

app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key
# Service account key file path on Render (secret file)
client = bigquery.Client(credentials=credentials, project=credentials.project_id)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        age = int(request.form['age'])
        bp = float(request.form['bp'])
        bgr = float(request.form['bgr'])
        bu = float(request.form['bu'])
        sc = float(request.form['sc'])
    except ValueError:
        flash('Invalid input: Please enter valid numeric values.')
        return redirect(url_for('home'))

    if not (0 <= age <= 100):
        flash('Age must be between 0 and 100.')
        return redirect(url_for('home'))

    for val, name in [(bp, 'Blood Pressure'), (bgr, 'Blood Glucose'), (bu, 'Blood Urea'), (sc, 'Serum Creatinine')]:
        if val < 0:
            flash(f'{name} must be a non-negative number.')
            return redirect(url_for('home'))

    # Example query to get predicted cluster for input data
    query = f"""
    SELECT
      CENTROID_ID AS predicted_cluster
    FROM
      ML.PREDICT(MODEL `kidneydisease-464009.kidneydataset.kidney_kmeans_model`,
      (SELECT {age} AS age, {bp} AS bp, {bgr} AS bgr, {bu} AS bu, {sc} AS sc))
    """

    try:
        query_job = client.query(query)
        results = query_job.result()
        predicted_cluster = None
        for row in results:
            predicted_cluster = row.predicted_cluster
            break
    except Exception as e:
        flash(f'Error during prediction: {str(e)}')
        return redirect(url_for('home'))

    # For demo: dummy cluster counts to display chart (replace with real data if available)
    cluster_counts = {1: 10, 2: 15, 3: 5, 4: 7, 5: 3}

    return render_template('result.html', cluster=predicted_cluster, cluster_counts=cluster_counts)

if __name__ == '__main__':
    app.run(debug=True)
