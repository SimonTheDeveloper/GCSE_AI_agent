# Backend notes: Homework endpoint

New endpoint: `POST /api/v1/homework/submit`

- Form fields: `uid` (string), `question` (string)
- Files: `files` (one or many)
- Returns JSON: `{ extractedText: string[], combinedText: string, aiHelp?: string, files: string[], warnings: string[] }`

Optional integrations:
- OCR: install system Tesseract OCR and ensure `pytesseract` + `Pillow` are installed.
  - macOS: `brew install tesseract`
- AI help: set environment variable `OPENAI_API_KEY` and optionally `OPENAI_MODEL` (defaults to gpt-3.5-turbo).

Dev tips:
- CORS already allows localhost. Update `REACT_APP_API_URL` for the frontend if needed.
- This endpoint does not persist uploads yet; it reads in-memory and extracts text from images. Extend as needed (e.g., S3 upload).
