from flask import Flask, render_template, request, redirect, url_for, send_file ,flash
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Load the CSV file
    mainFile = pd.read_csv("main.csv")

    # Filter out rows where 'Event Date', 'Event Name', 'Number', or 'Name' is "---"
    mainFile = mainFile[~mainFile[['Event Date', 'Event Name', 'Number', 'Name']].isin(['---']).any(axis=1)]

    if request.method == 'POST':
        # Update the DataFrame with new remarks and current timestamp from the form
        for i in range(len(mainFile)):
            remark_key = f'remarks_{i + 1}'
            if remark_key in request.form:
                new_remark = request.form[remark_key]
                
                # Check if the new remark is different from the existing one
                if new_remark and new_remark != mainFile.at[i, 'Remarks']:
                    # Save the previous remark and last updated time
                    mainFile.at[i, 'Previous Remark'] = mainFile.at[i, 'Remarks']
                    mainFile.at[i, 'Previous Updated'] = mainFile.at[i, 'Last Updated']
                    
                    # Update the current remark and last updated time
                    mainFile.at[i, 'Remarks'] = new_remark
                    mainFile.at[i, 'Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save the updated DataFrame back to the CSV
        mainFile.to_csv("main.csv", index=False)

        # Redirect to avoid form resubmission issues
        return redirect(url_for('index'))

    # Fill NaN values with empty strings for rendering in the template
    mainFile.fillna('', inplace=True)
    data = mainFile.to_dict(orient='records')
    return render_template('index.html', userRow=data)

@app.route('/download_csv')
def download_csv():
    return send_file("main.csv", as_attachment=True, download_name="main.csv")


@app.route('/download_pdf')
def download_pdf():
    data = pd.read_csv("main.csv")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add the header row to the PDF
    headers = list(data.columns)
    header_line = " | ".join(headers)
    pdf.cell(200, 10, txt=header_line, ln=True, align='L')

    # Add a line separator
    pdf.cell(200, 10, txt="-" * len(header_line), ln=True, align='L')

    # Add each data row to the PDF
    for _, row in data.iterrows():
        line = " | ".join(str(x) for x in row)
        pdf.cell(200, 10, txt=line, ln=True, align='L')

    # Output the PDF and send as download
    pdf_file_path = "main.pdf"
    pdf.output(pdf_file_path)
    
    return send_file(pdf_file_path, as_attachment=True)

app.secret_key = "supersecretkey"  # Needed for flash messages if used

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if file and file.filename.endswith('.csv'):
        # Read the uploaded CSV into a DataFrame
        uploaded_data = pd.read_csv(file)

        # Load the main CSV file to append data
        main_csv_path = 'main.csv'
        main_data = pd.read_csv(main_csv_path)

        # Ensure new columns are present in the uploaded data
        new_columns = ['Remarks', 'Last Updated', 'Previous Remark', 'Previous Updated']
        for col in new_columns:
            if col not in uploaded_data.columns:
                uploaded_data[col] = ''  # Add the column with empty values if not present

        # Check for columns mismatch, including new columns
        if not all(col in uploaded_data.columns for col in main_data.columns):
            flash('Uploaded CSV columns do not match main CSV columns.')
            return redirect(url_for('index'))

        # Append uploaded data to the main DataFrame
        main_data = pd.concat([main_data, uploaded_data], ignore_index=True)

        # Optionally, drop duplicate rows
        main_data.drop_duplicates(inplace=True)

        # Save the updated main DataFrame back to the CSV file
        main_data.to_csv(main_csv_path, index=False)
        flash('File successfully uploaded and merged!')
    else:
        flash('Invalid file format. Please upload a CSV file.')

    return redirect(url_for('index'))




if __name__ == '__main__':
    app.run(debug=True)
