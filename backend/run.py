from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("  Jawahar Enterprises - Store Management")
    print("  Running at: http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, host='127.0.0.1', port=5000)
