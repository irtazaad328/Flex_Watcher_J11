"""Pre-caches ChromeDriver — called once during install."""
try:
    from webdriver_manager.chrome import ChromeDriverManager
    path = ChromeDriverManager().install()
    print(f"  [OK] ChromeDriver cached: {path}")
except Exception as e:
    print(f"  [WARN] Could not pre-cache ChromeDriver: {e}")
    print("  The watcher will find your Chrome installation at login time.")
