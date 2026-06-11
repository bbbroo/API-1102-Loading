# Screenshot Refresh Workflow

`docs/screenshots/` contains the current README screenshots captured from the latest running application. `App Screenshots/` contains older reference and audit screenshots used for UI alignment.

To regenerate the current screenshots:

```powershell
python -m uvicorn app.backend.main:app --reload --host 127.0.0.1 --port 8000

cd frontend
npm install
npm run dev
npm run screenshots
```

The capture script uses Playwright at a 1440 x 1100 viewport, creates a temporary deterministic documentation project through the API, captures the README image set, and deletes that temporary project when it finishes.
