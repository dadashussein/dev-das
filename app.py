from flask import Flask, render_template_string

app = Flask(__name__)

# Define the HTML template with inline CSS for the pink background
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello</title>
    <style>
        body {
            background-color: black;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            font-family: Arial, sans-serif;
        }
        .message {
            text-align: center;
            font-size: 40px;
            color: #ffd700;
        }
    </style>
</head>
<body>
    <div class="message">
        Hello! This is my simple app for the RS School.<br>
    </div>
</body>
</html>
'''

@app.route('/')
def hello_world():
    return render_template_string(html_template)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
