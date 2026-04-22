# Frontend

React + TypeScript frontend for the GCSE AI Tutor, built with Vite and Tailwind CSS.

## Running locally

```sh
npm install
npm run dev
```

The dev server starts on `http://localhost:5173`. Set `REACT_APP_API_URL` (or the Vite equivalent `VITE_API_URL`) to point at the backend if it's not on `http://localhost:8000`.

## Building for production

```sh
npm run build
```

The output goes to `frontend/dist/` and is deployed to S3 via CDK.

## Structure

```
src/
├─ App.tsx                      # Root component and routing
├─ components/
│  ├─ Homepage.tsx
│  ├─ Login.tsx / SignUp.tsx
│  ├─ Navigation.tsx
│  ├─ MathProblem.tsx
│  ├─ HomeworkSubmission.tsx     # Logic container (state + API calls)
│  ├─ ExplanationPanel.tsx
│  ├─ ProblemSelector.tsx
│  ├─ views/                     # Pure presentational components
│  │  ├─ LoginView.tsx
│  │  ├─ SignUpView.tsx
│  │  ├─ MathProblemView.tsx
│  │  └─ HomeworkSubmissionView.tsx
│  └─ ui/                        # shadcn/ui primitives
└─ __tests__/
```

See [src/components/views/README.md](src/components/views/README.md) for usage examples of the view components.
