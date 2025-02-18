from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    print("Current working directory:", os.getcwd())
    print("App template folder:", app.template_folder)
    print("App static folder:", app.static_folder)
    app.run(debug=True)