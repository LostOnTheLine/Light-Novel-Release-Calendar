name: Diagnose Metadata and Clear Calendar

on:
  workflow_dispatch:  # Manual trigger only

jobs:
  diagnose:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.9"
          
      - name: Install dependencies
        run: pip install requests beautifulsoup4 google-auth-oauthlib google-auth-httplib2 google-api-python-client python-dateutil
        
      - name: Run metadata diagnosis and clear calendar
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
          CALENDAR_ID: ${{ secrets.CALENDAR_ID }}
        run: python calendar/diagnose_metadata.py
        
      - name: Upload diagnosis results
        uses: actions/upload-artifact@v3.1.3  # Explicitly specify latest v3 release
        with:
          name: metadata-diagnosis
          path: metadata_diagnosis.json