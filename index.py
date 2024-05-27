from flask import Flask, request, render_template, send_file
import json
import tempfile

app = Flask(__name__)

def process_files(followers_file, following_file, whitelist_file=None):
    # Load followers data
    with open(followers_file, 'r') as f:
        followers_data = json.load(f)

    # Load following data
    with open(following_file, 'r') as f:
        following_data = json.load(f)

    # Load whitelist data if provided
    whitelist = set()
    if whitelist_file:
        with open(whitelist_file, 'r') as f:
            whitelist_data = json.load(f)
        whitelist = set(whitelist_data.get('whitelist', []))

    # Extract values from followers
    followers_values = set()
    for relationship in followers_data:
        if isinstance(relationship, dict):  # Ensure the item is a dictionary
            for string_data in relationship.get('string_list_data', []):
                if isinstance(string_data, dict):  # Ensure the item is a dictionary
                    followers_values.add(string_data['value'])

    print(f"Extracted {len(followers_values)} followers values.")

    # Find values in following but not in followers, and not in the whitelist
    unique_following = []
    for relationship in following_data.get('relationships_following', []):
        if isinstance(relationship, dict):  # Ensure the item is a dictionary
            for string_data in relationship.get('string_list_data', []):
                if isinstance(string_data, dict):  # Ensure the item is a dictionary
                    value = string_data['value']
                    if value not in followers_values and value not in whitelist:
                        unique_following.append(string_data)

    print(f"Found {len(unique_following)} unique following values.")

    # Generate HTML
    html_content = ""
    for item in unique_following:
        html_content += f'<a href="{item["href"]}">{item["value"]}</a><br>\n'

    # Write to HTML file
    html_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'unique_following.html')
    with open(html_file_path, 'w') as f:
        f.write(html_content)

    return html_file_path

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # Check if the post request has the files
        if 'followers_file' not in request.files or 'following_file' not in request.files:
            return "Missing file(s)", 400

        followers_file = request.files['followers_file']
        following_file = request.files['following_file']
        whitelist_file = request.files.get('whitelist_file')  # Optional

        if followers_file.filename == '' or following_file.filename == '':
            return "No selected file(s)", 400

        # Store files in temporary files
        with tempfile.NamedTemporaryFile(delete=False) as temp_followers_file, \
             tempfile.NamedTemporaryFile(delete=False) as temp_following_file, \
             tempfile.NamedTemporaryFile(delete=False) as temp_whitelist_file:

            followers_file.save(temp_followers_file.name)
            following_file.save(temp_following_file.name)

            if whitelist_file and whitelist_file.filename != '':
                whitelist_file.save(temp_whitelist_file.name)

            # Process files and generate the HTML
            html_file_path = process_files(temp_followers_file.name, temp_following_file.name, temp_whitelist_file.name)

        return send_file(html_file_path, as_attachment=True)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
