AWS Console deployment — artifacts and exact steps

Overview
- This repo contains a React frontend (`frontend/` or `frontend1/`) and a Flask backend (`backend/`).
- We'll upload a backend ZIP to Elastic Beanstalk and static frontend build to S3, then serve via CloudFront.

Artifacts created for you
- `backend/Procfile` — tells EB to run Gunicorn.
- `backend/make_backend_zip.ps1` — PowerShell helper to create `backend-app.zip`.

Before you start (local tasks)
1. Build frontend
   - Open PowerShell in `frontend/`:
     ```powershell
     npm install
     npm run build
     ```
   - This creates `frontend/build`.

2. Prepare backend
   - Ensure `backend/requirements.txt` includes `gunicorn` and all runtime libs.
   - Remove any plaintext secrets (e.g., `credentials.json`) from the repo; store them in Secrets Manager instead.
   - Confirm `backend/Procfile` exists (created for you).

3. Create backend ZIP (PowerShell) — from `backend/` folder
   ```powershell
   cd c:\Users\kushw\Downloads\CodingProjects\ai_smith_schedular\backend
   .\make_backend_zip.ps1
   # This will create backend-app.zip in the backend folder
   ```

Elastic Beanstalk (Console) — backend upload
1. Console → Elastic Beanstalk → Create Application → "ai-smith-backend".
2. Create environment → "Web server environment" → Platform: Python (select matching Python 3.x).
3. When prompted for code, choose "Upload" and select `backend-app.zip` created above.
4. After environment is created, go to Configuration → Software → Edit → set Environment properties:
   - `DB_HOST` = RDS endpoint (or leave and use Secrets Manager)
   - `DB_USER`
   - `DB_PASSWORD`
   - `DB_NAME`
   - `GEMINI_API_KEY` (if used)
   - `FLASK_DEBUG` = `False`
   - `FLASK_PORT` = `5000`

Notes on Secrets
- Recommended: Store DB credentials and 3rd-party keys in AWS Secrets Manager.
- If you use Secrets Manager, either:
  - Add code in your app to read secrets via `boto3`, or
  - Add the secret values to EB environment variables by copy/paste (less secure).
- Make sure the EB instance profile role can access Secrets Manager (add a policy).

S3 + CloudFront (Console) — frontend
1. Console → S3 → Create bucket (unique name) in your region.
2. Upload the contents of `frontend/build` to the bucket (Upload → Add folder).
3. Console → CloudFront → Create distribution → Origin = S3 bucket.
   - Default root object = `index.html`.
   - Use ACM certificate (request cert in `us-east-1`) and add the domain.
4. (Optional) Route 53: create an Alias A record pointing to CloudFront.

RDS (Console)
1. Console → RDS → Create database → Engine: MySQL.
2. Choose instance class, storage, backups, and network (place in private subnets).
3. Create or note the master user and password. Save these to Secrets Manager.
4. When DB is available, note endpoint for `DB_HOST`.

Networking / Security groups
- Ensure EB env security group can reach the RDS security group on port 3306.
- RDS SG inbound should only allow EB SG (not 0.0.0.0/0).

Testing & verification
- Backend health: `https://<eb-environment>.elasticbeanstalk.com/api/health`
- Frontend/CORS: ensure frontend calls backend API URL (set in frontend's config or build-time env variables).
- Test check-in flow to verify `student_feedback` is stored in `Attendance.student_feedback`.

If you'd like I can:
- Generate a sample `/.ebextensions` config (for installing OS packages or creating directories).
- Add a small `boto3` helper snippet to read secrets from Secrets Manager inside `backend/app.py`.

Next step options
- I can prepare a small `secrets_helper.py` and show how to integrate Secrets Manager (recommended).
- Or walk you step-by-step through the EB Console upload screen.

