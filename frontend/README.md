# BEST Galaxy Assessment - Frontend

A simple React frontend for testing the BEST Executive Function Galaxy Assessment backend.

## Features

- **52-Question Assessment** — All questions organized by subdomain (4 questions per page)
- **Real-time Progress Tracking** — Visual progress bar and completion counter
- **Interactive Results Dashboard** — View scores, archetype, domain profiles, and AI interpretation
- **Responsive Design** — Works on desktop and mobile devices
- **Tailwind CSS Styling** — Modern, clean UI

## Prerequisites

- Node.js 16+ and npm
- Backend API running on `http://localhost:8000`

## Installation

```bash
cd frontend
npm install
```

## Running the Frontend

```bash
# Start the development server
npm start
```

The app will open at `http://localhost:3000`

## Usage

1. **Start the Backend** (in a separate terminal):
   ```bash
   cd ..
   python3 run_server.py
   ```

2. **Start the Frontend**:
   ```bash
   npm start
   ```

3. **Take the Assessment**:
   - Click "Begin Assessment"
   - Answer all 52 questions (4 per page, 13 pages total)
   - Submit to see your results

## Project Structure

```
frontend/
├── public/
│   └── index.html           # HTML template with Tailwind CDN
├── src/
│   ├── components/
│   │   ├── AssessmentForm.js  # 52-question assessment form
│   │   └── Results.js         # Results dashboard with tabs
│   ├── App.js               # Main app component
│   └── index.js             # React entry point
├── package.json
└── README.md
```

## API Integration

The frontend connects to the backend API at `http://localhost:8000`:

- **POST /api/v1/assess** — Submit assessment responses
- **GET /api/v1/questions** — Fetch questions (optional, has fallback)

The `proxy` setting in `package.json` automatically forwards API requests to the backend.

## Response Format

Questions use A/B/C/D format:
- **A = 4** (Best functioning)
- **B = 3**
- **C = 2**
- **D = 1** (Lowest functioning)

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

## Deployment

The built frontend can be deployed to:
- **Netlify** — Drag and drop the `build/` folder
- **Vercel** — Connect your Git repo
- **Supabase Storage** — Upload as static site
- **Any static hosting** — Serve the `build/` folder

Make sure to update the API endpoint in production (remove the proxy and use full URL).

## Troubleshooting

**CORS errors**: Make sure the backend has CORS enabled (already configured in `api.py`)

**Questions not loading**: The frontend has fallback questions if the `/api/v1/questions` endpoint doesn't exist

**Submission fails**: Check that the backend is running and accessible at `http://localhost:8000`
