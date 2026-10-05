# Job Matcher Frontend

This is a React + Vite frontend for searching and viewing job listings.

## Features

- Search jobs by keywords and location
- Limit number of jobs returned
- Filter by time range (none, 1 hour, 24 hours)
- View fetched jobs in a card-based layout
- Expand/collapse long job descriptions
- Open original job links in a new tab

## Routes

- `/` → Job search form
- `/GetJobs` → Job results list

## Backend API Requirements

The frontend expects a backend running at `http://127.0.0.1:5000` with:

- `POST /search_jobs` to submit search criteria
- `GET /get_jobs` to fetch the latest job results

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```
2. Start the development server:
   ```bash
   npm run dev
   ```
3. Open the app in your browser (Vite prints the local URL in the terminal).

## Available Scripts

- `npm run dev` — start dev server
- `npm run build` — create production build
- `npm run preview` — preview production build
- `npm run lint` — run ESLint
