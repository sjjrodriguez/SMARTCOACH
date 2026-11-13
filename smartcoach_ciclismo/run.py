import os

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Debug mode shows an interactive debugger to anyone who can reach the server,
    # so it is opt-in: set FLASK_DEBUG=1 in your .env while developing.
    app.run(debug=os.getenv('FLASK_DEBUG') == '1', port=5000)
