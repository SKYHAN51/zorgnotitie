# ZorgNotitie Frontend

Next.js-based frontend for ZorgNotitie, a healthcare voice note application.

## Prerequisites

- Node.js 18+ and npm 9+
- Backend API running at `http://localhost:8000` (or configured via `NEXT_PUBLIC_API_URL`)

## Getting Started

1. Copy `.env.local.example` to `.env.local` and adjust `NEXT_PUBLIC_API_URL` if needed:
   ```bash
   cp .env.local.example .env.local
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open `http://localhost:3000` in your browser

## Building for Production

```bash
npm run build
npm start
```

## Architecture

- **Framework:** Next.js 15.5.25 with React 18.3.1
- **Styling:** Tailwind CSS 3.4.17
- **Language:** TypeScript 5.9.2
- **API Client:** `lib/api.ts` (fetches from ZorgNotitie backend)

## Known issues

- `postcss` has an unresolved path-traversal advisory (GHSA-6g55-p6wh-862q / GHSA-r28c-9q8g-f849) that requires upgrading to `next@16` (major version) to fully resolve. Deferred: exposure is build-time only (Tailwind/CSS pipeline processing this app's own source), and the app has no feature that ingests or renders attacker-controlled CSS, so real-world exploitability here is low. Revisit when doing a deliberate Next 16 upgrade.
