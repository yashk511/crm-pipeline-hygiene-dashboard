# Streamlit dashboard: run locally and deploy

## Run locally
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_all.py          # rebuilds clean/ and runs all tests (20 expected)
streamlit run app.py       # opens http://localhost:8501
```

## Deploy free on Streamlit Community Cloud
1. Push the app files to `main` on GitHub (the repo must be public).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app** > **Deploy a public app from GitHub**.
4. Repository: `yashk511/crm-pipeline-hygiene-dashboard`, Branch: `main`, Main file path: `app.py`.
5. Open **Advanced settings** and choose Python 3.11 or 3.12.
6. Click **Deploy**. The first build takes a few minutes.
7. Optional: in the app's settings, set a custom subdomain, for example `crm-pipeline-intelligence`.

The app reads the committed `clean/` CSVs, so no secrets or database are needed.
If you change the data, run `python run_all.py`, commit `clean/`, and push. The app redeploys itself.

## After it is live
- Add the link to the top of `README.md`: `[Live dashboard](https://<your-app>.streamlit.app)`
- Add the same link next to the GitHub link on your resume.
- Open the link in a private window to confirm it works logged out.
- Free apps go to sleep after inactivity. Open the link yourself shortly before sharing it, so a recruiter doesn't see the wake-up screen.
